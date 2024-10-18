from pprint import pprint

def custom_callback(formatted_answer):
    pprint(f"The callback received from the agent is {formatted_answer}")