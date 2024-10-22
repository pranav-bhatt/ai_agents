from pprint import pprint

def custom_callback(*args, **kwargs):
    pprint(f"The callback args are {args}")
    pprint(f"The callback kwargs are {kwargs}")
    #pprint(f"The callback received from the agent is {formatted_answer}")