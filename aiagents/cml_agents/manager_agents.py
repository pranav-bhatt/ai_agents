from textwrap import dedent

from crewai import Agent
from crewai_tools import FileReadTool

from .tools import (
    generated_directory_lister,
    metadata_summary_fetcher,
    get_human_input,
)

from aiagents.config import Initialize


class ManagerAgents:
    def __init__(self, configuration: Initialize) -> None:
        self.task_matching_agent = Agent(
            role="Task Matcher",
            goal="""Match the tasks to the best matching API based on the metadata summaries."""
            """ Fetch the metadata summary using the metadata_summary_fetcher tool. If there"""
            """ is no metadata summary available, make sure the swagger_splitter agent runs first."""
            """ Once metadata file is present, figure out which swagger metadata file is best"""
            """suited for the provided task Only once you are confident about which swagger to use,"""
            """tell the user the what the appropriate swagger metadata file to use for the task.""",
            backstory="You are an expert in matching tasks to APIs.",
            verbose=True,
            allow_delegation=True,
            tools=[metadata_summary_fetcher, get_human_input],
            llm=configuration.llm,
            callbacks=configuration.customCallbacks,
        )

        self.manager_agent = Agent(
            role="API Selector Agent",
            goal=dedent(
                """
                Using the information provided in your context, your job is to read the contents of the specified metadata file 
                and decide which specific endpoint and method to use to fulfill the task. To decide which endpoint and method to
                use, you must see which description in the metadata file is the closest to the description of the task.
                Think through this decision carefully and make sure to provide a justification as to why you chose the
                that particular endpoint and method. Once you have decided on the endpoint and method to use, you must delegate
                the task to the API caller agent and provide it with the 'file' field associated with the endpoint, as well as
                the original user query verbatim.

                It can also happen that the API caller agent in return asks you to fetch details about some parameters. In 
                this case you must take a look at the metadata file and have the API caller agent execute the call to fetch
                those details. Once the requested details are fetched, we can return the result to the API caller agent so it can
                finish the original task.

                For any query that comes your way, first read the metadata file, then and only then based on the metadata decide 
                on which endpoint suites the best.
                """
            ),
            backstory=dedent(
                """
                You an API selector where based on the context received by the task matcher, you need to help out the 
                API Caller agent by telling it the exact metadata file it needs to use to service a user query. 
                You need to make sure that you are able to provide the API agent with concise information about the file 
                location. Make sure to provide full complete answers, and make no assumptions.

                You are the boss of the API caller agents and need to do your best to help them complete their tasks.
                """
            ),
            verbose=True,
            tools=[FileReadTool(), generated_directory_lister],
            llm=configuration.llm,
            allow_delegation=True,
            callbacks=configuration.customCallbacks,
        )
