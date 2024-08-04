from pathlib import Path
from os.path import join
from os import environ
from aiagents.custom_threading import threads

from dotenv import load_dotenv, find_dotenv

from langchain_openai import AzureChatOpenAI
import panel as pn


class Initialize:

    diagrams = {
        "full": "full.jpg", 
        "Human Input Agent": "human_input.jpg", 
        "Task Matcher": "task_matcher.jpg", 
        "swagger_splitter": "swagger_splitter.jpg", 
        "Swagger API Description Summarizer": "metadata_summariser.jpg", 
        "API Selector Agent": "api_selector.jpg",
        "Decision Validator Agent": "decision_validator.jpg",
        "API Caller Agent": "api_caller.jpg",
        "API Calling Tool": "api_tool.jpg"
    }

    def __init__(self):
        current_file_path = Path(__file__).resolve()
        project_root = str(current_file_path.parents[2])

        environ["PROJECT_ROOT"] = project_root

        self.project_root = environ.get("PROJECT_ROOT")
        self.app_port = int(environ.get("CDSW_APP_PORT", "8080"))

        self.swagger_files_directory = environ.get(
            "SWAGGER_FILES_DIRECTORY", f"{self.project_root}/swagger_files"
        )
        self.generated_folder_path = join(self.swagger_files_directory, "generated")
        self.metadata_summaries_path = join(
            self.generated_folder_path, "summaries", "metadata_summaries"
        )
        self.selected_swagger_file = ""
        self.user_input = None
        self.first_run = pn.Param.param

        self.sidebar: pn.Column = None
        self.chat_interface: pn.chat.ChatInterface = None
        self.spinner: pn.indicators.LoadingSpinner = None
        self.reload_button : pn.widgets.Button = None

        self.customCallbacks = []
        self.diagram_path = f"{self.project_root}/assets/images"
        self.active_diagram = pn.widgets.TextInput(value=f"{self.diagram_path}/{self.diagrams['full']}")
        self.crew_thread: threads.thread_with_trace = None

    def update_configuration(self):
        load_dotenv(find_dotenv(), override=True)

        # from langchain_groq import ChatGroq
        # self.llm = ChatGroq(
        #     temperature=0,
        #     model_name="llama3-70b-8192",
        #     api_key="gsk_",
        # )

        self.llm = AzureChatOpenAI(azure_deployment="cml")
        self.llm.temperature = float(environ.get("LLM_TEMPERATURE", 0.4))
        print("LLM temperature: ", self.llm.temperature)


global configuration
configuration = Initialize()
