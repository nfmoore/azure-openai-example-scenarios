"""
    This module contains the main function that runs the streamlit application.
"""

import os
import re
import sys

import streamlit as st
from dotenv import load_dotenv

from rag.utilities import RetrievalAugmentedGenerationClient


def get_answer(question: str) -> str:
    """
    Create a completion using the client and message history.

    Parameters:
        client (RetrievalAugmentedGenerationClient): The rag client.
        question (str): The latest user message.

    Returns:
        formatted_answer: The response to the the user's message.
    """

    # Generate a chat response and update chat history
    message_history = st.session_state.client.get_answer(
        question=question, message_history=st.session_state.message_history
    )

    # Update message history for client
    st.session_state.message_history = message_history

    # Get the assistant message from the chat history
    formatted_answer = replace_references(
        answer=message_history[-1]["content"],
        references=message_history[-2]["references"],
    )

    return formatted_answer


def replace_references(answer: str, references: list[dict]) -> str:
    """
    Convert references in the format [*.md] to ``[*.md](path)``*.

    Parameters:
        answer (str): The text to modify.
        references (list[dict]): The list of references.

    Returns:
        answer: The modified answer.
    """
    # Generate lookup table for references
    reference_lookup = (
        {item["title"]: item["path"] for item in references} if references else {}
    )

    # Find and format all references in answer
    references = re.findall(r"\[([^\]]*.md)\]", answer)
    for reference in references:
        answer = answer.replace(
            f"[{reference}]",
            f"[``{reference}``]({reference_lookup.get(reference)})",
        )

    return answer


def main():
    """
    Main function that runs the application.

    This function initializes the Azure OpenAI client, displays system prompt,
    user input, and assistant response in a chat-like interface.

    Parameters:
        None

    Returns:
        None
    """
    # Set the title of the app
    st.title(os.getenv("AZURE_APP_TITLE"))

    # Initialize the orchestration client
    st.session_state.client = RetrievalAugmentedGenerationClient(
        open_ai_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
        open_ai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        open_ai_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        search_endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
        search_index_name=os.getenv("AZURE_AI_SEARCH_INDEX_NAME"),
        system_prompt_configuration_file="src/rag/configuration.yaml"
        or os.getenv("AZURE_APP_SYSTEM_PROMPT_CONFIGURATION_FILE"),
    )

    # Initialize messages from app session
    if "app_messages" not in st.session_state:
        st.session_state.app_messages = [
            {"role": "assistant", "content": "How may I assist you today?"}
        ]

    # Initialize message history for client
    if "message_history" not in st.session_state:
        st.session_state.message_history = []

    # Initialize a flag for create_completion running status
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    # Display messages from app session on app rerun
    for message in st.session_state.app_messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input(
        "Ask me a question", disabled=st.session_state.is_running
    ):

        # Add user message to app message history
        st.session_state.app_messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
            st.session_state.is_running = True

        st.rerun()

    # Generate a new response if last message is not from assistant
    if st.session_state.app_messages[-1]["role"] != "assistant":

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = get_answer(
                    question=st.session_state.app_messages[-1]["content"]
                )

            st.markdown(response)
            st.session_state.is_running = False

        # Add assistant response to chat history
        st.session_state.app_messages.append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), "src"))
    load_dotenv()
    main()
