from textwrap import dedent
from typing import Dict

from crewai import Task, Agent
from pydantic import BaseModel, Field, field_validator

from aiagents.config import Initialize

class TasksInitialize:
    def __init__(self, configuration: Initialize, agents: Dict[str, Agent]) -> None:

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
            output_file=f"{configuration.generated_folder_path}/metadata_summaries",
        )





class Tasks:
    def __init__(self, configuration: Initialize, agents: Dict[str, Agent]) -> None:
        # self.splitter_task = Task(
        #     description=dedent(
        #         """
        #         Find all the swagger files present in the target swagger directory and then split each swagger file.
        #         * If the folder called 'generated' is already present, consider this task as complete, and take no 
        #         further actions.
        #         * If the generated folder is not present, run the swagger splitter tool.
                
        #         Make no assumptions whatsoever.
        #         """
        #     ),
        #     expected_output="A concise answer stating the exact location of all the generated swagger metadata files.",
        #     agent=agents["swagger_splitter_agent"],
        # )

        # class metadata_summaries(BaseModel):
        #     summaries: dict[str, str]

        # self.metadata_summarizer_task = Task(
        #     description=dedent(
        #         f"""
        #         Trigger the 'summary_generator' tool. This tool will automatically pick up the necessary swagger files
        #         from the {configuration.generated_folder_path}, and generate a summary for each of them. It outputs a structured
        #         k:v pair json, where the key is the location of the summarized swagger file, and the value is 
        #         the generated summary.

        #         If the metadata summary has already been generated, consider this task as complete, and take no 
        #         further actions.

        #         Make no assumptions whatsoever.
        #         """
        #     ),
        #     expected_output="A concise answer stating the exact location of the final generated metadata summary file.",
        #     agent=agents["metadata_summarizer_agent"],
        #     #output_json=metadata_summaries,
        #     output_file=f"{configuration.generated_folder_path}/metadata_summaries",
        #     # context=[self.splitter_task],
        # )

        class humanInputOutput(BaseModel):
            """
            This class is used to store the decision made by the input matcher agent. It has several fields:
            - answer: A clear answer stating the user action EXACTLY as they have mentioned within quotes
            - role: The role of the agent executing the task
            """

            answer: str
            role: str

        self.initial_human_input_task = Task(
            description=dedent(
                """
                Ask the human what action they would like to perform using the API Specification file they have provided and 
                format the result in the exact structure required by the 'humanInputOutput' class.
                """
            ),
            expected_output=dedent(
                f"""
                The output should be of the structure of the humanInputOutput class. It has several fields:
                    - answer: A clear answer stating the user action EXACTLY as they have mentioned within quotes, 
                        and please don't change or miss a single word they have provided. 
                    - role: The value of {agents['human_input_agent'].role}
                """
            ),
            output_json=humanInputOutput,
            agent=agents["human_input_agent"],
        )

        class inputMatcherDecision(BaseModel):
            """
            This class is used to store the decision made by the input matcher agent. It has several fields:
            - file_name: The file name of the appropriate swagger metadata file chosen.
            - file_location: The path or location of the appropriate swagger metadata file chosen.
            - task: The task at hand for which the swagger file was chosen.
            - reason: The reasoning behind why the input matcher agent has decided to use this particular swagger metadata file.
            - description: The description of this class used to identify the output
            - role: The role of the agent executing the task
            """

            file_name: str
            file_location: str
            task: str
            reason: str
            description: str = Field("This output contains the appropriate swagger metadata file to use for the task at hand", frozen=True)
            role: str

            @field_validator('description')
            def set_fixed_method(cls, v):
                return "This output contains the appropriate swagger metadata file to use for the task at hand"

        self.task_matching_task = Task(
            description=dedent(
                """
                Complete the following steps:
                1. Fetch Metadata Summary:
                    1. Use the 'file read tool' to retrieve the metadata summary file. Ensure the contents are fully loaded before proceeding. If and only if no metadata summary file is available, return an error message indicating no API spec is available and Finish Execution by throwing an error with apt messaging..
                2. Identify the Relevant Swagger File:
                    1. Review the metadata file, which consists of key-value pairs where each key is the path of a Swagger file and each value is a summary.
                    2. Based on the context provided by the human input task, analyze the summaries to determine which Swagger file aligns best with the task requirements.
                3. Infer the Best Swagger File:
                    1. Critical step: If the summaries are unclear or do not directly indicate the appropriate Swagger file, make a logical assumption based on the descriptions and your understanding of the task.
                    2. Prioritize selecting the Swagger file that most closely matches the user's query and the context of the task.
                4. Confirm with the User (Optional):
                    1. If multiple API options are available, or if you are uncertain about your choice, use the 'get_human_input' tool to confirm your decision with the user.
                    2. Provide a clear explanation of why you selected this particular Swagger API.
                    3. If only one option exists or you are highly confident, you can skip this step and proceed directly.
                5. Return Swagger Metadata Location:
                    1. Once the appropriate Swagger file is identified, format the result in the exact structure required by the 'inputMatcherDecision' class.
                    2. Include the description: "This output contains the appropriate swagger metadata file to use for the task at hand."
                    3. Finish execution.
                """
            ),
            expected_output="A concise answer stating the exact location of the appropriate swagger metadata file, "
            f"""as well as the reason why it is the one that has been chosen. The output should be of the structure 
            of the inputMatcherDecision class. It has several fields:
                - file_name: The file name of the appropriate swagger metadata file chosen.
                - file_location: The path or location of the appropriate swagger metadata file chosen.
                - task: The task at hand for which the swagger file was chosen.
                - reason: The reasoning behind why the input matcher agent has decided to use this particular swagger metadata file.
                - description: The description of this class which will be used to identify the output = 'This output contains 
                the appropriate swagger metadata file to use for the task at hand'
                - role: The value of {agents['task_matching_agent'].role}
            """,
            output_json=inputMatcherDecision,
            agent=agents["task_matching_agent"],
            context=[ self.initial_human_input_task],
        )

        class decisionValidatorOutput(BaseModel):
            """
            This class is used to store the decision validation done by the decision validator agent. It has two fields:
            - answer: The conclusion and reasoning as to whether or not the action of the agent will result in the original query posed to the agent to be addressed
            - role: The role of the agent executing the task
            """

            answer: str
            role: str

        self.validator_task = Task(
            description=dedent(
                """
                Follow the below steps:
                1. Understand the Original Query:
                    1. Carefully review the original query that was passed to the agent requesting validation. Pay close attention to its nuances, ensuring you grasp the user’s intent and expectations.
                2. Evaluate the Agent's Proposed Answer:
                    1. Analyze the response provided by the agent seeking validation. Understand the exact outcome that will be produced based on its actions.
                3. Assess the Outcome:
                    1. Based on your understanding of both the original query and the proposed answer, determine whether the agent's actions will satisfactorily fulfill the user's request. Consider potential gaps or mismatches.
                4. Provide a Conclusion:
                    1. Clearly state whether the agent's proposed solution will result in successful task completion.
                    2. Justify your conclusion with a concise explanation, detailing why the actions are or are not aligned with the original query.
                    3. Communicate your decision to the calling agent so it can proceed with the rest of its tasks accordingly by formatting the result in the exact structure required by the 'decisionValidatorOutput' class.
                """
            ),
            expected_output=dedent(
                f"""
                The output should be of the structure of the decisionValidatorOutput class. 
                It has several fields:
                    - answer: The conclusion and reasoning as to whether or not the action of the agent will result in the original query posed to the agent to be addressed
                    - role: The value of {agents['validator_agent'].role}
                """
            ),
            output_json=decisionValidatorOutput,
            agent=agents["validator_agent"],
        )

        class managerOutput(BaseModel):
            """
            This class is used to store the decision made by the input matcher agent. It has several fields:
            - answer: The exact full result of the 'api caller tool', summarized and formatted clearly and concisely
            - role: The role of the agent executing the task
            """

            answer: str
            role: str

        self.manager_task = Task(
            description=dedent(
                """
                Follow the following steps:
                1. Read the Metadata File:
                    1. Use the 'file read tool' to access the metadata file. The file location can be found in the context provided by the 'input matcher' agent.
                2. Select Endpoint and HTTP Method:
                    1. Analyze the metadata to identify the Swagger file that contains the endpoint most suited to the user query.
                    2. Match the user’s query to endpoint descriptions by evaluating the similarity between the user's intent and the function of the endpoint.
                3. Justify Endpoint Selection using Decision Validator Agent:
                    1. Present the selected endpoint and HTTP method to the 'decision validator' agent, explaining how it aligns with the user’s query. 
                    2. Make sure the justification is clear and directly tied to the user’s request.
                4. Handle Feedback from Validator:
                    1. If the 'decision validator' agent provides feedback, revise the selection and justify the change. 
                    2. Ensure the updated selection addresses the user's query, and seek validation again if necessary.
                5. Provide Parameters to User:
                    1. Extract both required and optional parameters from the selected endpoint's Swagger file.
                    2. Present the user with a clear list of required and optional parameters:
                        1. Required parameters: List them along with brief descriptions.
                        2. Optional parameters: Highlight optional parameters and describe how they enhance functionality.
                6. Request User Input:
                    1. Prompt the user to provide values for the required parameters based on the last step. Ensure that the request is polite and clear.
                    2. Proceed without optional parameters or use default values unless the user provides them or requests to include them.
                7. Respond to Additional Queries:
                    1. If the user requests further related information (e.g., related endpoints, more data from the Swagger file, 
                    or related API calls), assist them accordingly by retrieving the relevant details or making additional API calls as needed.
                8. Build and Confirm Payload:
                    1. Construct the final payload for the API call using the user-provided values for the parameters.
                    2. Display the payload to the user for their review and confirmation before proceeding with the API call.
                9. Execute the API Call:
                    1. Use the 'api-caller' tool to trigger the API call with the payload and intelligently handle any errors that occur during the process. 
                    2. If the issue requires user input or clarification, invoke the 'get human input' tool to ask the user for the relevant information.
                    3. If the API Endpoint or API Bearer Token are found to be incorrect, fetch their correct values from the user using the 'get human input' tool, 
                    and update the 'API_ENDPOINT' or 'API_BEARER_TOKEN' respectively using the 'update env variables' tool.
                    4. Using the 'api-caller' tool retry the API call with the updated parameters and updated token/key. Even after 3 retries, if you still
                    get error, return the error message back to the user.
                10. Return Results:
                    1. Once the API call is successful, return the full result to the user by formatting the result in the exact structure required by the 'managerOutput' class, and if there is an error, retry the API call for  max of 2 tries with 5 second delays and then return
                        the error if still the call is not successful.
                    2. If the result is complex, summarize it clearly and concisely to ensure easy understanding but make sure everything is sent to the user.
                """
            ),
            expected_output=dedent(
                f"""
                The output should be of the structure of the managerOutput class. 
                It has several fields:
                    - answer: Once the API call is successful, return the exact full result of the 'api caller tool'. If the result is complex, 
                        summarize it clearly and concisely to ensure easy understanding but make sure everything is sent to the user.
                    - role: The value of {agents['manager_agent'].role}
                """
            ),
            output_json=managerOutput,
            context=[
                self.task_matching_task,
                self.initial_human_input_task,
                self.validator_task,
            ],
            agent=agents["manager_agent"],
        )

