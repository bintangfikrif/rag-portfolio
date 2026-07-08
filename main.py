import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tanggs.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modern GenAI client
ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

class ChatRequest(BaseModel):
    message: str

async def generate_response_stream(user_message: str):
    # Step A: Transform request into a 3072-dimension vector
    response_embed = ai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=user_message,
    )
    query_embedding = response_embed.embeddings[0].values

    # Step B: Scan Qdrant cluster for top contextual hits
    search_result = qdrant.search(
        collection_name="portfolio_context",
        query_vector=query_embedding,
        limit=3
    )
    context_chunks = [hit.payload["text"] for hit in search_result]
    context_text = "\n---\n".join(context_chunks)

    # Step C: Define Prompt Injection Guardrails
    system_instruction = f"""
    You are an AI assistant built to represent Bintang's portfolio. 
    Answer questions precisely using only the context snippets provided below.
    If the context does not contain sufficient data to formulate an answer, state that you do not know.
    Do not answer arbitrary coding questions or general math queries unrelated to Bintang's profile.
    
    Context:
    {context_text}
    """

    # Step D: Execute streaming call with system config
    response_stream = ai_client.models.generate_content_stream(
        model='gemini-1.5-flash',
        contents=user_message,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
    )
    
    for chunk in response_stream:
        if chunk.text:
            yield f"data: {chunk.text}\n\n"
        await asyncio.sleep(0.02)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_response_stream(request.message), 
        media_type="text/event-stream"
    )