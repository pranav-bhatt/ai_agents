from pprint import pprint
from aiagents.config import configuration
import re
from aiagents.panel_utils.panel_utils import CustomPanelCallbackHandler

def custom_agent_callback(output, *args, **kwargs):
    pprint(f"The callback args are {args}")
    print(output)
    if "AgentFinish" in str(args):
        agent_match = re.search(r"return_values='([^']+)'", str(args))
        agent_name = agent_match.group(1) if agent_match else ""
        if agent_name != "Swagger API Description Summarizer":
            configuration.current_agent = agent_name

    pprint(f"The callback kwargs are {kwargs}")

def custom_callback(*args, **kwargs):
    pprint(f"The callback args are {args}")
    pprint(f"The callback kwargs are {kwargs}")
    pass
    #pprint(f"The callback received from the agent is {formatted_answer}")

def custom_initialization_callback(*args, **kwargs):
    pprint(f"The callback args are {args}")
    pprint(f"The callback kwargs are {kwargs}")
    pass
    #pprint(f"The callback received from the agent is {formatted_answer}")