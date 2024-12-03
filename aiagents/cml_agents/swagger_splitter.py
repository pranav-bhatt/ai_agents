from textwrap import dedent
from crewai import Agent

from .tools import (
    # swagger_splitter,
    summary_generator,
    generated_directory_lister,
    swagger_directory_lister,
)
from .callback_utils import custom_initialization_callback

from aiagents.config import Initialize




class SwaggerSplitterAgents:
    def __init__(self, configuration: Initialize) -> None:

        # Define the Summary Agent
        self.metadata_summarizer_agent = Agent(
            role="Swagger API Description Summarizer",
            goal=dedent(
                """
                Summarize the metadata files into descriptive, but succinct summaries.
                The summaries should as the first line contain the path where the metadata file is located. 
                The rest of the summary will contain information about all the capabilities of the API. 
                You will use the summary_generator tool to generate the summaries. It requires no inputs. 
                Ensure that the prompt you construct is created keeping in mind the above instructions.

                If you find that any directory or file you need is missing, that means that the swagger_splitter 
                tool has not been run. In that case, delegate the task to the swagger splitter agent, 
                and once its done, then run the summary generation via the summary_generator tool.
                
                Make no assumptions whatsoever. You are not to interact with the user for any purpose.
                """
            ),
            backstory="You are an expert in analysing swagger JSON files and summarising the API capabilities.",
            verbose=True,
            allow_delegation=False,
            tools=[
                summary_generator,
                generated_directory_lister,
            ],
            llm=configuration.llm,
            callbacks=configuration.customInitializationCallbacks,
            step_callback=custom_initialization_callback
        )
