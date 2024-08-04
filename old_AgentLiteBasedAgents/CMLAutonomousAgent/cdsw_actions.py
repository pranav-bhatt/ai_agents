import os
import requests

from langchain_community.tools import DuckDuckGoSearchResults, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from agentlite.actions.BaseAction import BaseAction


class CDSWClient:
    def __init__(self):
        self.base_url = os.environ.get("CDSW_API_ENDPOINT", "http://localhost:8080")
        self.bearer_token = os.environ.get("CDSW_API_TOKEN")

    def make_request(self, request_info):
        url = self.base_url + request_info["url"]
        method = request_info["method"]
        parameters = request_info.get("parameters", {})

        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        print(
            "making request to: ",
            url,
            " with parameters: ",
            parameters,
            " and headers: ",
            headers,
        )

        if method.upper() == "GET":
            response = requests.get(
                url, params=parameters, headers=headers, verify=False
            )
        elif method.upper() == "POST":
            response = requests.post(
                url, json=parameters, headers=headers, verify=False
            )
        elif method.upper() == "PATCH":
            response = requests.patch(
                url, json=parameters, headers=headers, verify=False
            )
        elif method.upper() == "DELETE":
            response = requests.delete(
                url, json=parameters, headers=headers, verify=False
            )
        else:
            raise ValueError("Unsupported HTTP method")

        if response.ok:
            return response.json()
        else:
            return response._content.decode("utf-8")

    def __call__(self, payload):
        return self.make_request(payload)


class CDSWApiCaller(BaseAction):
    def __init__(self) -> None:
        action_name = "CDSW_Api_Caller"
        action_desc = "Using this API to invoke actions on CDSW."
        params_doc = {
            "payload": {
                "url": "The endpoint that needs to be invoked using the CDSW API. Be exact",
                "method": "The HTTP method to use for the request. e.g. POST, GET, DELETE etc.",
                "parameters": "key-value pairs of parameters to pass in request body or query params based on method",
            }
        }

        self.client = CDSWClient()
        super().__init__(
            action_name=action_name,
            action_desc=action_desc,
            params_doc=params_doc,
        )

    def __call__(self, payload):
        return self.client.make_request(request_info=payload)


class AskUser(BaseAction):
    def __init__(self) -> None:
        action_name = "Ask_User"
        action_desc = "Using this action to ask user for input incase some more information is required from user and isn't provided in the previous prompts."
        params_doc = {
            "query": "the prompt to ask user input for clarifying or requesting any additional details. be descriptive as to what exact parameters you need from user."
        }

        self.input = input
        super().__init__(
            action_name=action_name,
            action_desc=action_desc,
            params_doc=params_doc,
        )

    def __call__(self, query):
        print(query)
        return self.input()
