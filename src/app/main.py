"""
    This module contains the main function that runs the streamlit application.
"""

import os
import re
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "src"))

from orchestration.utilities import OrchestrationClient


def create_completion(client: OrchestrationClient, chat_history: dict):
    """
    Create a completion using the client and messages.

    Parameters:
        client (OrchestrationClient): The orchestration client client.
        messages (list): The list of messages.

    Returns:
        chat_history: The chat history.
    """

    # Generate a chat response and update chat history
    chat_history = client.generate_chat_response(chat_history)
    st.session_state.chat_history = chat_history

    # Get the assistant message from the chat history
    assistant_message = chat_history["messages"][-1]["content"]

    return assistant_message


def replace_references(text: str, sources: list[dict]) -> str:
    """
    Convert references in the format [*.md] to ``[*.md](path)``*.

    Parameters:
        text (str): The text to modify.

    Returns:
        modified_text: The modified text.
    """
    try:
        # Regex to match references in the format [*.md]
        regex = r"\[([^\]]*.md)\]"

        if sources:
            # Find matched references
            references = re.findall(regex, text)

            # Replace matched references with modified references
            for reference in references:
                # Get the source path for the reference
                source = list(filter(lambda x: x["title"] == reference, sources))[
                    0
                ].get("path")

                if source:
                    modified_text = text.replace(
                        f"[{reference}]", f"[``{reference}``]({source})"
                    )
                else:
                    modified_text = text.replace(f"[{reference}]", f"``{reference}``")
        else:
            # Replace matched references with modified references
            modified_text = re.sub(regex, r"``\1``", text)

        return modified_text

    except Exception as e:
        print(e)
        return text


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

    st.title("Get your data talking!")

    # Initialize the orchestration client
    st.session_state.client = OrchestrationClient(
        open_ai_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
        open_ai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        open_ai_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        search_endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
        search_index_name=os.getenv("AZURE_AI_SEARCH_INDEX_NAME"),
    )

    # Initialize chat history for app session (without source documents)
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How may I assist you today?"}
        ]

    # Initialize chat history for orchastation client (with source documents)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {"messages": []}

    # Initialize a flag for create_completion running status
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input(
        "Ask me a question", disabled=st.session_state.is_running
    ):

        # Add user message to chat history
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        st.session_state.chat_history["messages"].append(user_message)

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
            st.session_state.is_running = True

        st.rerun()

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = create_completion(
                    st.session_state.client, st.session_state.chat_history
                )

                response = replace_references(
                    response,
                    st.session_state.chat_history["messages"][-2].get("references"),
                )

            st.markdown(response)
            st.session_state.is_running = False

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    load_dotenv()
    main()
