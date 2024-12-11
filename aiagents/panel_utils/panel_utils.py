import json
import re
import time
from typing import Optional, Any, Union, List
from json import dumps
from re import search
from os import environ
from bokeh.server.contexts import BokehSessionContext
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import panel as pn
from aiagents.custom_threading import threads
from aiagents.config import configuration
from aiagents.panel_utils.panel_stylesheets import card_stylesheet, chat_stylesheet

avatars = {}


def output_formatter(output: str) -> dict:
    human_prompt = f"""
        As a good observer, find and fetch me the value of "role" parameter from:
        {output}
        Have no prefix or suffix, just return the value, don't act extra smart.
        Your instructions are very clear and straight forward. The text you see is the output returned 
        by one of the agents whose roles are defined below.
        There are only these many roles possible, you must return a value from this list:
            1. "Human Input Agent" (takes input from user)
            2. "API Selector Agent" (makes the API call using the selected API endpoint and returns the response)
            3. "Decision Validator Agent" (validates and provides feedback on the selection of API endpoint, returns the selection)
            4. "Input Matcher" (matches the user input to the correct API Spec file)
            5. "None" (none of the above agent's description matched)
        Here, the 5th role is the fallback role, such that if no role is mentioned, it means that
        role 5 must be returned. So don't try to generate whimsical roles on your own, when in doubt.
        Also, don't just randomly select a role from above. Read the text very thoroughly
    """
    llm = AzureChatOpenAI(azure_deployment=environ.get(
        "AZURE_OPENAI_DEPLOYMENT", "cml"
    ), temperature=0.6) if configuration.openai_provider == "AZURE_OPENAI" else ChatOpenAI()
    message = HumanMessage(content=human_prompt)
    response = llm(messages=[message]).content
    return response

class CustomPanelCallbackHandler(pn.chat.langchain.PanelCallbackHandler):
    """Callback Handler that prints to std out."""

    def __init__(
        self,
        chat_interface: pn.chat.ChatInterface,
    ) -> None:
        """Initialize callback handler."""
        super().__init__(chat_interface)
        self.chat_interface: pn.chat.ChatInterface = chat_interface
        self.agent_name: Optional[str] = None

    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], *args, **kwargs
    ):
        user = serialized["repr"].split("role=")[1].split(",")[0]
        self.agent_name = user
        configuration.active_diagram.value = (
            f"{configuration.diagram_path}/{configuration.diagrams[user]}"
        )

        self.send_event(
            "Started Task",
            re.sub(r'\bswagger\b', 'API Specification', inputs["input"], flags=re.IGNORECASE),
            user,
        )
        configuration.reload_button.disabled = False

    def on_chain_end(self, outputs: dict[str, Any], *args, **kwargs):
        print(dumps(outputs, indent=2))
        role = re.sub(r"[^a-zA-Z\s]", "", output_formatter(outputs["output"])).strip()
        possible_roles = [
            "Human Input Agent",
            "API Selector Agent",
            "Decision Validator Agent",
            "Input Matcher",
        ]
        if role in possible_roles:
            self.agent_name = role
        if "this output contains the appropriate swagger metadata file to use for the task at hand" in outputs["output"].lower():
            configuration.selected_swagger_file = search(
                r'"file_name":\s*"([^"]+)"', outputs["output"]
            ).group(1).replace("_metadata", "")
            print(configuration.selected_swagger_file)
        if "iteration limit" in outputs["output"] or "time limit" in outputs["output"]:
            message = outputs["output"] + "😵‍💫 Retrying..."
            self.chat_interface.send(
                pn.pane.Alert(message, alert_type='warning', styles=configuration.chat_styles), 
                user="System", respond=False,
                avatar=pn.pane.Image(f"{configuration.diagram_path}/system.svg", styles={"margin-top": "1rem", "padding": "1.5rem"})
            )
        else:
            self.send_event(
                "Ended Task",
                outputs["output"],
                self.agent_name,
            )
        configuration.reload_button.disabled = False

    def send_event(
        self,
        step_name: str,
        message: str,
        user: Optional[str] = None,
    ) -> pn.Card:
        custom_style = {
            "background": "#f9f9f9",
            "border": "1px solid black",
            "padding": "10px",
            "box-shadow": "5px 5px 5px #bcbcbc",
            "font-size": "0.85rem",
            "border-radius": "0.7rem",
            "overflow-y": "scroll",
            "max-height": "20em",
            "margin": "0.7rem",
            "display":"block",
            "width":"100%",
        }
        markdown_input = pn.pane.Markdown(
            object=message,
        )
        markdown_input.styles = custom_style
        color = {
            "Human Input Agent": "#9eebee",
            "API Selector Agent": "#fde492",
            "Decision Validator Agent": "#ffc07f",
            "Input Matcher": "#9fd1f8",
        }
        card = pn.Card(
            markdown_input,
            title=step_name,
            collapsed=True,
            header=f"""<html>
                        <h4 style='
                            margin:0.25rem;
                            font-size:0.86rem;
                            font-weight:500;
                            color: #111;
                        '>{step_name}</h4>
                    </html>""",
            active_header_background=color.get(user, "#ffe5f1"),
            header_background=color.get(user, "#ffe5f1"),
            styles={
                "border": "0.01rem solid #8b9d9d",
                "border-bottom": "0.1rem solid #346d6d",
                "border-radius": "0.25rem !important",
                "background-color": "#f6fafa",
            },
            stylesheets=[card_stylesheet]
        )
        configuration.spinner.value = False
        configuration.spinner.visible = False
        self.chat_interface.send(
            card,
            user=user,
            respond=False,
            avatar=pn.pane.Image(f"{configuration.avatar_images[user]}", styles={"margin-top": "1rem", "padding": "1.5rem"}),
        )
        time.sleep(1)
        configuration.spinner.value = True
        configuration.spinner.visible = True


class CustomPanelSidebarHandler(pn.chat.langchain.PanelCallbackHandler):
    def __init__(
        self,
        chat_interface: pn.chat.ChatInterface,
    ) -> None:
        """Initialize callback handler."""
        super().__init__(chat_interface)
        self.chat_interface: pn.chat.ChatInterface = chat_interface
        self.agent_name: Optional[str] = None

    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], *args, **kwargs
    ):
        user = serialized["repr"].split("role=")[1].split(",")[0]
        self.agent_name = user
        # configuration.metadata_summarization_status.value = (
        #     "Processing the API Spec file ⏱" 
        # )
        

    def on_chain_end(self, outputs: dict[str, Any], *args, **kwargs):
        print(dumps(outputs, indent=2))
        print(self.agent_name)

