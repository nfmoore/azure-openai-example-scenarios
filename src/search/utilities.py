"""
This module contains the AISearchClient class which is used for 
interacting with the AI Search service.

Classes:
    AISearchClient: A client for interacting with the AI Search service.
"""

import json
import uuid

import requests
from azure.identity import DefaultAzureCredential
from jinja2 import Template


class AISearchClient:
    """A client for interacting with the AI Search service.

    This class provides methods for loading templates, checking if resources exist,
    and creating resources in the AI Search service.

    Attributes:
        search_endpoint (str): The endpoint of the AI Search service.
        api_key (str): The API key for the AI Search service.
        api_version (str): The version of the AI Search service API.
        headers (dict): The headers to use when making requests to the AI Search service.
        data_source_name (str): The name of the data source.
        index_name (str): The name of the index.
        indexer_name (str): The name of the indexer.
        skillset_name (str): The name of the skillset.
        data_source_payload (dict): The payload for creating the data source.
        index_payload (dict): The payload for creating the index.
        skillset_payload (dict): The payload for creating the skillset.
        indexer_payload (dict): The payload for creating the indexer.
    """

    def __init__(
        self,
        search_endpoint: str,
        api_version="2023-10-01-Preview",
    ):
        self.search_endpoint: str = search_endpoint
        self.api_version: str = api_version

        self.data_source_name = None
        self.index_name = None
        self.indexer_name = None
        self.skillset_name = None

        self.data_source_payload = None
        self.index_payload = None
        self.skillset_payload = None
        self.indexer_payload = None

        credential = DefaultAzureCredential()
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
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())
        rendered_json = template.render(**kwargs)
        return json.loads(rendered_json)

    def load_data_source_template(
        self,
        data_source_name: str,
        data_source_template_path: str,
        template_variables: dict,
    ) -> None:
        """Load a data source template.

        Args:
            data_source_name (str): The name of the data source.
            data_source_template_path (str): The path to the data source template file.
            template_variables (dict): The variables to be used in the template.
        """
        self.data_source_name = data_source_name
        self.data_source_payload = self.format_template(
            data_source_template_path, **template_variables
        )

    def load_index_template(
        self, index_name: str, index_template_path: str, template_variables: dict
    ) -> None:
        """Load an index template.

        Args:
            index_name (str): The name of the index.
            index_template_path (str): The path to the index template file.
            template_variables (dict): The variables to be used in the template.
        """
        self.index_name = index_name
        self.index_payload = self.format_template(
            index_template_path, **template_variables
        )

    def load_skillset_template(
        self, skillset_name: str, skillset_template_path: str, template_variables: dict
    ) -> None:
        """Load a skillset template.

        This method is used to load a skillset template with the provided variables.

        Args:
            skillset_name (str): The name of the skillset.
            skillset_template_path (str): The path to the skillset template file.
            template_variables (dict): The variables to be used in the template.
        """
        self.skillset_name = skillset_name
        self.skillset_payload = self.format_template(
            skillset_template_path, **template_variables
        )

    def load_indexer_template(
        self, indexer_name: str, indexer_template_path: str, template_variables: dict
    ) -> None:
        """Load an indexer template.

        This method is used to load an indexer template with the provided variables.

        Args:
            indexer_name (str): The name of the indexer.
            indexer_template_path (str): The path to the indexer template file.
            template_variables (dict): The variables to be used in the template.
        """
        self.indexer_name = indexer_name
        self.indexer_payload = self.format_template(
            indexer_template_path, **template_variables
        )

    def check_data_source_exists(self) -> bool:
        """Check if a data source exists.

        This method is used to check if a data source already exists in the AI Search service.

        Returns:
            bool: True if the data source exists, False otherwise.
        """
        response = requests.get(
            f"{self.search_endpoint}/datasources('{self.data_source_name}')?api-version={self.api_version}",
            headers=self.headers,
            timeout=10,
        )
        return response.status_code == 200

    def check_index_exists(self) -> bool:
        """Check if an index exists.

        This method is used to check if an index already exists in the AI Search service.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        response = requests.get(
            f"{self.search_endpoint}/indexes('{self.index_name}')?api-version={self.api_version}",
            headers=self.headers,
            timeout=10,
        )
        return response.status_code == 200

    def check_skillset_exists(self) -> bool:
        """Check if an skillset exists.

        This method is used to check if an skillset already exists in the AI Search service.

        Returns:
            bool: True if the skillset exists, False otherwise.
        """
        response = requests.get(
            f"{self.search_endpoint}/skillsets('{self.skillset_name}')?api-version={self.api_version}",
            headers=self.headers,
            timeout=10,
        )
        return response.status_code == 200

    def check_indexer_exists(self) -> bool:
        """Check if an indexer exists.

        This method is used to check if an indexer already exists in the AI Search service.

        Returns:
            bool: True if the indexer exists, False otherwise.
        """
        response = requests.get(
            f"{self.search_endpoint}/indexers('{self.indexer_name}')?api-version={self.api_version}",
            headers=self.headers,
            timeout=10,
        )
        return response.status_code == 200

    def create_index(self) -> requests.Response | str:
        """Create an index.

        This method is used to create a new index in the AI Search service.

        Returns:
            Response: The response from the AI Search service.
        """
        try:
            response = requests.put(
                f"{self.search_endpoint}/indexes('{self.index_name}')?api-version={self.api_version}",
                headers=self.headers,
                json=self.index_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            print(f"Index '{self.index_name}' created successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error creating index: {e}")
            return False

    def create_data_source(self) -> requests.Response | str:
        """Create a data source.

        This method is used to create a new data source in the AI Search service.

        Returns:
            Response: The response from the AI Search service.
        """
        try:
            response = requests.put(
                f"{self.search_endpoint}/datasources('{self.data_source_name}')?api-version={self.api_version}",
                headers=self.headers,
                json=self.data_source_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            print(f"Data store '{self.data_source_name}' created successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error creating index: {e}")
            return False

    def create_skillset(self) -> requests.Response:
        """Create a skillset.

        This method is used to create a new skillset in the AI Search service.

        Returns:
            Response: The response from the AI Search service.
        """
        try:
            if not self.check_index_exists():
                raise ValueError("Index does not exist.")
            response = requests.put(
                f"{self.search_endpoint}/skillsets('{self.skillset_name}')?api-version={self.api_version}",
                headers=self.headers,
                json=self.skillset_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            print(f"Skillset '{self.skillset_name}' created successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error creating skillset: {e}")
            return False

    def create_indexer(self) -> requests.Response | str:
        """Create an indexer.

        This method is used to create a new indexer in the AI Search service.

        Returns:
            Response | str: The response from the AI Search service.
        """
        try:
            if not self.check_data_source_exists():
                raise ValueError("Data source does not exist.")
            if not self.check_index_exists():
                raise ValueError("Index does not exist.")
            if not self.check_skillset_exists():
                raise ValueError("Skillset does not exist.")
            response = requests.put(
                f"{self.search_endpoint}/indexers('{self.indexer_name}')?api-version={self.api_version}",
                headers=self.headers,
                json=self.indexer_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            print(f"Indexer '{self.indexer_name}' created successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error creating indexer: {e}")
            return False

    def run_indexer(self, reset_flag: bool = False) -> requests.Response | str:
        """Run an indexer.

        This method is used to run an existing indexer in the AI Search service.

        Returns:
            Response | str: The response from the AI Search service.
        """
        try:
            if self.check_indexer_exists():
                raise ValueError("Indexer does not exist.")
            reset_or_run = "reset" if reset_flag else "run"
            indexer_payload = {
                "x-ms-client-request-id": str(uuid.uuid4()),
            }
            response = requests.post(
                f"{self.search_endpoint}/indexers('{self.indexer_name}')/search.{reset_or_run}?api-version={self.api_version}",
                headers=self.headers,
                json=indexer_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            print(f"Indexer '{self.indexer_name}' {reset_or_run} successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error creating indexer: {e}")
            return False
