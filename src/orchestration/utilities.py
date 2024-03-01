"""
This module contains the OrchestrationClient class for 
orchestrating various operations related to AI search and chat.

Classes:
    OrchestrationClient: A client class for orchestrating various 
    operations related to AI search and chat.
"""

import requests
from azure.identity import DefaultAzureCredential


class OrchestrationClient:
    """
    A client class for orchestrating various operations related to AI search and chat.

    Args:
        open_ai_endpoint (str): The endpoint URL for the OpenAI service.
        open_ai_chat_deployment (str): The deployment ID for the OpenAI chat service.
        open_ai_embedding_deployment (str): The deployment ID for the OpenAI embedding service.
        search_endpoint (str): The endpoint URL for the Azure AI Search service.
        search_index_name (str): The name of the search index to be used.
        open_ai_api_version (str, optional): The version of the OpenAI API.
        search_api_version (str, optional): The version of the Azure AI Search API.

    Attributes:
        open_ai_endpoint (str): The endpoint URL for the OpenAI service.
        open_ai_chat_deployment (str): The deployment ID for the OpenAI chat service.
        open_ai_embedding_deployment (str): The deployment ID for the OpenAI embedding service.
        search_endpoint (str): The endpoint URL for the Azure AI Search service.
        search_index_name (str): The name of the search index to be used.
        open_ai_api_version (str): The version of the OpenAI API.
        search_api_version (str): The version of the Azure AI Search API.
        credential (DefaultAzureCredential): The credential object for authentication.
        chat_endpoint (str): The endpoint URL for the OpenAI chat service.
        embedding_endpoint (str): The endpoint URL for the OpenAI embedding service.
        search_endpoint (str): The endpoint URL for the Azure AI Search service.
        search_query_system_message (str): The system message for search query generation.
        chat_response_system_message (str): The system message for chat response generation.
    """

    def __init__(
        self,
        open_ai_endpoint: str,
        open_ai_chat_deployment: str,
        open_ai_embedding_deployment: str,
        search_endpoint: str,
        search_index_name: str,
        open_ai_api_version="2023-09-01-preview",
        search_api_version="2023-11-01",
    ):
        self.open_ai_endpoint = open_ai_endpoint
        self.open_ai_chat_deployment = open_ai_chat_deployment
        self.open_ai_embedding_deployment = open_ai_embedding_deployment
        self.search_endpoint = search_endpoint
        self.search_index_name = search_index_name
        self.open_ai_api_version = open_ai_api_version
        self.search_api_version = search_api_version

        self.credential = DefaultAzureCredential()

        self.chat_endpoint = f"{self.open_ai_endpoint}/openai/deployments/{self.open_ai_chat_deployment}/chat/completions?api-version={self.open_ai_api_version}"
        self.embedding_endpoint = f"{self.open_ai_endpoint}/openai/deployments/{self.open_ai_embedding_deployment}/embeddings?api-version={self.open_ai_api_version}"
        self.search_endpoint = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/search?api-version={self.search_api_version}"

        self.search_query_system_message = """
            You are a bot that translates user queries into an effective search query for Azure AI Search.
            Ensure the user's intent is captured by including relevant keywords or phrases from their query. 
            Ensure you ownly return the search query and nothing else in your response.
        """

        self.chat_response_system_message = """
            You are an customer service bot designed to answer questions on products.
            Keep your answers short and to the point. Try to use dot points as much as possible.
            Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. 
            Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
            For tabular information return it as an html table. Do not return markdown format. 
            If the question is not in English, answer in the language used in the question.
            Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. 
            Use square brackets to reference the source, for example [info1.txt]. Don't combine sources, list each source separately, for example [info1.txt][info2.pdf].
        """

    def get_request_headers(self, token: str) -> dict[str, str]:
        """
        This method is used to get the request headers.

        Parameters:
        self (object): An instance of the class that this method belongs to.
        token (str): The access token for authentication.

        Returns:
        dict: A dictionary containing the request headers.
        """

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def generate_search_query(self, user_input: str) -> str:
        """
        Generates a search query based on the provided keywords and filters.

        Parameters:
        user_input (str): The user input to be used for generating the search query.

        Returns:
        search_query (str): The search query.
        """
        try:
            access_token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )

            request_headers = self.get_request_headers(access_token.token)

            request_payload = {
                "messages": [
                    {"role": "system", "content": self.search_query_system_message},
                    {"role": "user", "content": user_input},
                ],
            }

            response = requests.post(
                self.chat_endpoint,
                headers=request_headers,
                json=request_payload,
                timeout=120,
            )

            response.raise_for_status()  # Raise an exception for non-2xx status codes

            response_payload = response.json()

            search_query = response_payload["choices"][0]["message"]["content"]

            return search_query

        except requests.exceptions.RequestException as e:
            print(f"Error generating search query: {e}")

    def get_embedding(self, search_query: str) -> list[float]:
        """
        Generates an embedding for the provided search query.

        Parameters:
            search_query (str): The search query to be used for generating the embedding.

        Returns:
            embedding (list[float]): The vector embedding.
        """
        try:
            access_token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )

            request_headers = self.get_request_headers(access_token.token)

            request_payload = {"input": search_query}

            response = requests.post(
                self.embedding_endpoint,
                headers=request_headers,
                json=request_payload,
                timeout=120,
            )

            response.raise_for_status()  # Raise an exception for non-2xx status codes

            response_payload = response.json()

            embedding = response_payload["data"][0]["embedding"]

            return embedding

        except requests.exceptions.RequestException as e:
            print(f"Error generating embedding: {e}")

    def get_documents(
        self,
        search_query: str,
        search_query_vector_embedding: list[float],
        number_of_documents: str = "5",
        selected_fields: str = "*",
    ) -> list[any]:
        """
        Gets the documents based on the provided search query and vector embedding.

        Parameters:
            search_query (str): The search query to be used for getting the documents.
            search_query_vector_embedding (list[float]): The vector embedding for the search query.
            number_of_documents (str, optional): The number of documents to return. Defaults to "5".
            selected_fields (str, optional): The fields to be selected. Defaults to "*".

        Returns:
            search_documents (list[any]): The list of documents.
        """
        try:
            access_token = self.credential.get_token(
                "https://search.azure.com/.default"
            )

            request_headers = self.get_request_headers(access_token.token)

            request_payload = {
                "search": search_query,
                "select": selected_fields,
                "queryType": "semantic",
                "semanticConfiguration": f"{self.search_index_name}-semantic-configuration",
                "captions": "extractive",
                "answers": "extractive",
                "top": number_of_documents,
                "vectorQueries": [
                    {
                        "kind": "vector",
                        "k": 50,
                        "fields": "vector",
                        "vector": search_query_vector_embedding,
                    }
                ],
            }

            response = requests.post(
                self.search_endpoint,
                headers=request_headers,
                json=request_payload,
                timeout=60,
            )

            response.raise_for_status()  # Raise an exception for non-2xx status codes

            response_payload = response.json()

            search_documents = response_payload["value"]

            return search_documents

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving documents: {e}")
            return False

    def generate_user_prompt(self, user_input: str, search_results: list[any]) -> str:
        """
        Generates a user prompt based on the user input and search results.

        Parameters:
            user_input (str): The user input to be used for generating the user prompt.
            search_results (list[any]): The search results to be used for generating the user prompt.

        Returns:
            str: The user prompt.
        """
        sources = ""

        for doc in search_results:
            chunk = doc["chunk"].replace("\n", " ").replace("*", "").replace("#", "")
            sources += f"{doc['title']}:{doc['path']}:{chunk}\n"

        return f"""{user_input}\n\nSources:\n{sources}"""

    def generate_assistant_response(
        self, message_history: dict["messages" : list[any]]
    ) -> str:
        """
        Generates an assistant response based on the provided user prompt.

        Args:
            user_prompt (str): The user prompt to be used for generating the assistant response.

        Returns:
            assistant_message (str): The assistant response.
        """
        try:
            access_token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )

            request_headers = self.get_request_headers(access_token.token)

            message_history_filtered = [
                {k: v for k, v in d.items() if k in ("role", "content")}
                for d in message_history["messages"]
            ]

            request_payload = {
                "messages": [
                    {"role": "system", "content": self.chat_response_system_message}
                ]
                + message_history_filtered,
            }

            response = requests.post(
                self.chat_endpoint,
                headers=request_headers,
                json=request_payload,
                timeout=120,
            )

            response.raise_for_status()  # Raise an exception for non-2xx status codes

            response_payload = response.json()

            assistant_message = response_payload["choices"][0]["message"]["content"]

            return assistant_message

        except requests.exceptions.RequestException as e:
            print(f"Error generating assistant message: {e}")
            return False

    def generate_chat_response(
        self, message_history: dict["messages" : list[any]]
    ) -> str:
        """
        Generates a chat response based on the provided user input.

        Parameters:
            user_input (str): The user input to be used for generating the chat response.

        Returns:
            message_history (dict["messages" : list[any]]): The message history including the assistant response.
        """
        try:
            latest_user_input = message_history["messages"][-1]["content"]

            search_query = self.generate_search_query(latest_user_input)

            search_query_vector_embedding = self.get_embedding(search_query)

            search_documents = self.get_documents(
                search_query,
                search_query_vector_embedding,
                selected_fields="title,path,chunk",
            )

            search_documents_filtered = [
                {k: v for k, v in d.items() if k in ("title", "path")}
                for d in search_documents
            ]

            updated_user_prompt = self.generate_user_prompt(
                latest_user_input, search_documents
            )

            message_history["messages"].pop()
            message_history["messages"].append(
                {
                    "role": "user",
                    "content": updated_user_prompt,
                    "references": search_documents_filtered,
                }
            )

            assistant_message = self.generate_assistant_response(message_history)

            message_history["messages"].append(
                {"role": "assistant", "content": assistant_message}
            )

            return message_history

        except requests.exceptions.RequestException as e:
            print(f"Error generating chat response: {e}")
            return message_history
