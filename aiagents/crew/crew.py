from os import environ, listdir
import os
import shutil
from aiagents.custom_threading import threads
from aiagents.config import configuration
from crewai import Crew
from dotenv import find_dotenv, get_key, load_dotenv, set_key
import panel as pn
from bokeh.server.contexts import BokehSessionContext
from aiagents.cml_agents.manager_agents import ManagerAgents
from aiagents.cml_agents.swagger_splitter import SwaggerSplitterAgents
from aiagents.cml_agents.agents import Agents
from aiagents.cml_agents.parse_for_manager import swagger_parser
from aiagents.cml_agents.callback_utils import custom_callback, custom_initialization_callback
from aiagents.cml_agents.tasks import Tasks, TasksInitialize

from aiagents.config import Initialize, configuration
from aiagents.custom_threading import threads

from aiagents.panel_utils.panel_stylesheets import chat_stylesheet


# we can't directly import the agents and tasks because we want to ensure that the configuration is first
# initialize the configuration with panel hooks, and then pass it as an argument
def StartCrewInitialization(configuration: Initialize):
    #manager_agents = ManagerAgents(configuration=configuration)
    swagger_splitter_agents = SwaggerSplitterAgents(configuration=configuration)
    #agents = Agents(configuration=configuration)
    ##please call swagger splitter here

    ## if generated folder has any entries delete the same.

    # """Delete all files and subdirectories inside the specified directory."""
    # if os.path.exists(configuration.generated_folder_path):
    #     # Remove the directory and all its contents
    #     shutil.rmtree(configuration.generated_folder_path)
    #     # Recreate the empty directory
    #     os.makedirs(configuration.generated_folder_path)

    env_file = find_dotenv()
    load_dotenv(env_file)
    file_count = get_key(env_file, "fileCount")
    try:
        file_count = int(file_count)
    except:
        file_count = 0
    if file_count >= 1:
        configuration.metadata_summarization_status.value = (
            f"Processing the API Specification file {configuration.new_file_name} ⏱" 
        )
    else:
        configuration.chat_interface.send(
            pn.pane.Markdown(
                f"""Your API specification file, **{configuration.new_file_name}**, is currently being processed to figure out metadata to route future requests. This may take a few moments as we thoroughly analyze its content to ensure all details are accurately captured.
                We kindly request your patience during this process, and you will be notified immediately upon its completion.""",
                styles=configuration.chat_styles,
                stylesheets=[chat_stylesheet]
            ),
            user="System",
            respond=False,
            avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
        )
        configuration.initialization_spinner.visible = True
        configuration.initialization_spinner.value = True

    for filename in listdir(configuration.swagger_files_directory):
            if filename == configuration.new_file_name:
                swagger_parser(
                    filename,
                    configuration.swagger_files_directory,
                    configuration.generated_folder_path,
                )
    agent_dict = {
        "metadata_summarizer_agent": swagger_splitter_agents.metadata_summarizer_agent,
    }
    tasks = TasksInitialize(configuration=configuration, agents=agent_dict)
    embedding = {
        "provider": "azure_openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            ),
            "deployment_name": environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "ada-embedding"
            ),
        },
    } if configuration.openai_provider=="AZURE_OPENAI" else {
        "provider": "openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            )
        },
    }

    splitterCrew = Crew(
        agents=[
            agent_dict["metadata_summarizer_agent"],
        ],
        tasks=[
            tasks.metadata_summarizer_task,
        ],
        verbose=1,
        memory=False,
        embedder=embedding,
        task_callback=custom_initialization_callback
    )
    try:
        configuration.processing_file = True
        splitterCrew.kickoff()
        env_file = find_dotenv()
        load_dotenv(env_file)
        file_count = get_key(env_file, "fileCount")
        try:
            file_count = int(file_count)
        except:
            file_count = 0
        if file_count == 0:
            configuration.chat_interface.send(
                pn.pane.Markdown(
                    f"""The API Specification File {configuration.new_file_name} has been successfully processed.""",
                    styles=configuration.chat_styles,
                    stylesheets=[chat_stylesheet]
                ),
                user="System",
                respond=False,
                avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
            )
            configuration.initialization_spinner.visible = False
            configuration.initialization_spinner.value = False
            session_created()
        else:
            configuration.metadata_summarization_status.value = f"Processed the API Specification File {configuration.new_file_name}"
        file_count += 1
        set_key(env_file, 'fileCount',str(file_count))
        configuration.processing_file = False
        if not configuration.empty_inputs:
            configuration.upload_button.disabled = False
    except Exception as err:
        load_dotenv(env_file)
        file_count = get_key(env_file, "fileCount")
        try:
            file_count = int(file_count)
        except:
            file_count = 0
        if file_count == 0:
            configuration.chat_interface.send(
                pn.pane.Markdown(
                    f"""Failed with: {err}\nPlease upload the details again.""",
                    styles=configuration.chat_styles,
                    stylesheets=[chat_stylesheet]
                ),
                user="System",
                respond=False,
                avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
            )
            configuration.initialization_spinner.visible = False
            configuration.initialization_spinner.value = False
        else:
            configuration.metadata_summarization_status.value = f"Failed with: {err}\nPlease upload the details again."
        configuration.spinner.visible=False
        configuration.spinner.value=False
        configuration.reload_button.disabled=False
        configuration.processing_file=False
        if not configuration.empty_inputs:
            configuration.upload_button.disabled = False




def StartCrewInteraction(configuration: Initialize):
    manager_agents = ManagerAgents(configuration=configuration)
    agents = Agents(configuration=configuration)



    agent_dict = {
        "task_matching_agent": manager_agents.task_matching_agent,
        "manager_agent": manager_agents.manager_agent,
        "human_input_agent": agents.human_input_agent,
        "validator_agent": agents.validator_agent,
    }

    tasks = Tasks(configuration=configuration, agents=agent_dict)

    embedding = {
        "provider": "azure_openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            ),
            "deployment_name": environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "ada-embedding"
            ),
        },
    } if configuration.openai_provider=="AZURE_OPENAI" else {
        "provider": "openai",
        "config": {
            "model": environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
            )
        },
    }

    splitterCrew = Crew(
        agents=[
            agent_dict["task_matching_agent"],
            agent_dict["manager_agent"],
            agent_dict["human_input_agent"],
            agent_dict["validator_agent"],
        ],
        tasks=[
            tasks.initial_human_input_task,
            tasks.task_matching_task,
            tasks.manager_task,
        ],
        verbose=1,
        memory=False,
        embedder=embedding,
        task_callback=custom_callback
    )

    try:
        splitterCrew.kickoff()

        configuration.chat_interface.send(
            pn.pane.Markdown(
                "Execution Completed", 
                styles=configuration.chat_styles,
                stylesheets=[chat_stylesheet]
            ), 
            user="System", 
            respond=False,
            avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
        )
        reset_for_new_input()
        configuration.spinner.value = False
        configuration.spinner.visible = False
    
    except Exception as err:
        configuration.chat_interface.send(
            pn.pane.Markdown(
                object=f"Starting Interaction Crew Failed with {err}\n Please try restarting the crew.",
                styles=configuration.chat_styles,
                stylesheets=[chat_stylesheet]
            ),
            user="System",
            respond=False,
            avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
        )

        configuration.spinner.visible=False
        configuration.spinner.value=False
        configuration.reload_button.disabled=False



# Handle session creation, which includes starting the CrewAI process
def session_created():
    # Disable the start button and clear chat interface to start a session
    configuration.chat_interface.send(
        pn.pane.Markdown(
            "Starting the Crew",
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ), user="System", respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
    )
    # Show the loading spinner as the Crew loads
    configuration.spinner.value = True
    configuration.spinner.visible = True
    configuration.crew_thread = threads.ThreadWithTrace(
        target=StartCrewInteraction, args=(configuration,)
    )
    configuration.crew_thread.daemon = True  # Ensure the thread dies when the main thread (the one that created it) dies
    configuration.crew_thread.start()

def create_session_without_start_button():
    configuration.chat_interface.send(
        pn.pane.Markdown(
            "Thank you. \n Please enter further query below once the Human Input Agent is available.",
            styles=configuration.chat_styles,
            stylesheets=[chat_stylesheet]
        ), user="System", respond=False,
        avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
    )
    # Show the loading spinner as the Crew loads
    configuration.spinner.value = True
    configuration.spinner.visible = True
    configuration.crew_thread = threads.ThreadWithTrace(
        target=StartCrewInteraction, args=(configuration,)
    )
    configuration.crew_thread.daemon = True  # Ensure the thread dies when the main thread (the one that created it) dies
    configuration.crew_thread.start()

def reset_for_new_input():
    # Set the active diagram to the current full diagram path for visualization
    configuration.active_diagram.value = (
        f"{configuration.diagram_path}/{configuration.diagrams['full']}"
    )
    # Attempt to kill the currently running crew thread, if any
    try:
        print("Stopping thread...")
        success = configuration.crew_thread.stop()
        
        if not success:
            print("Soft stop failed, forcing thread termination")
            killed = configuration.crew_thread.force_stop()
            print(f"Force thread termination gave {killed}")
        
        configuration.crew_thread.join()
        print("Thread terminated")
        print("Successfully killed thread")
    except:
        print("Not able to kill the thread")
        pass
    configuration.reload_button.disabled = True
    configuration.spinner.visible = False
    configuration.spinner.value = False
    print("Setting configuration")
    create_session_without_start_button()