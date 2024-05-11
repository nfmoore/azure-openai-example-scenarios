FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./app/requirements.txt /app/requirements.txt

COPY ./llms/custom_rag_client.py /app/llms/custom_rag_client.py
COPY ./llms/system_messages.yml /app/llms/system_messages.yml

COPY ./app/main.py /app/streamlit_app.py

ARG AZURE_APP_SYSTEM_PROMPT_CONFIGURATION_FILE=./llms/system_messages.yml
ARG AZURE_APP_TITLE="Contoso Trek Product Info"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
