# Full-Stack RAG Portfolio Agent: FastAPI & React Integration

This repository implements a Retrieval-Augmented Generation (RAG) backend that powers the interactive agent on my personal portfolio website. It connects a custom React frontend widget to an asynchronous FastAPI backend to autonomously handle context-aware professional inquiries.

## Architecture Overview

The system operates as a real-time digital proxy designed to answer questions about my experience, skills, and projects based on embedded markdown files. 

* **Vector Ingestion:** Portfolio data (`data/*.md`) is chunked and embedded into a 3072-dimensional vector space using Google's `gemini-embedding-2` model.
* **Semantic Retrieval:** User queries are vectorized and matched against the context using Qdrant.
* **Asynchronous Streaming:** The generative response is processed by `gemini-2.5-flash` and streamed back to the frontend client with low latency via Server-Sent Events (SSE).
* **Cloud Infrastructure:** Hosted on Hugging Face Spaces. The platform provisions a Linux environment to build the containerized application, running the Uvicorn ASGI server continuously and exposing a secure public URL for the React widget payload.

## Tech Stack

* **FastAPI:** Core backend framework managing the asynchronous SSE streaming endpoint.
* **Qdrant:** Vector database handling the storage and retrieval of high-dimensional document embeddings.
* **Google GenAI (Gemini):** Dual-model setup handling both text embeddings and conversational response generation.
* **Hugging Face Spaces & Docker:** Cloud-based Linux environment and containerization strategy for persistent, 24/7 API availability.

## Repository Structure

* `main.py`: The FastAPI application containing the chat endpoint, prompt guardrails, and streaming logic.
* `ingest.py`: A utility script to parse markdown files, generate vectors, and upsert them into the Qdrant cluster.
* `data/`: Directory containing the source context files (resume, projects, skills, social).
* `Dockerfile`: Container configuration using `python:3.12-slim`.
* `requirements.txt`: Python dependencies.

## Local Setup & Development

### 1. Environment Variables
Create a `.env` file in the root directory and add the following keys:
```env
GOOGLE_API_KEY="your_google_gemini_api_key"
QDRANT_URL="your_qdrant_cluster_url"
QDRANT_API_KEY="your_qdrant_api_key"
```

### 2. Standard Installation (Virtual Environment)
Ensure you have Python 3.12+ installed.
```Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ingesting Data
Before starting the server, populate your Qdrant cluster with the portfolio context.
```Bash
python ingest.py
```

### 4. Running the Server
Start the ASGI server using Uvicorn.
```Bash
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
``` 

## Huggingface Spaces Deployment
This application is designed for zero-downtime deployment on Hugging Face Spaces utilizing the Docker runtime.

1. Container Build: The Space automatically reads the Dockerfile, pulls the lightweight Python image, and installs all required dependencies.

2. Continuous Execution: The cloud Linux server runs the FastAPI script 24/7, maintaining a persistent connection for incoming traffic.

3. Secure Routing: Hugging Face provisions a secure public endpoint (https://<your-space-name>.hf.space). Your frontend React widget routes its POST requests directly to this URL to initiate the SSE stream.

You must configure your repository secrets (GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY) within the Hugging Face Spaces settings interface before initiating the build.