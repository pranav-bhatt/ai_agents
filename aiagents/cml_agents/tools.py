from ast import literal_eval
from os import makedirs, listdir, environ
from os.path import join, exists
from dotenv import get_key, load_dotenv, find_dotenv, set_key
from textwrap import dedent
from json import dump, loads
from requests import get, post, patch, delete
from time import sleep
import panel as pn

from crewai_tools import BaseTool, FileReadTool, DirectoryReadTool, tool

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

from typing import Dict

from aiagents.config import configuration

from .parse_for_manager import swagger_parser

metadata_summary_fetcher = FileReadTool(file_path=configuration.metadata_summaries_path)

generated_directory_traverser = DirectoryReadTool(
    directory=configuration.generated_folder_path
)

generated_directory_lister = Tool(
    name="generated_directory_lister",
    # use langchain toolkit to list all the files in the generated folder
    func=FileManagementToolkit(
        root_dir=configuration.generated_folder_path,
        selected_tools=["list_directory"],
    )
    .get_tools()[0]
    .run,
    description=dedent(
        f"""
        This tool will list all the files in the '{configuration.generated_folder_path}' directory and no other. It takes 
        'input: {{}}' as the argument. It will return the list of files in the swagger directory separated by newlines.
        The swagger files that need to be read are the ones that end with '.json'.
        """
    ),
)

swagger_directory_lister = Tool(
    name="swagger_directory_lister",
    # use langchain toolkit to list all the files in the generated folder
    func=FileManagementToolkit(
        root_dir=configuration.swagger_files_directory,
        selected_tools=["list_directory"],
    )
    .get_tools()[0]
    .run,
    description=dedent(
        f"""
        This tool will list all the files in the '{configuration.swagger_files_directory}' directory and no other. It takes 
        'input: {{}}' as the argument. It will return the list of files in the swagger directory separated by newlines.
        The swagger files that need to be read are the ones that end with '.json'.
        """
    ),
)


@tool("get_human_input")
def get_human_input(agent_name: str, agent_question: str) -> str:
    """
    This function will get the human input from the user. It has 2 parameter it accepts:
    - agent_name: The name of the agent invoking this tool
    - agent_question: The question that the agent will ask the user.
    """
    print(f"The get human input tool is called with name:{agent_name}\n and \n question{agent_question}\n\n")
    configuration.active_diagram.value = (
        f"{configuration.diagram_path}/{configuration.diagrams["get_human_input"]}"
    )
    configuration.chat_interface.send(
        value=pn.pane.Markdown(
            object=agent_question,
            styles=configuration.chat_styles
        ),
        user=agent_name,
        respond=False,
        avatar=f"{configuration.avatar_images[agent_name]}",
    )
    configuration.spinner.value = False
    configuration.spinner.visible = False

    while configuration.user_input == None:
        sleep(1)

    human_comments = configuration.user_input
    configuration.user_input = None

    configuration.spinner.value = True
    configuration.spinner.visible = True
    return human_comments


@tool("update_env_variables")
def update_env_variables(*, API_ENDPOINT: str = None, API_BEARER_TOKEN: str = None):
    """
    This function will update the API Endpoint or API Bearer Token in the environment variables. It has 2 parameter it accepts:
    - API_ENDPOINT: The API Endpoint (Optional) to be updated in case of faulty API Endpoint in the .env file
    - API_BEARER_TOKEN: The API Endpoint (Optional) to be updated in case of faulty API Endpoint in the .env file
    """
    print("values received", API_BEARER_TOKEN, "\n", API_ENDPOINT)
    env_file = find_dotenv()
    load_dotenv(env_file)

    if API_ENDPOINT:
        # Update API endpoint in the .env file
        api_endpoint = (
            literal_eval(get_key(env_file, "API_ENDPOINT"))
            if get_key(env_file, "API_ENDPOINT")
            else {}
        )
        api_endpoint[configuration.selected_swagger_file] = API_ENDPOINT
        set_key(env_file, "API_ENDPOINT", api_endpoint, quote_mode="never")

    if API_BEARER_TOKEN:
        # Update API bearer token in the .env file
        api_bearer_token = (
            literal_eval(get_key(env_file, "API_BEARER_TOKEN"))
            if get_key(env_file, "API_BEARER_TOKEN")
            else {}
        )
        api_bearer_token[configuration.selected_swagger_file] = API_BEARER_TOKEN
        set_key(env_file, "API_BEARER_TOKEN", api_bearer_token, quote_mode="never")

# class SwaggerSplitter(BaseTool):
#     """
#     This tool splits will swagger file into multiple files."
#     """

#     name: str = "swagger_splitter"
#     description: str = (
#         """This tool splits will swagger file into multiple files, and generates a metadata file."""
#         """This tool accepts no input parameters, so just pass '{"input": {}}' as input."""
#     )

#     def _run(self) -> str:
#         if exists(configuration.generated_folder_path):
#             return dedent(
#                 """
#                     Swagger splitter has already run. If a user wants to force a rerun,
#                     they need to delete the 'generated' folder. If there exists no metadata summaries,
#                     or you fail to read the directory, you must run the Swagger API Description Summarizer.
#                     Exiting.
#                 """
#             )
#         for filename in listdir(configuration.swagger_files_directory):
#             if filename.endswith(".json"):
#                 swagger_parser(
#                     filename,
#                     configuration.swagger_files_directory,
#                     configuration.generated_folder_path,
#                 )

#         return f"""Swagger splitter has run successfully. The generated swagger files are in the directory {configuration.generated_folder_path}."""


class SummaryGenerator(BaseTool):
    """
    This tool passes provided text to an LLM model and returns a detailed summary.
    """

    name: str = "summary_generator"
    description: str = (
        """This tool passes provided text to an LLM model and returns a detailed summary. """
        """The tool accepts no inputs."""
    )

    def __init__(self):
        super().__init__()

    def _run(self):
        if exists(join(configuration.generated_folder_path, "metadata_summaries")):
            return """Metadata summaries have already been generated. Exiting."""

        makedirs(
            join(configuration.generated_folder_path, "summaries"),
            exist_ok=True,
        )

        swagger_summaries = {}

        human_template = """
        Generate a summary of the below provided metadata that is descriptive and concise. 
        Based on the provided API metadata, generate a detailed overview of the API's capabilities. Structure your response clearly to match the following categories:

        Endpoints: List all available endpoints with a brief description of each.
        Methods: Identify the HTTP methods (e.g., GET, POST) supported by each endpoint.
        Parameters: Detail required and optional parameters, including data types and descriptions for each endpoint.
        Authentication: Describe the authentication methods (e.g., API key, OAuth) needed to access the API.
        Use Cases: Suggest specific use cases for the API based on its capabilities.
        Ensure that your response is structured in a way that is straightforward for developers to understand and use for integration tasks and can be matched with task in plain english.

        ```
        {json_content}
        ```
        """
        llm = AzureChatOpenAI(azure_deployment=environ.get(
            "AZURE_OPENAI_DEPLOYMENT", "cml"
        )) if configuration.openai_provider == "AZURE_OPENAI" else ChatOpenAI()
        prompt_template = PromptTemplate(
            template=human_template, input_variables=["json_content"]
        )

        for filename in listdir(configuration.generated_folder_path):
            # all the generated metadata files
            if filename.endswith(".json"):
                json_content = ""
                with open(
                    join(configuration.generated_folder_path, filename), "r"
                ) as file:
                    json_content = file.read()

                prompt = prompt_template.format(json_content=json_content)
                message = HumanMessage(content=prompt)
                results = llm(messages=[message])
                swagger_summaries[
                    join(configuration.generated_folder_path, filename)
                ] = results.content

        dump(
            swagger_summaries,
            open(
                configuration.metadata_summaries_path,
                "w",
            ),
        )

        return f"""Metadata summaries have been generated successfully. The generated summaries are in the file {configuration.generated_folder_path}/metadata_summaries"""


class APICaller(BaseTool):
    """
    This tool accepts a very specific input and makes API calls.
    """

    name: str = "api_caller"
    description: str = (
        """This tool is meant to make API calls. The tool accepts inputs in the following format:
        ```
            "path": This is the path of the API endpoint,
            "method": This is the HTTP method,
            "parameters": This is a dictionary of parameters of form Dict[str,str] that need to be passed 
            to the API, with strictly no nesting of parameters. This field is of the form k:v
            where the key is the name of the parameter, and v is the value of the parameter.
            Using these parameters, the api_caller tool will construct the body and send the request.
            For example, "parameters": {"key1": "value1", "key2": "value2"...},
            "**kwargs": Extra arguments that might be necessary to make the API call, such as 
            "API_ENDPOINT" and "API_BEARER_TOKEN"
        ```
        """
    )

    class Config:
        arbitrary_types_allowed = True

    def __init__(self):
        super().__init__()

    def _run(self, path: str, method: str, parameters: Dict[str, str] = {}, *args, **kwargs):
        configuration.active_diagram.value = (
            f"{configuration.diagram_path}/{configuration.diagrams["api_caller"]}"
        )
        print("The parameters received are:", path, "\n", method, "\n", parameters, "\n", args, "\n", kwargs)
        load_dotenv(find_dotenv(), override=True)
        base_url = kwargs.get("API_ENDPOINT") if "API_ENDPOINT" in kwargs else \
        loads(environ.get("API_ENDPOINT").replace("'", '"'))[configuration.selected_swagger_file]
        base_url = base_url.rstrip("/")
        url = base_url + path

        # taking care of edge cases
        if "body" in parameters:
            for key, value in parameters["body"].items():
                parameters[key] = value
            del parameters["body"]

        bearer_token = kwargs.get("API_BEARER_TOKEN") if "API_BEARER_TOKEN" in kwargs else \
        loads(environ.get("API_BEARER_TOKEN").replace("'", '"'))[configuration.selected_swagger_file]
        
        headers = {"Authorization": f"Bearer {bearer_token}"}

        call_details = f"""Making request to: {url} with parameters: {parameters} and headers: {headers}"""
        configuration.chat_interface.send(
            value=pn.pane.Markdown(
                object=call_details,
                styles=configuration.chat_styles
            ), user="API Caller Tool", respond=False, avatar="🛠️"
        )

        if method.upper() == "GET":
            response = get(url, params=parameters, headers=headers, verify=False)
        elif method.upper() == "POST":
            response = post(url, json=parameters, headers=headers, verify=False)
        elif method.upper() == "PATCH":
            response = patch(url, json=parameters, headers=headers, verify=False)
        elif method.upper() == "DELETE":
            response = delete(url, json=parameters, headers=headers, verify=False)
        else:
            raise ValueError("Unsupported HTTP method")

        if response.ok:
            return response.json()
        else:
            return response._content.decode("utf-8")


# swagger_splitter = SwaggerSplitter()
summary_generator = SummaryGenerator()
api_caller = APICaller()
