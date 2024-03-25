"""
This module contains the RetrievalAugmentedGenerationClient class for 
orchestrating various operations related to AI search and chat.

Classes:
    RetrievalAugmentedGenerationClient: A client class for orchestrating various 
    operations related to AI search and chat.
"""

import string

import requests
import yaml
from azure.identity import DefaultAzureCredential
from nltk.corpus import stopwords


class RetrievalAugmentedGenerationClient:
    """
    A client class for orchestrating various operations related to AI search and chat.

    Args:
        open_ai_endpoint (str): The endpoint URL for the OpenAI service.
        open_ai_chat_deployment (str): The deployment ID for the OpenAI chat service.
        open_ai_embedding_deployment (str): The deployment ID for the OpenAI embedding service.
        search_endpoint (str): The endpoint URL for the Azure AI Search service.
        search_index_name (str): The name of the search index to be used.
        system_prompt_configuration_file (str): The path to the system prompt configuration file.
        open_ai_api_version (str, optional): The version of the OpenAI API.
        search_api_version (str, optional): The version of the Azure AI Search API.
        credential (DefaultAzureCredential): The credential object for authentication.
    """

    def __init__(
        self,
        open_ai_endpoint: str,
        open_ai_chat_deployment: str,
        open_ai_embedding_deployment: str,
        search_endpoint: str,
        search_index_name: str,
        system_prompt_configuration_file: str,
        open_ai_api_version="2023-12-01-preview",
        search_api_version="2023-11-01",
        credential=DefaultAzureCredential(),
    ):
        self.open_ai_endpoint = open_ai_endpoint
        self.open_ai_chat_deployment = open_ai_chat_deployment
        self.open_ai_embedding_deployment = open_ai_embedding_deployment
        self.search_endpoint = search_endpoint
        self.search_index_name = search_index_name
        self.open_ai_api_version = open_ai_api_version
        self.search_api_version = search_api_version

        self.open_ai_access_token = credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
        self.search_access_token = credential.get_token(
            "https://search.azure.com/.default"
        ).token

        self.chat_endpoint = f"{self.open_ai_endpoint}/openai/deployments/{self.open_ai_chat_deployment}/chat/completions?api-version={self.open_ai_api_version}"
        self.embedding_endpoint = f"{self.open_ai_endpoint}/openai/deployments/{self.open_ai_embedding_deployment}/embeddings?api-version={self.open_ai_api_version}"
        self.query_search_endpoint = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/search?api-version={self.search_api_version}"

        with open(system_prompt_configuration_file, "r", encoding="utf-8") as f:
            configuration = yaml.safe_load(f)

        self.search_query_system_message = configuration.get(
            "search_query_system_message"
        )
        self.chat_response_system_message = configuration.get(
            "chat_response_system_message"
        )

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

    def retrieve_documents(
        self,
        question: str,
        number_of_documents: str = "5",
        selected_fields: str = "*",
    ) -> list[any]:
        """
        This method is used to retrieve passages from the Azure AI Search service.

        Parameters:
            self (object): An instance of the class that this method belongs to.
            question (str): The user question to be used for retrieving passages.
            number_of_documents (str, optional): The number of documents to return. Defaults to "5".
            selected_fields (str, optional): The fields to be selected. Defaults to "*".

        Returns:
            list: A list of passages retrieved from the Azure AI Search service.
        """
        # Generate search query
        response = requests.post(
            self.chat_endpoint,
            headers=self.get_request_headers(self.open_ai_access_token),
            json={
                "messages": [
                    {"role": "system", "content": self.search_query_system_message},
                    {"role": "user", "content": question},
                ],
            },
            timeout=30,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        search_query = response.json()["choices"][0]["message"]["content"]

        # Generate vector embedding for search query
        response = requests.post(
            self.embedding_endpoint,
            headers=self.get_request_headers(self.open_ai_access_token),
            json={"input": search_query},
            timeout=30,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        search_query_embedding = response.json()["data"][0]["embedding"]

        # Retrieve documents from Azure AI Search
        response = requests.post(
            self.query_search_endpoint,
            headers=self.get_request_headers(self.search_access_token),
            json={
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
                        "vector": search_query_embedding,
                    }
                ],
            },
            timeout=30,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        search_documents = response.json()["value"]

        # Filter search documents
        filtered_search_documents = [
            {"title": doc["title"], "path": doc["path"], "chunk": doc["chunk"]}
            for doc in search_documents
        ]

        return filtered_search_documents

    def augment_prompt(self, question: str, retrieved_documents: list[any]) -> str:
        """
        This method is used to augment the prompt with the retrieved documents.

        Parameters:
            self (object): An instance of the class that this method belongs to.
            question (str): The user question to be used for retrieving passages.
            retrieved_documents (list[any]): The list of retrieved documents.

        Returns:
            str: The augmented prompt with the retrieved documents.
        """

        # Function to pre-process document content - remove punctuation and stopwords
        def preprocess_text(text: str):
            text = text.lower().translate(str.maketrans("", "", string.punctuation))
            stop_words = set(stopwords.words("english"))
            text = " ".join([word for word in text.split() if word not in stop_words])
            return text

        # Generate prompt sources string
        prompt_sources = "".join(
            [
                f"{doc['title']} :: {doc['path']} :: {preprocess_text(doc['chunk'])} ||\n"
                for doc in retrieved_documents
            ]
        )

        # Embed the sources in the prompt
        augmented_prompt = f"{question}\nSources:\n{prompt_sources}"

        return augmented_prompt

    def generate_response(
        self, augmented_prompt: str, message_history: list[dict[str, any]]
    ) -> str:
        """
        Generates an assistant response based on the provided message history.

        Parameters:
            self (object): An instance of the class that this method belongs to.
            message_history (list[dict[str, any]]): The message history containing the user prompt.

        Returns:
            response (str): The assistant response.
        """
        # Filter message history
        message_history_filtered = list(
            map(
                lambda message: {
                    "role": message["role"],
                    "content": message["content"],
                },
                message_history,
            )
        )
        # Generate assistant response
        response = requests.post(
            self.chat_endpoint,
            headers=self.get_request_headers(self.open_ai_access_token),
            json={
                "messages": [
                    {"role": "system", "content": self.chat_response_system_message}
                ]
                + message_history_filtered
                + [{"role": "user", "content": augmented_prompt}],
            },
            timeout=30,
        )

        response.raise_for_status()  # Raise an exception for non-2xx status codes
        response = response.json()["choices"][0]["message"]["content"]

        return response

    def update_message_history(
        self,
        message_history: list[dict[str, any]],
        augmented_prompt: str,
        response: str,
        retrieved_documents: list[any],
    ) -> list[dict[str, any]]:
        """
        Updates the message history with the user and agent messages.

        Parameters:
            self (object): An instance of the class that this method belongs to.
            message_history (list[dict[str, any]]): The message history containing the user prompt.
            augmented_prompt (str): The user message.
            response (str): The assistant message.
            retrieved_documents (list[any]): The list of retrieved documents.

        Returns:
            updated_message_history (list[dict[str, any]]): The updated message history.
        """
        # Generate references from retrieved documents
        references = list(
            map(
                lambda doc: {"title": doc["title"], "path": doc["path"]},
                retrieved_documents,
            )
        )

        # Update message history
        user_message = {
            "role": "user",
            "content": augmented_prompt,
            "references": references,
        }
        agent_message = {"role": "assistant", "content": response}
        updated_message_history = message_history + [user_message, agent_message]

        return updated_message_history

    def get_answer(self, question: str, message_history: list[dict[str, any]]) -> str:
        """
        This method is used to get the answer to a user question.

        Parameters:
            self (object): An instance of the class that this method belongs to.
            question (str): The user question.
            message_history (list[dict[str, any]]): The message history containing the user prompt.

        Returns:
            str: The answer to the user question.
        """

        # Retrieve documents
        retrieved_documents = self.retrieve_documents(
            question, selected_fields="title,path,chunk"
        )

        # Augment prompt
        augmented_prompt = self.augment_prompt(question, retrieved_documents)

        # Generate response
        response = self.generate_response(augmented_prompt, message_history)

        # Update message history
        updated_message_history = self.update_message_history(
            message_history, augmented_prompt, response, retrieved_documents
        )

        return updated_message_history
