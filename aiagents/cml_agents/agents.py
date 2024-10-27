from textwrap import dedent

from crewai import Agent
from crewai_tools import FileReadTool, DirectoryReadTool

from aiagents.config import Initialize
from .tools import get_human_input, api_caller


class Agents:
    def __init__(self, configuration: Initialize) -> None:
        # self.api_caller_agent = Agent(
        #     role="API Caller Agent",
        #     goal=dedent(
        #         f"""
        #         Based on the information provided by the manager task, fetch the user query, as well as the file containing
        #         the API call information. If you cannot find the generated folder, that means the swagger splitter has not
        #         run yet. After that you will need to read the file and determine the exact details of the API call. Identify 
        #         which parameters are required and which are optional. 
                
        #         Based on all the information gathered, incase you don't already have the information in hand, using the 
        #         human input tool ask the user to provide details about the fields they would like to set while making the
        #         call. Make no assumptions here. Make sure to clarify any doubts a user might have about the API call.

        #         If the user doesn't have some information on hand, or they ask you a question you aren't sure of, make sure
        #         to ask the manager agent to fetch the information for you. Once the manager agent has fetched the information, 
        #         provide it back to the user so they can tell you what information they need.
                
        #         Once the user has confirmed all the details, make the API call and return the results. If you run into errors
        #         while making the API call, make sure to try and deal with the error to the best of your abilities. If you 
        #         determine that user inputs are needed to complete the call, provide the error message back to the user, 
        #         and ask for clarification about the same. Once the user has provided all the required information, make the
        #         call again.

        #         After successfully making the API call, give the user the results through the human input tool. Post this, ask 
        #         the user using the human input tool to Reload the Crew if they have any further queries, and end the execution.
        #         """
        #     ),
        #     backstory=dedent(
        #         """
        #         You are an intelligent, helpful API caller who is very experienced with understanding the importance of 
        #         varied parameters. You are patient and can help users with their queries. You are also very good at
        #         figuring out what action to take based on the situation, and if the user asks for information that you
        #         aren't aware of, you can ask your boss, the API selector to help fetch the information so you can,
        #         provide it to the user. Make sure you clearly state which parameters are optional and which are required.
        #         Make no assumptions."
        #         """
        #     ),
        #     allow_delegation=True,
        #     verbose=True,
        #     tools=[
        #         get_human_input,
        #         FileReadTool(),
        #         DirectoryReadTool(),
        #         api_caller,
        #     ],
        #     llm=configuration.llm,
        #     callbacks=configuration.customInteractionCallbacks,
        # )

        self.human_input_agent = Agent(
            role="Human Input Agent",
            goal=dedent(
                """
                Prompt the user with concise, yet detailed information about any information that the agent that delegated
                the query to needs to know. If a user asks any queries, pass the user's query back to the agent that gave 
                you the task. If the user provides the information, pass it back to the agent that gave you the task and
                complete your execution.
                """
            ),
            backstory=dedent(
                """
                You are a super kind, helpful and intelligent agent aiming to help gather required information from a user. 
                You only gather the information that has been asked of you, and it is the job of the agent that delegated the
                task aid the user with queries they ask. You are not to directly answer any queries on your own.
                """
            ),
            allow_delegation=False,
            verbose=True,
            tools=[get_human_input],
            llm=configuration.llm,
            callbacks=configuration.customInteractionCallbacks,
        )

        self.validator_agent = Agent(
            role="Decision Validator Agent",
            goal=dedent(
                """
                Observe the original query passed to the agent that called you for your validation and understand its nuances. 
                Validate the answer of the agent that has asked your validation and understand the exact outcome that will be produced
                You should be able to deduce whether or not the agent's actions will result in the satisfactory completion of the original query 
                You should also be able to state your conclusion explicitly and provide explanation on why you reached that conclusion 
                in a succinct manner.

                Once you've made a decision, make sure to pass back the decision to the agent that asked you this question so it can
                incorporate your feedback.
                """
            ),
            backstory=dedent(
                """
                You are an expert in observing and validating actions taken by the agents that call you for your opinions and deduction
                skills.
                """
            ),
            verbose=True,
            allow_delegation=False,
            llm=configuration.llm,
            callbacks=configuration.customInteractionCallbacks,
        )
