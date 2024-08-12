from textwrap import dedent
from typing import Dict

from crewai import Task, Agent
from pydantic import BaseModel

from aiagents.config import Initialize


class Tasks:
    def __init__(self, configuration: Initialize, agents: Dict[str, Agent]) -> None:
        self.splitter_task = Task(
            description=dedent(
                """
                Find all the swagger files present in the target swagger directory and then split each swagger file.
                * If the folder called 'generated' is already present, consider this task as complete, and take no 
                further actions.
                * If the generated folder is not present, run the swagger splitter tool.
                
                Make no assumptions whatsoever.
                """
            ),
            expected_output="A concise answer stating the exact location of all the generated swagger metadata files.",
            agent=agents["swagger_splitter_agent"],
        )

        class metadata_summaries(BaseModel):
            summaries: dict[str, str]

        self.metadata_summarizer_task = Task(
            description=dedent(
                f"""
                Trigger the 'summary_generator' tool. This tool will automatically pick up the necessary swagger files
                from the {configuration.generated_folder_path}, and generate a summary for each of them. It outputs a structured
                k:v pair json, where the key is the location of the summarized swagger file, and the value is 
                the generated summary.

                If the metadata summary has already been generated, consider this task as complete, and take no 
                further actions.

                Make no assumptions whatsoever.
                """
            ),
            expected_output="A concise answer stating the exact location of the final generated metadata summary file.",
            agent=agents["metadata_summarizer_agent"],
            output_json=metadata_summaries,
            output_file=f"{configuration.generated_folder_path}/metadata_summaries",
            context=[self.splitter_task],
        )

        self.initial_human_input_task = Task(
            description=dedent(
                """
                Ask the human what action they would like to perform using the swaggers they have provided.
                """
            ),
            expected_output=dedent(
                """
                A clear answer stating the user action EXACTLY as they have mentioned within quotes, 
                and please don't change or miss a single word they have provided.
                """
            ),
            agent=agents["human_input_agent"],
        )

        self.task_matching_task = Task(
            description=dedent(
                """
                Complete the following steps:
                1. Fetch the metadata summary using the file read tool.
                2. Once metadata file is present, figure out which swagger metadata file is best suited for the task 
                already provided by the context of the human input task. The json is structured as k:v pairs where k is 
                the path of the swagger and v is the summary of the swagger.
                4. This is the most important step. Based on the metadata summaries, infer which swagger metadata 
                file will be best suited to address the query. If the description is not inherently clear such that 
                you aren't able to decide which swagger API needs to be used, make an assumption as to 
                which swagger file to use.
                5. Confirm the choice of API with the user by using the 'get_human_input' tool and make sure you provide 
                the reasoning behind why you chose it. If there is only one API available, or if you are very confident about
                the fact that a particular API can service the request, you can skip this step.
                6. Return the location of the swagger metadata file that has been chosen in the exact json format as below and finish execution:
                    'Format': {
                        'Description': 'This output contains the appropriate swagger metadata file to use for the task at hand'
                        'Appropriate Swagger Metadata File': {
                                'file_name': <file_name>,
                                'file_location': <file location>
                        }
                        'Task': <task>,
                        'Reason': <why the file was chosen>
                    }
                    Remember that this format shouldn't vary in any situation
                """
            ),
            expected_output="A concise answer stating the exact location of the appropriate swagger metadata file, "
            """as well as the reason why it is the one that has been chosen.""",
            agent=agents["task_matching_agent"],
            context=[self.metadata_summarizer_task, self.initial_human_input_task],
        )

        self.validator_task = Task(
            description=dedent(
                """
                Follow the below steps:
                1. Observe the original query passed to the agent that asked your validation and understand its nuances
                2. Observe the answer of the agent that has asked your validation and understand the exact outcome that will be produced
                3. Using the above points, deduce whether or not the agent's actions will result in the satisfactory completion of the original query 
                4. State your conclusion explicitly and explain why you reached that conclusion in a succinct manner to the 
                calling agent and let it continue with the rest of its tasks
                """
            ),
            expected_output=dedent(
                """
                Output the conclusion and reasoning as to whether or not the action of the agent will result in the 
                original query posed to the agent to be addressed
                """
            ),
            agent=agents["validator_agent"],
            context=[self.metadata_summarizer_task],
        )

        class managerDecision(BaseModel):
            """
            This class is used to store the decision made by the manager agent. It has several fields:
            - endpoint: The endpoint that the manager agent has decided needs to be used.
            - method: The HTTP method that the manager agent has decided needs to be used.
            - file: The location of the split metadata file associated with the endpoint..
            - user_query: The original user query verbatim.
            - reasoning: The reasoning behind why the manager agent has decided to use this particular endpoint and method .
            """

            endpoint: str
            method: str
            file: str
            user_query: str
            reasoning: str

        self.manager_task = Task(
            description=dedent(
                """
                Follow the following steps:
                1. Read the contents of the metadata file using the file read tool. The location of the metadata file 
                should be fetched from the task matcher task's context.
                2. Once the contents of the metadata file are present, decide which endpoint and HTTP method is most suitable
                to fulfill the task based on how similar the user query is to the description of the endpoint and method.
                3. Present your choice of endpoint and method with justification to the validator agent along with the 
                original query. The validator agent will either approve your choice or provide suggestions for improvement.
                4. If suggestions are provided, adjust your choice accordingly and seek approval again.
                5. Once the validator confirms your choice, output only the 'file' field associated with that endpoint, and
                the original user query verbatim.
                """
            ),
            expected_output=dedent(
                """
                The output should be of the structure of the managerDecision class. It has several fields:
                    - endpoint: The endpoint that the manager agent has decided needs to be used.
                    - method: The HTTP method that the manager agent has decided needs to be used.
                    - file: The location of the split metadata file associated with the endpoint..
                    - query: The original user query verbatim.
                    - reasoning: The reasoning behind why the manager agent has decided to use this particular endpoint and method .
                """
            ),
            output_json=managerDecision,
            context=[
                self.task_matching_task,
                self.initial_human_input_task,
                self.validator_task,
            ],
            agent=agents["manager_agent"],
        )

        self.api_calling_task = Task(
            description=dedent(
                """
                Complete the following steps to make the API call, using the context obtained from the manager_task:
                1. Read the swagger metadata file and identify the API call that the user has asked for. To construct the 
                full path of the API call file, you will need to combine the information obtained from the manager task, 
                as well as the path of the generated folder '{configuration.generated_folder_path}'.
                2. Identify the parameters that are required and optional.
                4. If you don't already have the information, ask the user to provide the information about the parameters.
                Make sure to explicitly specify which parameters are the required and which are optional and also ensure
                to explain each parameter in a well formatted, yet succinct manner. If the user doesn't specify required
                parameters, prompt them gently again. If they leave out optional parameters, proceed without setting them.
                3. If the user asks for information that you don't have, ask your boss, the API selector, to make another 
                API call to help get the information. Once the information is fetched, provide it back to the user in a 
                well formatted manner.
                5. Once the user has provided the necessary information, we need to call the 'api_caller' tool. 
                The api_caller tool , 
                and the value is the value of the parameter. Once you pass the parameters, the tool has logic that will
                parse it and perform the API call on your behalf. Make sure to refer to the description of the 'api_caller'
                tool while passing parameters. Once you have constructed the final list of parameters, show it to the
                user and get a confirmation that they are fine with the payload.
                6. Make the API call by triggering the API call tool. If the API call returns an error, try to deal with 
                the error yourself. If you determine that the error needs user intervention / clarification from the user,
                go ahead and ask the user the necessary query. Once you have the details, go ahead and try to make the API
                call again. The 'api_caller' tool supports **kwargs which you can use to send any extra parameters such as
                "API_BEARER_TOKEN" and "API_ENDPOINT" in case the API call returned an error due to incorrect API endpoint 
                or Bearer token being used, and the user has provided you with rectified values when you reported the error.
                7. Once a satisfactory output has been obtained, return the outcome of the api call.
                8. Once the outcome is returned, using the 'get_human_input' tool, inform the user with the below prompt:
                'Please Reload the Crew if you have any other queries to be answered', and finish the execution.
                """
            ),
            expected_output=dedent(
                """
                Output the result of the API call talking about the action that has been taken in a concise manner.
                """
            ),
            agent=agents["api_caller_agent"],
            context=[self.initial_human_input_task, self.manager_task],
        )
