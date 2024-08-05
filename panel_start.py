from os import environ, path, makedirs
from ast import literal_eval
from shutil import rmtree
from dotenv import load_dotenv, find_dotenv, set_key, get_key
from json import loads, dump
from openapi_spec_validator import validate

from aiagents.crew import StartCrew
from aiagents.panel_utils import CustomPanelCallbackHandler

# hacky way of setting custom callbacks only in case we are running crewai via panel
environ.setdefault("RUN_PANEL", "True")

from aiagents.custom_threading import threads
from bokeh.server.contexts import BokehSessionContext

from aiagents.config import configuration
import panel as pn

pn.extension(design="material")

env_vars = {
    "LLM_TEMPERATURE": "0.4",
    "OPENAI_API_VERSION": "2024-02-01",
    "AZURE_OPENAI_DEPLOYMENT": "cml",
    "AZURE_OPENAI_EMBEDDING_MODEL": "text-embedding-ada-002",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "cml-embedding",
    "AZURE_OPENAI_ENDPOINT": "https://cml-gpt-1.openai.azure.com",
}

# Create the .env file if it doesn't exist and write the environment variables
if not path.exists(".env"):
    with open(".env", "w") as env_file:
        for key, value in env_vars.items():
            set_key(find_dotenv(), key, value)

    print(".env file created successfully.")


def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    configuration.user_input = contents
    configuration.spinner.value = False
    configuration.spinner.visible = False


configuration.spinner = pn.indicators.LoadingSpinner(
    value=False, visible=False, height=30, width=30
)
configuration.chat_interface = pn.chat.ChatInterface(
    callback=callback, show_rerun=False, show_undo=False, show_clear=False
)


def session_created(session_context: BokehSessionContext):
    start_crew_button.disabled = True
    configuration.chat_interface.clear()
    configuration.chat_interface.send(
        "Starting the Crew!", user="System", respond=False
    )
    configuration.spinner.value = True
    configuration.spinner.visible = True
    configuration.crew_thread = threads.thread_with_trace(
        target=StartCrew, args=(configuration,)
    )
    configuration.crew_thread.daemon = True  # ensure the thread dies when the main thread (the one that created it) dies
    configuration.crew_thread.start()


# sidebar widgets
stylesheet = """
:host(.alert) {
  padding: 0 10px;
  max-height: 50px;
}
"""


def check_input_value(*events):
    if (
        (key_input.value or get_key(find_dotenv(), "AZURE_OPENAI_API_KEY"))
        and url_input.value
        and ml_api_input.value
        and file_input.value
    ):
        try:
            validate(loads(file_input.value.decode()))
            alert.visible = False
            submit_button.disabled = False
        except Exception as e:
            print("error:", e)
            submit_button.disabled = True
            alert.visible = True
    else:
        submit_button.disabled = True


key_input = pn.widgets.PasswordInput(
    name="OpenAI Key", placeholder="", styles={"font-size": "50px"}, width=380
)
url_input = pn.widgets.TextInput(
    name="API Endpoint", placeholder="", styles={"font-size": "50px"}, width=380
)
ml_api_input = pn.widgets.PasswordInput(
    name="API Bearer Token", placeholder="", styles={"font-size": "50px"}, width=380
)
file_input = pn.widgets.FileInput(accept=".json", multiple=False, width=380)
alert = pn.pane.Alert(
    "!!The Swagger file uploaded is invalid. Please upload a valid file",
    alert_type="danger",
    width=380,
    stylesheets=[stylesheet],
    css_classes=["alert"],
)
alert.visible = False
key_input.param.watch(check_input_value, "value")
url_input.param.watch(check_input_value, "value")
ml_api_input.param.watch(check_input_value, "value")
file_input.param.watch(check_input_value, "value")


def handle_inputs(event):
    env_file = find_dotenv()
    load_dotenv(env_file)
    api_endpoint = (
        literal_eval(get_key(env_file, "API_ENDPOINT"))
        if get_key(env_file, "API_ENDPOINT")
        else {}
    )
    api_endpoint[file_input.filename] = url_input.value
    set_key(env_file, "API_ENDPOINT", api_endpoint, quote_mode="never")
    api_bearer_token = (
        literal_eval(get_key(env_file, "API_BEARER_TOKEN"))
        if get_key(env_file, "API_BEARER_TOKEN")
        else {}
    )
    api_bearer_token[file_input.filename] = ml_api_input.value
    set_key(env_file, "API_BEARER_TOKEN", api_bearer_token, quote_mode="never")
    if not get_key(env_file, "AZURE_OPENAI_API_KEY") or key_input.value:
        set_key(env_file, "AZURE_OPENAI_API_KEY", key_input.value)

    if file_input.value:
        try:
            rmtree(configuration.generated_folder_path)
        except FileNotFoundError:
            pass

        if not path.exists(configuration.swagger_files_directory):
            makedirs(configuration.swagger_files_directory)
        file_path = path.join(
            configuration.swagger_files_directory, file_input.filename
        )
        file_content = loads(file_input.value.decode())
        with open(file_path, "w") as file:
            dump(file_content, file, indent=4)

    configuration.update_configuration()
    key_input.value = ml_api_input.value = url_input.value = file_input.value = ""
    submit_button.disabled = True
    start_crew_button.disabled = False


submit_button = pn.widgets.Button(
    name="Upload",
    button_type="primary",
    disabled=True,
    icon="upload",
    icon_size="1.2em",
    description="Upload the swagger file and the respective endpoints",
)
submit_button.on_click(handle_inputs)

start_crew_button = pn.widgets.Button(
    name="Start Crew",
    button_type="primary",
    disabled=True,
    icon="plane-tilt",
    icon_size="1.2em",
    description="Trigger the crew execution",
)
start_crew_button.on_click(session_created)


def reload_post_callback(event):
    configuration.active_diagram.value = (
        f"{configuration.diagram_path}/{configuration.diagrams['full']}"
    )
    try:
        configuration.crew_thread.kill()
    except:
        pass
    configuration.chat_interface.clear()
    start_crew_button.disabled = False
    configuration.reload_button.disabled = True
    configuration.spinner.visible = False
    configuration.spinner.value = False
    configuration.chat_interface.send(
        """Welcome to CML Agent!! Here, in you can implement different swagger file integrations. 
        Please upload the correct Swagger file, along with your OpenAI keys, API endpoint, and 
        access keys to make necessary API calls. Once all the inputs have been provided, click 
        on the 'Start Crew' button to fire the crew execution, and sit back and relax while the 
        agent performs the requested tasks on your behalf with the least manual intervention!""",
        user="System",
        respond=False,
    )


configuration.reload_button = pn.widgets.Button(
    name="Reload Crew",
    disabled=True,
    icon="reload",
    icon_size="1.2em",
    description="Reload the Crew",
)
configuration.reload_button.on_click(reload_post_callback)

configuration.sidebar = pn.Column(
    pn.Row(
        key_input,
    ),
    pn.Row(
        url_input,
    ),
    pn.Row(
        ml_api_input,
    ),
    pn.Row(
        file_input,
    ),
    pn.Row(
        submit_button,
    ),
    pn.Row(
        alert,
    ),
    pn.Spacer(height=10),
    pn.Row(
        pn.pane.Image(
            configuration.active_diagram,
            sizing_mode="scale_width",
        ),
        align=("start", "center"),  # vertical, horizontal
    ),
    pn.Spacer(height=10),
    pn.Row(start_crew_button, configuration.reload_button),
)

configuration.customCallbacks = [
    CustomPanelCallbackHandler(chat_interface=configuration.chat_interface)
]


def main():
    # Instantiate the template with widgets displayed in the sidebar
    template = pn.template.FastListTemplate(
        title="Multi-Agent API Orchestrator using CrewAI",
        sidebar=configuration.sidebar,
        accent="#2F4F4F",
        sidebar_width=400,
    )
    template.theme_toggle = False
    container = pn.Column(configuration.chat_interface, configuration.spinner)
    template.main.append(container)

    configuration.chat_interface.send(
        """Welcome to CML Agent!! Here, in you can implement different swagger file integrations. 
        Please upload the correct Swagger file, along with your OpenAI keys, API endpoint, and 
        access keys to make necessary API calls. Once all the inputs have been provided, click 
        on the 'Start Crew' button to fire the crew execution, and sit back and relax while the 
        agent performs the requested tasks on your behalf with the least manual intervention!""",
        user="System",
        respond=False,
    )

    print("Running panel on port ", configuration.app_port)

    app = pn.serve(
        {"multi-agents-with-crewai": template},
        address="127.0.0.1",
        port=configuration.app_port,
        title="Multi Agents With Crewai",
        websocket_origin="*",
        show=False,
        start=True,
        autoreload=True,
    )


if __name__ == "__main__":
    main()
