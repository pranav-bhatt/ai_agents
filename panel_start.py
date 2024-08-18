from os import environ, path, makedirs
from ast import literal_eval
from shutil import rmtree
from dotenv import load_dotenv, find_dotenv, set_key, get_key
from json import loads, dump
from openapi_spec_validator import validate
from requests import head, exceptions

from aiagents.crew import StartCrew
from aiagents.panel_utils import CustomPanelCallbackHandler
from aiagents.panel_utils.panel_stylesheets import (
    alert_stylesheet,
    button_stylesheet,
    radio_button_stylesheet,
    input_stylesheet,
    card_stylesheet,
    sidebar_styles,
    input_button_styles,
)

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
    "OPENAI_EMBEDDING_MODEL": "text-embedding-ada-002",
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
    value=False, visible=False, height=30, width=30,
    styles={"margin-top":"-2.8rem"}
)
configuration.chat_interface = pn.chat.ChatInterface(
    callback=callback, show_rerun=False, show_undo=False, show_clear=False,
    stylesheets=[card_stylesheet]
)


def session_created(session_context: BokehSessionContext):
    start_crew_button.disabled = True
    configuration.chat_interface.clear()
    configuration.chat_interface.send(
        pn.pane.Markdown(
            "Starting the Crew!",
            styles=configuration.chat_styles
        ), user="System", respond=False
    )
    configuration.spinner.value = True
    configuration.spinner.visible = True
    configuration.crew_thread = threads.thread_with_trace(
        target=StartCrew, args=(configuration,)
    )
    configuration.crew_thread.daemon = True  # ensure the thread dies when the main thread (the one that created it) dies
    configuration.crew_thread.start()


# sidebar widgets
def verify_api_endpoint(url, timeout):
    try:
        response = head(url, timeout=timeout, verify=False)
        if response.status_code >= 200 and response.status_code < 400:
            return True, response
        else:
            return False, response.status_code
    except exceptions.RequestException as e:
        return False, str(e)

def check_input_value(*events):
    azure_details.visible = openai_provider_input.value == "AZURE_OPENAI"
    if ((
            openai_provider_input.value == "AZURE_OPENAI" and azure_deployment_input.value
            and azure_embedding_input.value and azure_endpoint_input.value
            and key_input.value and ml_api_input.value
            and file_input.value and url_input.value
        ) or(
            openai_provider_input.value == "OPENAI" and key_input.value
            and ml_api_input.value and url_input.value and file_input.value
    )):
        # Check if API endpoint is reachable
        is_valid, response = verify_api_endpoint(url_input.value, timeout=10)
        if is_valid:
            endpoint_alert.visible = False
            # Check if Swagger file is valid
            try:
                validate(loads(file_input.value.decode()))
                swagger_alert.visible = False
                submit_button.disabled = False
            except Exception as e:
                print("Swagger Verification Error:", e)
                submit_button.disabled=True
                swagger_alert.visible = True
        else:
            print("API Endpoint Verification Error:", response)
            submit_button.disabled = True
            endpoint_alert.visible = True
    else:
        submit_button.disabled = True


openai_provider_label = pn.widgets.StaticText(
    value="OpenAI Provider", styles={"padding": "0 10px"}, width=370
)
openai_provider_input = pn.widgets.RadioButtonGroup(
    name="OpenAI Provider",
    options=["AZURE_OPENAI", "OPENAI"],
    styles=input_button_styles,
    stylesheets=[radio_button_stylesheet],
    button_style="outline",
    width=370,
)
azure_deployment_input = pn.widgets.TextInput(
    name="Azure OpenAI Deployment", 
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet],
)
azure_endpoint_input = pn.widgets.TextInput(
    name="Azure OpenAI Endpoint", 
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet],
)
azure_embedding_input = pn.widgets.TextInput(
    name="Azure OpenAI Embedding",
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet],
)
azure_details = pn.Card(azure_deployment_input,
    azure_endpoint_input,
    azure_embedding_input,
    width=380,
    title="Azure OpenAI Details",
    collapsed=True,
    styles={"background": "#f3f8f8"},
    header_background="#cee3e3",
    active_header_background="#cee3e3",
    header="<html><h4 style='margin:0.25rem; font-size:0.82rem'>Azure OpenAI Details</h4></html>",
    visible=True if openai_provider_input.value == "AZURE_OPENAI" else False,
)
key_input = pn.widgets.PasswordInput(
    name="OpenAI Key", placeholder="", styles={"font-size": "50px"}, width=370
)
url_input = pn.widgets.TextInput(
    name="API Endpoint", placeholder="", styles={"font-size": "50px"}, width=370
)
ml_api_input = pn.widgets.PasswordInput(
    name="API Bearer Token", placeholder="", styles={"font-size": "50px"}, width=370
)
file_input = pn.widgets.FileInput(accept=".json", multiple=False, width=370)
swagger_alert = pn.pane.Alert(
    "!!The Swagger file uploaded is invalid. Please upload a valid file",
    alert_type="danger",
    width=370,
    stylesheets=[alert_stylesheet],
    css_classes=["alert"],
)
swagger_alert.visible = False
endpoint_alert = pn.pane.Alert(
    "!!The API Endpoint provided is Invalid. Please retry with a valid endpoint or check your network configurations.",
    alert_type="danger",
    width=370,
    stylesheets=[alert_stylesheet],
    css_classes=["alert"],
)
endpoint_alert.visible = False
openai_provider_input.param.watch(check_input_value, "value")
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
    if not get_key(env_file, "OPENAI_API_KEY") or key_input.value:
        set_key(env_file, "OPENAI_API_KEY", key_input.value)

    configuration.openai_provider = openai_provider_input.value
    if configuration.openai_provider == "AZURE_OPENAI":
        if not get_key(env_file, "AZURE_OPENAI_DEPLOYMENT") or azure_deployment_input.value:
            set_key(env_file, "AZURE_OPENAI_DEPLOYMENT", azure_deployment_input.value)
        if not get_key(env_file, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or azure_embedding_input.value:
            set_key(env_file, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", azure_embedding_input.value)
        if not get_key(env_file, "AZURE_OPENAI_ENDPOINT") or azure_endpoint_input.value:
            set_key(env_file, "AZURE_OPENAI_ENDPOINT", azure_endpoint_input.value)

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
    ml_api_input.value = url_input.value = file_input.value = ""
    submit_button.disabled = True
    start_crew_button.disabled = False


submit_button = pn.widgets.Button(
    name="Upload",
    button_type="primary",
    disabled=True,
    icon="upload",
    icon_size="1.2em",
    stylesheets=[button_stylesheet],
    description="Upload the swagger file and the respective endpoints",
)
submit_button.on_click(handle_inputs)

start_crew_button = pn.widgets.Button(
    name="Start Crew",
    button_type="primary",
    disabled=True,
    icon="plane-tilt",
    icon_size="1.2em",
    stylesheets=[button_stylesheet],
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
        pn.pane.Markdown(
            """Welcome to Multi-Agent API Orchestrator using CrewAI!! Here, in you can implement different 
            swagger file integrations. Please upload the correct Swagger file, along with your OpenAI keys, 
            API endpoint, and access keys to make necessary API calls. Once all the inputs have been 
            provided, click on the 'Start Crew' button to fire the crew execution, and sit back and relax 
            while the agent performs the requested tasks on your behalf with the least manual intervention!""",
            styles=configuration.chat_styles,
        ),
        user="System",
        respond=False,
    )


configuration.reload_button = pn.widgets.Button(
    name="Reload Crew",
    disabled=True,
    icon="reload",
    icon_size="1.2em",
    stylesheets=[button_stylesheet],
    description="Reload the Crew",
)
configuration.reload_button.on_click(reload_post_callback)

configuration.sidebar = pn.Column(
    pn.Card(
        pn.Row(
            pn.Column(openai_provider_label, openai_provider_input),
        ),
        pn.Row(
            azure_details,
        ),
        pn.Row(
            key_input,
        ),
        pn.Row(
            url_input,
        ),
        pn.Row(
            endpoint_alert,
        ),
        pn.Row(
            ml_api_input,
        ),
        pn.Row(
            file_input,
        ),
        pn.Row(
            swagger_alert,
        ),
        pn.Row(
            submit_button,
        ),
        pn.Row(
            pn.pane.Image(
                configuration.active_diagram,
                width=380,
            ),
            align=("start", "center"),  # vertical, horizontal
        ),
        pn.Row(start_crew_button, configuration.reload_button),
        styles=sidebar_styles, 
        hide_header=True,
        width=400
    ),
    stylesheets=[card_stylesheet],
)

configuration.customCallbacks = [
    CustomPanelCallbackHandler(chat_interface=configuration.chat_interface)
]


def main():
    # Instantiate the template with widgets displayed in the sidebar
    template = pn.template.FastListTemplate(
        header="""
            <html><a href="/" style='
                font-size: 1.3rem;
                color: #f1e1e1;
                text-decoration: none;
                margin-left: -2rem;
            '>Multi-Agent API Orchestrator using CrewAI</a></html>
        """,
        title=" ",
        sidebar=pn.Column(configuration.sidebar),
        accent="#2F4F4F",
        sidebar_width=400,
    )
    template.theme_toggle = False
    container = pn.Column(configuration.chat_interface, configuration.spinner)
    template.main.append(container)

    configuration.chat_interface.send(
        pn.pane.Markdown(
            """Welcome to Multi-Agent API Orchestrator using CrewAI!! Here, in you can implement different 
            swagger file integrations. Please upload the correct Swagger file, along with your OpenAI keys, 
            API endpoint, and access keys to make necessary API calls. Once all the inputs have been 
            provided, click on the 'Start Crew' button to fire the crew execution, and sit back and relax 
            while the agent performs the requested tasks on your behalf with the least manual intervention!""",
            styles=configuration.chat_styles
        ),
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
