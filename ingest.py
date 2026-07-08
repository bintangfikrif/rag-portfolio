import os
import glob
from dotenv import load_dotenv
from google import genai 
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()

# Initialize the modern GenAI Client
ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60.0
)
COLLECTION_NAME = "portfolio_context"

# Qdrant's safe collection creation workflow
if qdrant.collection_exists(collection_name=COLLECTION_NAME):
    print("Found existing collection. Deleting to start fresh...")
    qdrant.delete_collection(collection_name=COLLECTION_NAME)

qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
)

def get_embedding(text):
    response = ai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
    )
    # Extract the actual float array from the response object
    return response.embeddings[0].values

markdown_files = glob.glob("data/*.md")

if not markdown_files:
    print("No markdown files found in the data/ directory.")
    exit()

all_chunks = []

for file_path in markdown_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        file_chunks = [chunk.strip() for chunk in content.split("\n\n") if len(chunk.strip()) > 30]
        
        file_name = os.path.basename(file_path)
        formatted_chunks = [f"[Source: {file_name}]\n{chunk}" for chunk in file_chunks]
        all_chunks.extend(formatted_chunks)

print(f"Total chunks found across {len(markdown_files)} files: {len(all_chunks)}")

points = []
for idx, chunk in enumerate(all_chunks):
    print(f"Embedding chunk {idx+1}/{len(all_chunks)}...")
    vector = get_embedding(chunk)
    points.append(
        models.PointStruct(id=idx, vector=vector, payload={"text": chunk})
    )

qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
print("All files ingested successfully.")