from textwrap import dedent
from os import environ
from crewai import Agent
from crewai_tools import FileReadTool
from .callback_utils import custom_agent_callback
from .tools import (
    generated_directory_lister,
    metadata_summary_fetcher,
    get_human_input,
    api_caller,
    update_env_variables
)


from aiagents.config import Initialize


class ManagerAgents:
    def __init__(self, configuration: Initialize) -> None:
        self.task_matching_agent = Agent(
            role="Input Matcher",
            goal="""Match the tasks to the best matching API based on the metadata summaries."""
            """ Fetch the metadata summary using the metadata_summary_fetcher tool. If there"""
            """ is no metadata summary available, make sure that you return a meesage to the user with appropriate message that"""
            """none of API signatures are available and ask the user :- Please use ADMIN API to upload an OPEN API spec file."""
            """ Once metadata file is present, figure out which swagger metadata file is best"""
            """suited for the provided task. Only when you are confident about which swagger to use,"""
            """tell the user about the appropriate swagger metadata file to be used for the task.""",
            backstory="You are an expert in matching tasks to APIs.",
            verbose=True,
            allow_delegation=True,
            tools=[metadata_summary_fetcher, get_human_input],
            llm=configuration.llm,
            callbacks=configuration.customInteractionCallbacks,
            step_callback=custom_agent_callback,
            step_kwargs={"agent": "Input Matcher"}
        )

        self.manager_agent = Agent(
            role="API Selector Agent",
            goal=dedent(
                """
                Using the information provided in your context, your job is to read the contents of the specified metadata file 
                and decide which specific endpoint and method to use to fulfill the task. To decide which endpoint and method to
                use, you must see which description in the metadata file is the closest to the description of the task.
                Think through this decision carefully and make sure to provide a justification as to why you chose the
                that particular endpoint and method.

                For any query that comes your way, first read the metadata file, then and only then based on the metadata decide 
                on which endpoint suites the best. Use 'Decision Validator Agent' to validate the endpoints chosen. 
                Once you have decided on the endpoint and method to use, using the human input tool ask the user to provide 
                details about the parameters they would like to set while making the call. Make no assumptions here. 
                Make sure to clarify any doubts a user might have about the API call.

                If the user doesn't have some information on hand, or they ask you a question, make sure to fetch the appropriate 
                information, provide it to the user so they can tell you what information they need.
                
                Once the user has confirmed all the details, make the API call using api-caller-tool and return the results. If you run into errors
                while making the API call, make sure to try and deal with the error to the best of your abilities. If you determine that user inputs are needed to complete the call, 
                provide the error message back to the user, and ask for clarification about the same. Once the user has provided all the 
                required information, make the api call again using api-caller-tool with updated parameters and token/apikey if provided and not the old ones. Even after 3 retries, if you still
                get error, return the error message back to the user.

                After successfully making the API call, return the results to the user.
                """
            ),
            backstory=dedent(
                """
                You are an API selector and caller where based on the context received by the input matcher, you need to choose the exact 
                metadata file needed to use to service a user query. Make sure to generate full complete answers, and make no assumptions.

                You are also very experienced with understanding the importance of varied parameters. You are patient and can help 
                users with their queries. You are also very good at figuring out what action to take based on the situation, 
                and provide it to the user. Make sure you clearly state which parameters are optional and which are required. 
                """
            ),
            verbose=True,
            tools=[FileReadTool(), generated_directory_lister, api_caller, get_human_input, update_env_variables],
            llm=configuration.llm,
            allow_delegation=True,
            callbacks=configuration.customInteractionCallbacks,
            step_callback=custom_agent_callback,
            # step_kwargs={"agent": "API Selector Agent"}
        )
