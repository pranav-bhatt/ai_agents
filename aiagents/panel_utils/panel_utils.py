import time
from typing import Optional, Any, Union, List
from json import dumps
from re import search

import panel as pn

from aiagents.config import configuration

avatars = {}


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
        print(self.agent_name)
        if "This output contains the appropriate swagger metadata file to use for the task at hand" in outputs["output"]:
            configuration.selected_swagger_file = search(
                r'"file_name":\s*"([^"]+)"', outputs["output"]
            ).group(1).replace("_metadata", "")
            print(configuration.selected_swagger_file)
        if "iteration limit" in outputs["output"] or "time limit" in outputs["output"]:
            message = outputs["output"] + "😵‍💫 Retrying..."
            self.chat_interface.send(
                pn.pane.Alert(message, alert_type='warning'), 
                user="System", respond=False
            )
        else:
            self.send_event(
                "Task outcome",
                outputs["output"],
                self.agent_name,
            )
        configuration.reload_button.disabled = False

    def send_event(
        self,
        step_name: str,
        message: str,
        user: Optional[str] = None,
    ) -> pn.Accordion:
        custom_style = {
            "background": "#f9f9f9",
            "border": "1px solid black",
            "padding": "10px",
            "box-shadow": "5px 5px 5px #bcbcbc",
            "font-size": "1.2em",
            "border-radius": "10px",
            "overflow": "scroll",
            "max-height": "20em",
            "min-width": "50vw",
        }
        markdown_input = pn.pane.Markdown(
            object=message,
        )
        markdown_input.styles = custom_style
        color = {
            "Human Input Agent": "#fbd7d1",
            "API Selector Agent": "#fdf4e2",
            "Decision Validator Agent": "#f2fce8",
            "API Caller Agent": "#e8fdf6",
            "Task Matcher": "#e8fdf6",
            "Swagger API Description Summarizer": "#fcf4bd",
            "swagger_splitter": "#f3e1fe",
        }
        accordion = pn.Accordion((step_name, markdown_input))
        accordion.active_header_background = color[user]
        accordion.header_background = color[user]
        configuration.spinner.value = False
        configuration.spinner.visible = False
        self.chat_interface.send(
            accordion,
            user=user,
            respond=False,
            avatar=f"{configuration.avatar_images[user]}",
        )
        time.sleep(1)
        configuration.spinner.value = True
        configuration.spinner.visible = True
