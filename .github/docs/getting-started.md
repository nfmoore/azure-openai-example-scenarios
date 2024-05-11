# Getting Started

The purpose of this section is to provide an overview of each example scenario.

## Example Scenario: Pull-Based Data Ingestion with Azure AI Search & Custom Retrieval-Augmented Generation (RAG) Implementation

### Potential Use Cases

This project serves as a valuable foundation for small-scale proof-of-concept for enterprises seeking to:

- Implement AI-powered chatbots for improved user engagement and information access.
- Leverage the power of Azure AI Search for intelligent knowledge retrieval.
- Build and deploy chatbots efficiently and seamlessly using Streamlit.

### Solution Design

The below diagram shows a high-level design for the chatbot leveraging Azure OpenAI, Azure AI Search, deployed as part of an Azure Container App.

![Solution Design](./images/solution-design.png)

The solution consists of the following services:

- **[Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/overview)**: Provides the large language model (LLM) capabilities for generating human-like responses based on user queries.
- **[Azure AI Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)**: Enables efficient retrieval of relevant information from your enterprise knowledge base or data sources.
- **[Container Registry](https://learn.microsoft.com/azure/container-registry/container-registry-intro)**: Used for storing the Docker image.
- **[Container App](https://learn.microsoft.com/azure/container-apps/containers)**: Used for exposing the container as a REST API.

The following open-source Python framework are used in this project:

- **[Streamlit](https://streamlit.io/)**: Facilitates a lightweight and user-friendly deployment experience, making the chatbot readily accessible through a web interface.

The RAG pattern implemented here utilizes Azure AI Search to retrieve the most relevant information based on the user's query. This retrieved information is then fed into the Azure OpenAI LLM, which generates a comprehensive and informative response tailored to the specific context.

> [!CAUTION]
> This solution design is intended for proof-of-concept scenarios and is not recommended for enterprise production scenarios. It is advised to review and adjust the design based on your specific requirements if you plan to use this in a production environment. This could include:
>
> - Securing the solution through network controls.
> - Upflift observability by enabling monitoring and logging for different services.
> - Defining an operational support and lifecycle management plan for the solution.
> - Implementing alerting and notification mechanisms to notify support teams of any issues (e.g. performance, budget, etc.).
>
> The Azure Well-Architected Framework provides guidance on best practices for designing, building, and maintaining cloud solutions. For more information, see the [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/what-is-well-architected-framework).

## Related Resources

- [Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [Streamlit](https://streamlit.io/)
- [Azure OpenAI Service REST API reference](https://learn.microsoft.com/azure/ai-services/openai/reference)
- [Securely use Azure OpenAI on your data](https://learn.microsoft.com/azure/ai-services/openai/how-to/use-your-data-securely)
- [Introduction to prompt engineering](https://learn.microsoft.com/azure/ai-services/openai/concepts/prompt-engineering)
- [Prompt engineering techniques](https://learn.microsoft.com/azure/ai-services/openai/concepts/advanced-prompt-engineering?pivots=programming-language-chat-completions)
