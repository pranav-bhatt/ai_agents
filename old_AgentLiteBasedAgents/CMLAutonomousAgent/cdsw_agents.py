from typing import List
import json

from cdsw_actions import AskUser, CDSWApiCaller

from agentlite.actions import BaseAction, FinishAct, ThinkAct
from agentlite.actions.InnerActions import INNER_ACT_KEY
from agentlite.agents import ABCAgent, BaseAgent
from agentlite.commons import AgentAct, TaskPackage
from agentlite.llm.agent_llms import BaseLLM, get_llm_backend
from agentlite.llm.LLMConfig import LLMConfig
from agentlite.logging.terminal_logger import AgentLogger

# set PROMPT_DEBUG_FLAG to True to see the debug info
agent_logger = AgentLogger(PROMPT_DEBUG_FLAG=False)


class SearchAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        role: str,
        llm: BaseLLM,
        actions: List[BaseAction] = [AskUser()],
        manager: ABCAgent = None,
        **kwargs
    ):
        super().__init__(
            name=name, role=role, llm=llm, actions=actions, manager=manager, **kwargs
        )


class CDSWProjectAgent(BaseAgent):
    def __init__(
        self,
        llm: BaseLLM,
        actions: List[BaseAction] = [AskUser(), CDSWApiCaller()],
        **kwargs
    ):
        name = "cdsw_project_agent"
        role = "You can perform actions related to CDSW projects by invoking endpoints."
        super().__init__(
            name=name, role=role, llm=llm, actions=actions, logger=agent_logger
        )
        self.__build_examples__()

    def __build_examples__(self):
        """
        constructing the examples for agent working.
        Each example is a successful action-obs chain of an agent.
        those examples should cover all those api calls
        """
        # set the external context for the manager using the manager metadata
        agent_external_context = json.dumps(
            json.load(open("CMLAutonomousAgent/cdsw_api_spec/poc_project_create.json")),
            separators=(",", ":"),
        )

        # an example of search agent with wikipedia api call
        # task
        task = "create a new project"
        task_pack = TaskPackage(
            instruction=task, external_context=agent_external_context
        )

        # 1. think action and obs
        thought = "Based on the context I have, the relevant endpoint that will help me create a project is the POST HTTP method for the '/api/v2/projects' endpoint. This call requires a JSON payload with required parameter name, and other optional parameter like description, visibility, parent_project, git_url, "
        act_1 = AgentAct(name=ThinkAct.action_name, params={INNER_ACT_KEY: thought})
        obs_1 = ""

        # 2. user clarification action and obs
        act_params = {
            "query": "Could you please provide me with more details for the required and optional parameters for creating a CDSW project via the POST /api/v2/projects API endpoint? I require the project name, description, and template, but the other fields you can provide me are [Populate required and optional fields from the spec here]."
        }
        act_2 = AgentAct(name=AskUser().action_name, params=act_params)
        obs_2 = """The project should be called 'test_project', and the description can be 'Test project for API testing'. The visibility can be 'Private', and leave the other fields empty for now."""

        # 3. think action and obs
        thought = "I find that I should create a project called 'test_project' with the description 'Test project for API testing' and visibility of 'Private'. I now have the required information to make the JSON payload."
        act_3 = AgentAct(name=ThinkAct.action_name, params={INNER_ACT_KEY: thought})
        obs_3 = ""

        # 4. api call action and obs
        act_params = {
            "payload": {
                "url": "/api/v2/projects",
                "method": "POST",
                "parameters": {
                    "name": "test_project",
                    "description": "Test project for API testing",
                    "visibility": "Private",
                },
            }
        }
        act_4 = AgentAct(name=CDSWApiCaller().action_name, params=act_params)
        obs_4 = """The API call was successful. The response was:
        {
            "id": 123,
            "name": "test_project",
            "description": "Test project for API testing",
            "visibility": "Private"
        }"""

        # 5. think action and obs
        thought = "I find that the API call was successful in creating the project with the details provided. The task of creating a new project with the POST /api/v2/projects API call is now complete."
        act_5 = AgentAct(name=ThinkAct.action_name, params={INNER_ACT_KEY: thought})
        obs_5 = ""

        # 6. finish action
        result = "Task completed successfully."
        act_6 = AgentAct(name=FinishAct.action_name, params={INNER_ACT_KEY: result})
        obs_6 = "Task Completed."

        act_obs = [
            (act_1, obs_1),
            (act_2, obs_2),
            (act_3, obs_3),
            (act_4, obs_4),
            (act_5, obs_5),
            (act_6, obs_6),
        ]
        self.add_example(task=task_pack, action_chain=act_obs)
