from textwrap import dedent
from crewai import Agent

from .tools import (
    swagger_splitter,
    summary_generator,
    generated_directory_lister,
    swagger_directory_lister,
)

from aiagents.config import Initialize


class SwaggerSplitterAgents:
    def __init__(self, configuration: Initialize) -> None:
        # Define the Swagger Splitter Agent
        self.swagger_splitter_agent = Agent(
            role="swagger_splitter",
            goal=dedent(
                """
                Follow the following steps:
                    1. Use the directory read tool to find all Swagger JSON files in the specified directory.
                    2. If the generated folder doesn't exist, for each Swagger JSON file found run the 'swagger_splitter'
                    tool on the file. Upon running the tool, mark your execution as finished.
                    3. Using the previous output, check if the generated folder exists. If it does, then that means that
                    the tool has already run, and we can consider that the 'swagger_splitter' tool has run. Note that this
                    does not mean that the metadata summaries have been generated. 
                    
                The 'swagger_splitter' tool processes the file and generates smaller files. The swagger_splitter tool does
                not generate the metadata summaries, and the check whether or not the metadata summary files have to be generated
                needs to be performed by the Swagger API Description Summarizer agent.
                
                Make no assumptions whatsoever.
                """
            ),
            backstory="""You are an expert in processing Swagger files. Your primary responsibility is to """
            """split large Swagger JSON files into smaller, more manageable files to facilitate efficient """
            """processing and distribution across multiple services.""",
            verbose=True,
            allow_delegation=False,
            tools=[swagger_splitter, swagger_directory_lister],
            llm=configuration.llm,
            callbacks=configuration.customCallbacks,
        )

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

                If there are no summaries available, that means that the swagger_splitter tool has not been run.
                In that case, delegate the task to the swagger splitter agent, and once its done, then run the 
                summary generation via the summary_generator tool.
                
                Make no assumptions whatsoever.
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
            callbacks=configuration.customCallbacks,
        )
