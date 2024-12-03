from typing import List
import json
from dotenv import load_dotenv

from cdsw_agents import CDSWProjectAgent

from agentlite.actions import FinishAct, ThinkAct
from agentlite.actions.InnerActions import INNER_ACT_KEY
from agentlite.agents import ABCAgent, ManagerAgent
from agentlite.agents.agent_utils import AGENT_CALL_ARG_KEY
from agentlite.commons import AgentAct, TaskPackage
from agentlite.llm.agent_llms import BaseLLM, get_llm_backend
from agentlite.llm.LLMConfig import LLMConfig
from agentlite.logging.terminal_logger import AgentLogger

# set PROMPT_DEBUG_FLAG to True to see the debug info
agent_logger = AgentLogger(PROMPT_DEBUG_FLAG=False)


class CDSWManager(ManagerAgent):
    def __init__(self, llm: BaseLLM, TeamAgents: List[ABCAgent] = None, **kwargs):
        super().__init__(
            llm,
            name="CDSW_Manager",
            role="Controlling multiple Cloudera Data Science Workbench agents to invoke the requested actions.",
            TeamAgents=TeamAgents,
            logger=agent_logger,
        )


def test_manager_agent():
    # setting the llm config of manager agent
    llm_config_dict = {
        "llm_name": "llama3-70b-8192",
        "temperature": 0.3,
        "context_len": 8192,
    }
    llm_config = LLMConfig(llm_config_dict)
    llm = get_llm_backend(llm_config)

    # setting the team of manager agent
    cdsw_project_agent = CDSWProjectAgent(llm)
    team = [cdsw_project_agent]

    # initialize the manager with llm and team labor agent
    search_manager = CDSWManager(llm, TeamAgents=team)

    # set the external context for the manager using the manager metadata
    manager_external_context = json.dumps(
        json.load(open("CMLAutonomousAgent/cdsw_api_spec/manager_metadata.json")),
        separators=(",", ":"),
    )

    # adding one example to manager agent
    exp_task = "fetch me details for a project"
    exp_task_pack = TaskPackage(
        instruction=exp_task, external_context=manager_external_context
    )

    act_1 = AgentAct(
        name=ThinkAct.action_name,
        params={
            INNER_ACT_KEY: f"""Based on the information I have and the descriptions of the team agents, \
                I should ask {cdsw_project_agent.name} to handle this task. Based on the context I have, \
                the GET call for the '/api/v2/projects/{{project_id}}' endpoint has to be invoked since its description \
                which is 'Return one project.' matches the requested query 'fetch me details for a project'. The 'file' \
                field from the metadata for '/api/v2/projects/{{project_id}}' tells me that the agent has to refer to \
                'projects_project_id.json' and the query to be sent to it is the requested query 'fetch me details for a project'.\
                I will not interpret any field as a parameters and will proceed without any replacements.""",
        },
    )
    obs_1 = "OK"

    act_2 = AgentAct(
        name=cdsw_project_agent.name,
        params={
            AGENT_CALL_ARG_KEY: '{"query": "fetch me details for a project", "file":"projects_project_id.json"}'
        },
    )
    obs_2 = "Task completed successfully."

    act_3 = AgentAct(
        name=ThinkAct.action_name,
        params={INNER_ACT_KEY: "I find the task is completed successfully."},
    )
    obs_3 = ""

    act_4 = AgentAct(
        name=FinishAct.action_name,
        params={INNER_ACT_KEY: "Task completed successfully."},
    )
    obs_4 = "Task completed successfully."

    exp_act_obs = [(act_1, obs_1), (act_2, obs_2), (act_3, obs_3), (act_4, obs_4)]

    search_manager.add_example(task=exp_task_pack, action_chain=exp_act_obs)

    # run test
    test_task = input("Enter a task: ")
    test_task_pack = TaskPackage(
        instruction=test_task,
        task_creator="User",
        external_context=manager_external_context,
    )
    response = search_manager(test_task_pack)
    print(response)


if __name__ == "__main__":
    load_dotenv(dotenv_path="../.env")
    test_manager_agent()
