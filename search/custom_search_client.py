"""
This module contains the SearchClient class which is used for
interacting with the AI Search service.

Classes:
    CustomSearchClient: A client for interacting with the AI Search service.
"""

import json
import uuid
from typing import Literal

import requests
from azure.identity import DefaultAzureCredential
from jinja2 import Template


class CustomSearchClient:
    """A client for interacting with the AI Search service.

    This class provides methods for loading templates, checking if resources exist,
    and creating resources in the AI Search service.

    Attributes:
        search_endpoint (str): The endpoint of the AI Search service.
        api_version (str): The version of the AI Search service API.
        credential (DefaultAzureCredential): The credential object for authentication.
    """

    def __init__(
        self,
        search_endpoint: str,
        search_api_version="2024-03-01-Preview",
        credential=DefaultAzureCredential(),
    ):
        self.search_endpoint: str = search_endpoint
        self.api_version: str = search_api_version

        self.search_management_assets = {
            "indexers": {"name": None, "payload": None},
            "indexes": {"name": None, "payload": None},
            "datasources": {"name": None, "payload": None},
            "skillsets": {"name": None, "payload": None},
        }

        access_token = credential.get_token("https://search.azure.com/.default").token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

    def format_template(self, template_path: str, **kwargs):
        """Format a template with the provided variables.

        Args:
            template_path (str): The path to the template file.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: The formatted template as a dictionary.
        """
        # Load the template file
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        # Render the template with the provided variables
        rendered_json = template.render(**kwargs)
        return json.loads(rendered_json)

    def load_search_management_asset_templates(self, assets: list[dict]) -> None:
        """Load search management asset templates.

        Args:
            assets (list[dict]): A list of dictionaries containing asset information.
        """
        for asset in assets:
            asset_type = asset["type"]
            asset_name = asset["name"]
            asset_template_path = asset["template_path"]
            template_variables = asset["template_variables"]

            if asset_type not in self.search_management_assets.keys():
                raise ValueError(f"Invalid asset type: {asset_type}")

            self.search_management_assets[asset_type]["name"] = asset_name
            self.search_management_assets[asset_type]["payload"] = self.format_template(
                asset_template_path, **template_variables
            )

    def check_search_management_asset_exists(
        self,
        asset_type: Literal["indexers", "indexes", "datasources", "skillsets"],
    ) -> bool:
        """Check if an asset exists.

        This method is used to check if an asset already exists in the AI Search service.

        Returns:
            bool: True if the asset exists, False otherwise.
        """
        # Check if the search management asset exists
        asset_name = self.search_management_assets[asset_type]["name"]
        response = requests.get(
            f"{self.search_endpoint}/{asset_type}('{asset_name}')?api-version={self.api_version}",
            headers=self.headers,
            timeout=20,
        )

        return response.status_code == 200

    def create_search_management_asset(
        self,
        asset_type: Literal["indexers", "indexes", "datasources", "skillsets"],
    ) -> requests.Response:
        """Create an asset.

        This method is used to create a new asset in the AI Search service.

        Returns:
            Response: The response from the AI Search service.
        """
        # Define the asset name and payload
        asset_name = self.search_management_assets[asset_type]["name"]
        asset_payload = self.search_management_assets[asset_type]["payload"]

        # Check dependencies exist
        if asset_type in ["indexers", "skillsets"]:
            if not self.check_search_management_asset_exists("indexes"):
                raise ValueError("Index does not exist.")

        if asset_type in ["indexers"]:
            if not self.check_search_management_asset_exists("datasources"):
                raise ValueError("Data source does not exist.")
            if not self.check_search_management_asset_exists("skillsets"):
                raise ValueError("Skillset does not exist.")

        # Create the search management asset
        response = requests.put(
            f"{self.search_endpoint}/{asset_type}('{asset_name}')?api-version={self.api_version}",
            headers=self.headers,
            json=asset_payload,
            timeout=20,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response

    def run_indexer(self, reset_flag: bool = False) -> requests.Response:
        """Run an indexer.

        This method is used to run an existing indexer in the AI Search service.

        Returns:
            Response | str: The response from the AI Search service.
        """
        # Check dependencies exist
        if not self.check_search_management_asset_exists("indexers"):
            raise ValueError("Indexer does not exist.")

        # Set reset flag
        reset_or_run = "reset" if reset_flag else "run"
        indexer_payload = {
            "x-ms-client-request-id": str(uuid.uuid4()),
        }

        # Reset the indexer
        indexer_name = self.search_management_assets["indexers"]["name"]
        response = requests.post(
            f"{self.search_endpoint}/indexers('{indexer_name}')/search.{reset_or_run}?api-version={self.api_version}",
            headers=self.headers,
            json=indexer_payload,
            timeout=20,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response
