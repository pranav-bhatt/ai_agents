from os import environ

from crewai import Crew

from aiagents.cml_agents.manager_agents import ManagerAgents
from aiagents.cml_agents.swagger_splitter import SwaggerSplitterAgents
from aiagents.cml_agents.agents import Agents

from aiagents.cml_agents.tasks import Tasks

from aiagents.config import Initialize


# we can't directly import the agents and tasks because we want to ensure that the configuration is first
# initialize the configuration with panel hooks, and then pass it as an argument
def StartCrew(configuration: Initialize):
    manager_agents = ManagerAgents(configuration=configuration)
    swagger_splitter_agents = SwaggerSplitterAgents(configuration=configuration)
    agents = Agents(configuration=configuration)

    agent_dict = {
        "swagger_splitter_agent": swagger_splitter_agents.swagger_splitter_agent,
        "metadata_summarizer_agent": swagger_splitter_agents.metadata_summarizer_agent,
        "task_matching_agent": manager_agents.task_matching_agent,
        "manager_agent": manager_agents.manager_agent,
        "human_input_agent": agents.human_input_agent,
        "api_caller_agent": agents.api_caller_agent,
        "validator_agent": agents.validator_agent,
    }

    tasks = Tasks(configuration=configuration, agents=agent_dict)

    global splitterCrew
    splitterCrew = Crew(
        agents=[
            agent_dict["swagger_splitter_agent"],
            agent_dict["metadata_summarizer_agent"],
            agent_dict["task_matching_agent"],
            agent_dict["manager_agent"],
            agent_dict["human_input_agent"],
            agent_dict["api_caller_agent"],
            agent_dict["validator_agent"],
        ],
        tasks=[
            tasks.initial_human_input_task,
            tasks.task_matching_task,
            tasks.manager_task,
            tasks.api_calling_task,
        ],
        verbose=1,
        memory=True,
        embedder={
            "provider": "azure_openai",
            "config": {
                "model": environ.get(
                    "AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
                ),
                "deployment_name": environ.get(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "ada-embedding"
                ),
            },
        },
    )

    splitterCrew.kickoff()
