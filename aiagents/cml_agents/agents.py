from textwrap import dedent

from crewai import Agent
from crewai_tools import FileReadTool, DirectoryReadTool

from aiagents.cml_agents.callback_utils import custom_agent_callback
from aiagents.config import Initialize
from .tools import get_human_input, api_caller


class Agents:
    def __init__(self, configuration: Initialize) -> None:

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
            step_callback=custom_agent_callback,
            step_kwargs={"agent": "Human Input Agent"}
        )

        self.validator_agent = Agent(
            role="Decision Validator Agent",
            goal=dedent(
                """
                Observe the original query passed to the agent that called you for your validation and understand its nuances. 
                Validate the answer of the agent that has asked your validation strictly and understand the exact outcome that will be produced.
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
            allow_delegation=True,
            llm=configuration.llm,
            callbacks=configuration.customInteractionCallbacks,
            step_callback=custom_agent_callback,
            step_kwargs={"agent": "Decision Validator Agent"}
        )
