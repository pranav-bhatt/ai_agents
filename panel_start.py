from os import environ, path, makedirs
from ast import literal_eval
from shutil import rmtree
from dotenv import load_dotenv, find_dotenv, set_key, get_key
from json import loads, dump
import time
from openapi_spec_validator import validate
from requests import head, exceptions
from aiagents.crew import StartCrewInitialization, StartCrewInteraction, create_session_without_start_button
from aiagents.panel_utils import CustomPanelCallbackHandler, CustomPanelSidebarHandler
from aiagents.panel_utils.panel_stylesheets import (
    alert_stylesheet,
    button_stylesheet,
    radio_button_stylesheet,
    input_stylesheet,
    card_stylesheet,
    sidebar_styles,
    input_button_styles,
    azure_input_stylesheet,
    nl2api_stylesheet,
    markdown_stylesheet,
    chat_stylesheet
)

# Set the environment variable RUN_PANEL to "True" if it's not already set
# This ensures custom callbacks are only set when running crewai via panel
environ.setdefault("RUN_PANEL", "True")

from aiagents.custom_threading import threads
from bokeh.server.contexts import BokehSessionContext

from aiagents.config import configuration
import panel as pn

# Initialize Panel with Material design extension
pn.extension(design="material")

# Environment variables to be stored in the .env file
env_vars = {
    "LLM_TEMPERATURE": "0.1",
    "OPENAI_API_VERSION": "2024-02-01",
    "OPENAI_EMBEDDING_MODEL": "text-embedding-ada-002",
}

# Create the .env file if it doesn't exist and populate it with predefined environment variables
if not path.exists(".env"):
    with open(".env", "w") as env_file:
        for key, value in env_vars.items():
            set_key(find_dotenv(), key, value)

    print(".env file created successfully.")


# Callback to handle user input from the chat interface
def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    # Set the user input to the configuration and hide the spinner
    configuration.user_input = contents
    configuration.spinner.value = False
    configuration.spinner.visible = False


# Initialize a loading spinner that will be displayed when a process is running
configuration.spinner = pn.indicators.LoadingSpinner(
    value=False, visible=False, height=30, width=30,
    styles={"margin-top":"-2rem"}
)

configuration.initialization_spinner = pn.indicators.LoadingSpinner(
    value=False, visible=False, height=30, width=30, color="secondary",
    styles={"margin-top":"-2rem"}
)

# Define the chat interface with a custom callback function
configuration.chat_interface = pn.chat.ChatInterface(
    callback=callback, show_rerun=False, show_undo=False, show_clear=False, show_button_name=False,
    widgets=[pn.chat.ChatAreaInput(
        placeholder="Send your Message", 
        disabled=True, 
        stylesheets=[card_stylesheet], 
        resizable=False
    )],
    stylesheets=[card_stylesheet],
    avatar=pn.pane.Image(f"{configuration.diagram_path}/user.svg", styles={"margin-top": "1rem", "padding": "1.5rem"}),
    user="Me",
)
configuration.chat_interface.message_params = {"reaction_icons": pn.chat.ChatReactionIcons(options={})}



# Verify if the provided API endpoint is reachable
def verify_api_endpoint(url, timeout):
    try:
        response = head(url, timeout=timeout, verify=False)
        return True, response
    except exceptions.RequestException as e:
        return False, str(e)


#Check if API endpoint is reachable
def validate_api_endpoint_input(*events):
    if url_input.value:
        is_valid, response = verify_api_endpoint(url_input.value, timeout=10)
        if is_valid:
            endpoint_alert.visible = False # Hide the "invalid API" alert if valid
            check_input_value(*events)
        else:
            print("API Endpoint Verification Error:", response)
            configuration.upload_button.disabled = True
            endpoint_alert.visible = True


# Validate the uploaded Swagger file
def validate_swagger_file_input(*events):
    if file_input.value:
        try:
            validate(loads(file_input.value.decode()))
            swagger_alert.visible = False # Hide the "invalid Swagger" alert if valid
            check_input_value(*events)
        except Exception as e:
            print("API Specification Verification Error:", e)
            configuration.upload_button.disabled=True # Disable the Upload button
            swagger_alert.visible = True # Show the "invalid Swagger file" alert if invalid


# Check if input values are valid and enable the submit button if all checks pass
def check_input_value(*events):
    # Toggle visibility of Azure-specific fields based on the selected provider
    azure_details.visible = openai_provider_input.value == "AZURE_OPENAI"

    # Check if all the required fields are passed
    if ((
            openai_provider_input.value == "AZURE_OPENAI" and azure_deployment_input.value
            and azure_embedding_input.value and azure_endpoint_input.value
            and key_input.value and ml_api_input.value
            and file_input.value and url_input.value
        ) or(
            openai_provider_input.value == "OPENAI" and key_input.value
            and ml_api_input.value and url_input.value and file_input.value
    )) and not swagger_alert.visible and not endpoint_alert.visible:
        configuration.empty_inputs = False
        configuration.upload_button.disabled = False if not configuration.processing_file else True
    else:
        # Keep upload button disabled if inputs are incomplete
        configuration.upload_button.disabled = True
        configuration.empty_inputs = True


# Define sidebar widgets


# Label and input for selecting the OpenAI provider.
openai_provider_label = pn.widgets.StaticText(
    value="OpenAI Provider", styles={"padding": "8px 10px", "font-size": "13.5px", "font-weight": "500"}, width=125
)
openai_provider_input = pn.widgets.RadioButtonGroup(
    name="OpenAI Provider",
    options=["OPENAI", "AZURE_OPENAI"],
    styles=input_button_styles,
    stylesheets=[radio_button_stylesheet],
    button_style="outline",
    width=180,
)


# Inputs for Azure OpenAI related fields.
azure_deployment_input = pn.widgets.TextInput(
    name="Azure OpenAI Deployment", 
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet, azure_input_stylesheet],
)
azure_endpoint_input = pn.widgets.TextInput(
    name="Azure OpenAI Endpoint", 
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet, azure_input_stylesheet],
)
azure_embedding_input = pn.widgets.TextInput(
    name="Azure OpenAI Embedding",
    styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet, azure_input_stylesheet],
)

# Card to contain Azure-specific inputs.
# Azure details container
azure_details = pn.Column(
    azure_deployment_input,
    azure_endpoint_input,
    azure_embedding_input,
    visible=False
)

# OpenAI key input
key_input = pn.widgets.PasswordInput(
    name="OpenAI Key",
    placeholder="",
    width=360,
    styles={"font-size": "50px"},
    stylesheets=[input_stylesheet]
)

# Main configuration card
configuration_details = pn.Card(
    key_input,  # Start with just the key input
    width=380,
    title="Model Configuration Details",
    collapsed=True,
    styles={"background": "#eaf3f3"},
    header_background="#cee3e3",
    active_header_background="#cee3e3",
    header="<html><h4 style='margin:0.25rem; font-size:0.82rem'>Model Configuration Details</h4></html>"
)

def update_card_contents():
    """Updates the card contents based on the provider selection"""
    is_azure = openai_provider_input.value == "AZURE_OPENAI"
    
    if is_azure and not configuration_details.collapsed:
        # Show both Azure details and key input for Azure when expanded
        configuration_details.objects = [azure_details, key_input]
        azure_details.visible = True
        azure_name = "Azure " if "Azure " not in key_input.name else ""
        key_input.name = azure_name + key_input.name
    else:
        # Show only key input for OpenAI or when collapsed
        configuration_details.objects = [key_input]
        azure_details.visible = False
        if "Azure " in key_input.name:
            key_input.name = key_input.name.split("Azure ")[1]

def update_visibility(event=None):
    """Updates visibility of components based on the provider input value."""
    update_card_contents()

def on_expand(event):
    """Handle card expansion/collapse events"""
    update_card_contents()

# Set up event watchers
openai_provider_input.param.watch(update_visibility, "value")
configuration_details.param.watch(on_expand, "collapsed")


url_input = pn.widgets.TextInput(
    name="API Endpoint", placeholder="", styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet]
)
ml_api_input = pn.widgets.PasswordInput(
    name="API Bearer Token", placeholder="", styles={"font-size": "50px"}, width=360, stylesheets=[input_stylesheet]
)
file_input = pn.widgets.FileInput(name="Upload", accept=".json",multiple=False, width=360, stylesheets=[input_stylesheet])

# Alert for invalid Swagger file
swagger_alert = pn.pane.Alert(
    "!!The API Specification file uploaded is invalid. Please upload a valid file",
    alert_type="danger",
    width=360,
    stylesheets=[alert_stylesheet],
    css_classes=["alert"],
)
swagger_alert.visible = False

# Alert for invalid API endpoint
endpoint_alert = pn.pane.Alert(
    "!!The API Endpoint provided is Invalid. Please retry with a valid endpoint or check your network configurations.",
    alert_type="danger",
    width=360,
    stylesheets=[alert_stylesheet],
    css_classes=["alert"],
)
endpoint_alert.visible = False

nl2api_configuration = pn.Card(
    file_input,
    swagger_alert,
    url_input,
    endpoint_alert,
    ml_api_input,
    collapsible=False,
    title="Natural Language (NL) to API",
    width=380,
    styles={"background": "#eaf3f3", "overflow": "auto"},  # Enable scrolling if necessary
    stylesheets=[nl2api_stylesheet],
    header_background="#cee3e3",
    active_header_background="#cee3e3",
    header="<html><h4 style='margin:0.25rem; font-size:0.82rem'>Natural Language (NL) to API</h4></html>",
)

# Watch for changes in input values and trigger validations
openai_provider_input.param.watch(check_input_value, "value")
azure_deployment_input.param.watch(check_input_value, "value")
azure_endpoint_input.param.watch(check_input_value, "value")
azure_embedding_input.param.watch(check_input_value, "value")
key_input.param.watch(check_input_value, "value")
url_input.param.watch(validate_api_endpoint_input, "value")
url_input.param.watch(check_input_value, "value")
ml_api_input.param.watch(check_input_value, "value")
file_input.param.watch(validate_swagger_file_input, "value")
file_input.param.watch(check_input_value, "value")


# Handle input values and update the environment variables accordingly
def handle_inputs(event):
    configuration_details.collapsed=True
    configuration.metadata_summarization_status.value = f""
    env_file = find_dotenv()
    load_dotenv(env_file)

    # Update API endpoint in the .env file
    api_endpoint = (
        literal_eval(get_key(env_file, "API_ENDPOINT"))
        if get_key(env_file, "API_ENDPOINT")
        else {}
    )
    api_endpoint[file_input.filename] = url_input.value
    set_key(env_file, "API_ENDPOINT", api_endpoint, quote_mode="never")

    # Update API bearer token in the .env file
    api_bearer_token = (
        literal_eval(get_key(env_file, "API_BEARER_TOKEN"))
        if get_key(env_file, "API_BEARER_TOKEN")
        else {}
    )
    api_bearer_token[file_input.filename] = ml_api_input.value
    set_key(env_file, "API_BEARER_TOKEN", api_bearer_token, quote_mode="never")

    # Update OpenAI key if it's not already set or if a new key is provided
    if not get_key(env_file, "OPENAI_API_KEY") or key_input.value:
        set_key(env_file, "OPENAI_API_KEY", key_input.value)

    # Update Azure-specific environment variables if Azure is selected as the provider
    # Handle provider-specific details.
    configuration.openai_provider = openai_provider_input.value
    if configuration.openai_provider == "AZURE_OPENAI":
        if not get_key(env_file, "AZURE_OPENAI_DEPLOYMENT") or azure_deployment_input.value:
            set_key(env_file, "AZURE_OPENAI_DEPLOYMENT", azure_deployment_input.value)
        if not get_key(env_file, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or azure_embedding_input.value:
            set_key(env_file, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", azure_embedding_input.value)
        if not get_key(env_file, "AZURE_OPENAI_ENDPOINT") or azure_endpoint_input.value:
            set_key(env_file, "AZURE_OPENAI_ENDPOINT", azure_endpoint_input.value)



    # If the directory for Swagger files does not exist, create it
    if not path.exists(configuration.swagger_files_directory):
        makedirs(configuration.swagger_files_directory)
    # Save the uploaded Swagger file in the designated directory
    file_path = path.join(
        configuration.swagger_files_directory, file_input.filename
    )
    file_content = loads(file_input.value.decode())
    with open(file_path, "w") as file:
        dump(file_content, file, indent=4)

    configuration.new_file_name = file_input.filename

    configuration.update_configuration() # Update the configuration with the new values
    # Reset input values, disable the 'Upload' button, and enable the 'Start Crew' button after upload
    ml_api_input.value = url_input.value = file_input.value = ""
    configuration.upload_button.disabled = True
    configuration.empty_inputs = True
    configuration.initialization_crew_thread = threads.thread_with_trace(
        target=StartCrewInitialization, args=(configuration,)
    )
    configuration.initialization_crew_thread.daemon = True  # Ensure the thread dies when the main thread (the one that created it) dies
    configuration.initialization_crew_thread.start()
 

# Upload button widget configuration and event handling
configuration.upload_button = pn.widgets.Button(
    name="Upload",
    button_type="primary",
    disabled=True,
    icon="upload",
    icon_size="1.2em",
    stylesheets=[button_stylesheet],
    description="Upload the API Speicifcation file and the respective endpoints",
)
configuration.upload_button.on_click(handle_inputs)


def reset_for_new_input(event):
    # Set the active diagram to the current full diagram path for visualization
    configuration.active_diagram.value = (
        f"{configuration.diagram_path}/{configuration.diagrams['full']}"
    )
    # Attempt to kill the currently running crew thread, if any
    try:
        configuration.crew_thread.kill()
    except:
        pass
    configuration.reload_button.disabled = True
    configuration.chat_interface.clear()
    configuration.spinner.visible = False
    configuration.spinner.value = False
    configuration.chat_interface.send(
        pn.pane.Markdown(
            "The crew has been restarted.", 
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ),
        user="System",
        respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
    )
    create_session_without_start_button()



# Reload the diagram and handle post-reload session after stopping the crew thread
def reload_post_callback(event):
    # Set the active diagram to the current full diagram path for visualization
    configuration.active_diagram.value = (
        f"{configuration.diagram_path}/{configuration.diagrams['full']}"
    )
    # Attempt to kill the currently running crew thread, if any
    try:
        configuration.crew_thread.kill()
    except:
        pass
    # Clear the chat interface and Enable the 'Start Crew' button to start a new session
    configuration.chat_interface.clear()
    # Disable the reload button to prevent redundant reloads and hide the spinner
    configuration.reload_button.disabled = True
    configuration.spinner.visible = False
    configuration.spinner.value = False
    # Send a welcome message to the chat interface after reloading the session
    configuration.chat_interface.send(
        pn.pane.Markdown(
            """The crew has been restarted. Please enter further query below once the Human Input Agent Appears.""",
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ),
        user="System",
        respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
    )


# Reload button widget configuration and event handling
configuration.reload_button = pn.widgets.Button(
    name="Restart Crew",
    disabled=True,
    icon="reload",
    icon_size="1.2em",
    stylesheets=[button_stylesheet],
    description="Restart the Crew",
)
configuration.reload_button.on_click(reset_for_new_input)

# Sidebar configuration for input fields and buttons
configuration.sidebar = pn.Column(
    pn.Card(
        pn.Row(
            pn.Row(openai_provider_label, openai_provider_input),
        ),
        pn.Row(
            configuration_details,
        ),
        pn.Row(
            nl2api_configuration,
        ),
        pn.Row(
            configuration.upload_button,
        ),
        pn.Row(
            pn.pane.Markdown(
                configuration.metadata_summarization_status,
                width=380,
                styles={
                    "font-size": "0.83rem", 
                    "background-color": "#e7f5eb",
                    "color": "#092710",
                    "padding": "0 0.8rem",
                    "border-radius": "8px",
                    "font-weight": "bold",
                    "margin-left": "0.26rem",
                },
                stylesheets=[markdown_stylesheet]
            )
        ),
        pn.Row(
            pn.pane.Image(
                configuration.active_diagram,
                width=380,
            ),
            align=("start", "center"),  # vertical, horizontal
        ),
        pn.Row(configuration.reload_button),
        styles=sidebar_styles, 
        hide_header=True,
        width=405
    ),
    stylesheets=[card_stylesheet],
)

# Custom callback handlers for handling events in the chat interface
configuration.customInteractionCallbacks = [
    CustomPanelCallbackHandler(chat_interface=configuration.chat_interface)
]

configuration.customInitializationCallbacks = [
    CustomPanelSidebarHandler(chat_interface=configuration.chat_interface)
]


# Main function to initialize and run the application
def main():
    env_file = find_dotenv()
    load_dotenv(env_file)

    # Update API endpoint in the .env file
    set_key(env_file, 'fileCount', '0')

    # Instantiate the FastListTemplate with custom header and sidebar
    template = pn.template.FastListTemplate(
        header="""
            <html><a href="/" style='
                font-size: 1.2rem;
                color: #f1e1e1;
                text-decoration: none;
                margin-left: -2rem;
            '>Multi-Agent API Orchestrator using CrewAI</a></html>
        """,
        title=" ",
        sidebar=pn.Column(configuration.sidebar),
        accent="#2F4F4F",
        sidebar_width=400,
        main_layout=None,
    )
    template.theme_toggle = False # Disable theme toggle button in the template
    # Combine the chat interface and loading spinner into the main layout
    footer = pn.pane.Markdown(
        "Workflows are generated by AI and may be inaccurate.",
        styles = {
            "margin": "0 auto -0.8rem",
            "padding": "0",
            "font-size": "0.79rem",
            "font-family": "Verdana",
            "font-weight": "500",
            "color": "#454545",
        }
    )
    container = pn.Column(
        configuration.chat_interface,
        configuration.spinner,
        configuration.initialization_spinner,
        footer,
        styles = {
            "overflow": "hidden", 
            "height": "calc(100vh - 85px)",
        }
    )
    template.main.append(container)

    # Send an initial message to the chat interface providing instructions to the user
    configuration.chat_interface.send(
        pn.pane.Markdown(
            """
    ### Welcome to the Multi-Agent API Orchestrator

    Get started by configuring your model and API integrations. We support both **Azure OpenAI** and **OpenAI** services. Please follow the steps below:

    #### Configuration Steps
    - **Azure OpenAI**: Provide the deployment name, endpoint URL, embedding deployment name, and API key.
    - **OpenAI**: Simply provide your OpenAI API key to enable model integration.

    #### Natural Language (NL) to API Integration
    - **Upload API Specification**: Upload a valid API Specification file.
    - **API Endpoint**: Enter the API endpoint for the integration.
    - **API Bearer Token**: Provide the bearer token to enable secure API authentication.

    Once all details are entered, click **Upload** to validate your inputs and initiate the orchestration process. **Streamline API orchestration** with CrewAI—handle complexities effortlessly and focus on results.""",
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ),
        user="System",
        respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"}),
    )

    configuration.chat_interface.send(
        pn.pane.Markdown(
            """
        #### Accessing and Using the CML Workbench API Specification:
        - Sign in to Cloudera AI.
        - Access the API specification for CML Workbench at `https://<domain name of Cloudera AI instance>/api/v2/swagger.json`
        - Navigate to **User Settings** > **API Keys** and select **Create API Key**.
        - Copy the **API key** (bearer token) and the **domain endpoint** (API endpoint) from the browser’s address bar (e.g., `https://ml-xxxx123456.com`).

        Example Tasks that the Agent Can Perform With the given API Specification:
        - Create a project
        - List all projects
        - List all runtimes
        """,
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ),
        user="System",
        respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
    )

    print("Running panel on port ", configuration.app_port)

    # Serve the application using Panel with the specified configuration
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



# Call the main function to start the application
if __name__ == "__main__":
    main()
