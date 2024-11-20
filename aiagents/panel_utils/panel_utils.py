import json
import re
import time
from typing import Optional, Any, Union, List
from json import dumps
from re import search
from os import environ

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import panel as pn

from aiagents.config import configuration
from aiagents.panel_utils.panel_stylesheets import card_stylesheet

avatars = {}


def output_formatter(output: str) -> dict:
    human_prompt = f"""
    As a good observer, find and fetch me the value of "role" from:
    {output}
    Have no prefix or suffix, just return the value, don't act extra smart. 
    Don't panic or think too much if you can't find it, just return an empty string ("").
    There are only these many roles possible: 
        1. "Human Input Agent"
        2. "API Selector Agent"
        3. "Decision Validator Agent"
        4. "API Caller Agent"
        5. "Task Matcher"
    So don't try to generate whimsical roles on your own, just send empty string when in doubt
    """
    llm = AzureChatOpenAI(azure_deployment=environ.get(
        "AZURE_OPENAI_DEPLOYMENT", "cml"
    )) if configuration.openai_provider == "AZURE_OPENAI" else ChatOpenAI()
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

    # def on_agent_action(self, action: AgentAction, *args, **kwargs: Any) -> Any:
    #     self.chat_interface.send(
    #         f"Agent action: {action.log}",
    #         respond=False,
    #     )
    #     return super().on_agent_action(action, *args, **kwargs)

    # def on_agent_finish(self, finish: AgentFinish, *args, **kwargs: Any) -> Any:
    #     self.chat_interface.send(
    #         f"Agent finish: {finish.log}",
    #         respond=False,
    #     )
    #     return super().on_agent_finish(finish, *args, **kwargs)

    # def on_tool_start(
    #     self, serialized: dict[str, Any], input_str: str, *args, **kwargs
    # ):
    #     self.chat_interface.send(
    #         f"started tool: {serialized['name']}, other details: {serialized}, input str: {input_str}",
    #         respond=False,
    #     )
    #     self._update_active(DEFAULT_AVATARS["tool"], serialized["name"])
    #     self._stream(f"Tool input: {input_str}")
    #     return super().on_tool_start(serialized, input_str, *args, **kwargs)

    # def on_tool_end(self, output: str, *args, **kwargs):
    #     self.chat_interface.send(
    #         f"Tool output: {output}",
    #         respond=False,
    #     )
    #     self._stream(output)
    #     self._reset_active()
    #     return super().on_tool_end(output, *args, **kwargs)

    # def on_tool_error(
    #     self, error: Union[Exception, KeyboardInterrupt], *args, **kwargs
    # ):
    #     return super().on_tool_error(error, *args, **kwargs)

    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], *args, **kwargs
    ):
        user = serialized["repr"].split("role=")[1].split(",")[0]
        self.agent_name = user
        configuration.active_diagram.value = (
            f"{configuration.diagram_path}/{configuration.diagrams[user]}"
        )

        self.send_event(
            "Task to be completed",
            inputs["input"],
            user,
        )
        configuration.reload_button.disabled = False

    def on_chain_end(self, outputs: dict[str, Any], *args, **kwargs):
        print(dumps(outputs, indent=2))
        role = output_formatter(outputs["output"])
        print("role:", role)
        if role and "Agent" in role:
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
                user="System", respond=False
            )
        else:
            self.send_event(
                "Task outcome",
                outputs["output"],
                self.agent_name,
            )
        if "reload the crew" in outputs["output"].lower():
            configuration.spinner.value=False
            configuration.spinner.visible=False
            self.chat_interface.send(
                pn.pane.Markdown(
                    object="If you have any other queries or need further assistance, please Reload the Crew.",
                    styles=configuration.chat_styles
                ),
                user=self.agent_name, respond=False
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
            "font-size": "1.2em",
            "border-radius": "0.7rem",
            "overflow-y": "scroll",
            "max-height": "20em",
            "margin": "0.7rem",
            "display":"block",
        }
        markdown_input = pn.pane.Markdown(
            object=message,
        )
        markdown_input.styles = custom_style
        color = {
            "Human Input Agent": "#e2fcfd",
            "API Selector Agent": "#fef6db",
            "Decision Validator Agent": "#fbe7dd",
            "API Caller Agent": "#ffe5f1",
            "Task Matcher": "#e6f3fd",
            "Swagger API Description Summarizer": "#f3f9cf",
            "swagger_splitter": "#eedaff",
        }
        card = pn.Card(
            markdown_input,
            title=step_name,
            collapsed=True,
            header=f"""<html>
                        <h4 style='
                            margin:0.25rem;
                            font-size:1.2em;
                            font-weight:500;
                            color: #111;
                        '>{step_name}</h4>
                    </html>""",
            active_header_background=color[user],
            header_background=color[user],
            styles={
                "border-bottom": "0.1rem solid #c0caca",
                "border-radius": "0.25rem !important",
            },
            stylesheets=[card_stylesheet]
        )
        configuration.spinner.value = False
        configuration.spinner.visible = False
        self.chat_interface.send(
            card,
            user=user,
            respond=False,
            avatar=f"{configuration.avatar_images[user]}",
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
        configuration.metadata_summarization_status.value = (
            "Processing the API Spec file ⏱" 
        )
        

    def on_chain_end(self, outputs: dict[str, Any], *args, **kwargs):
        print(dumps(outputs, indent=2))
        print(self.agent_name)