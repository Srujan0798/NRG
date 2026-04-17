import os
import sys
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "nrg_research"
# Using 768 to match ai4bharat/IndicBERTv2-SS
VECTOR_SIZE = 768 
MODEL_NAME = "ai4bharat/IndicBERTv2-SS"

def ingest():
    client = QdrantClient(host="localhost", port=6333)
    
    # Try to load model, fallback to 384 dim model if 768 fails
    global VECTOR_SIZE, MODEL_NAME
    try:
        model = SentenceTransformer(MODEL_NAME)
        VECTOR_SIZE = model.get_sentence_embedding_dimension()
        print(f"Loaded model {MODEL_NAME} with dimension {VECTOR_SIZE}")
    except Exception as e:
        print(f"Could not load {MODEL_NAME}: {e}. Falling back to all-MiniLM-L6-v2")
        MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
        model = SentenceTransformer(MODEL_NAME)
        VECTOR_SIZE = model.get_sentence_embedding_dimension()
        print(f"Loaded fallback model {MODEL_NAME} with dimension {VECTOR_SIZE}")

    # Recreate collection
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"Initialized collection '{COLLECTION_NAME}'")

    data_dir = Path("docs/research_papers")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some synthetic research papers
    papers = [
        {
            "id": "IITGN-2024-001",
            "text": "Autonomous robotics research in Gujarat has seen a 40% increase in funding from 2021 to 2024. IIT Gandhinagar is leading the development of swarm robotics for agricultural monitoring.",
            "metadata": {"source_id": "IITGN-2024-001", "institution": "IIT Gandhinagar", "access_tier": 1, "year": 2024, "topics": ["Robotics", "Agriculture"]}
        },
        {
            "id": "IITGN-2023-012",
            "text": "Sustainable energy initiatives at IIT campuses include solar-hydrogen hybrid systems. Research at IIT Madras and IIT Gandhinagar focuses on high-efficiency electrolytes.",
            "metadata": {"source_id": "IITGN-2023-012", "institution": "IIT Gandhinagar", "access_tier": 1, "year": 2023, "topics": ["Energy", "Sustainability"]}
        },
        {
            "id": "IITB-2022-045",
            "text": "Quantum computing research in India is supported by the National Quantum Mission. IIT Bombay researchers are exploring superconducting qubits for error-corrected quantum gates.",
            "metadata": {"source_id": "IITB-2022-045", "institution": "IIT Bombay", "access_tier": 1, "year": 2022, "topics": ["Quantum Computing", "Physics"]}
        },
        {
            "id": "GUJ-RES-2021-009",
            "text": "Funding trends in Gujarat for robotics and AI show a significant shift towards industrial automation. Over 500 crores was allocated to state-led research hubs in 2021.",
            "metadata": {"source_id": "GUJ-RES-2021-009", "institution": "Gujarat University", "access_tier": 1, "year": 2021, "topics": ["Robotics", "Economics"]}
        },
        {
            "id": "IITGN-2020-088",
            "text": "Researcher Arjun Sharma at IIT Gandhinagar published groundbreaking work on multi-agent systems for disaster management in 2020.",
            "metadata": {"source_id": "IITGN-2020-088", "institution": "IIT Gandhinagar", "access_tier": 1, "year": 2020, "topics": ["Robotics", "AI"]}
        }
    ]

    points = []
    for i, paper in enumerate(papers):
        vector = model.encode(paper["text"]).tolist()
        # Save to disk as well for consistency with protocol
        with open(data_dir / f"{paper['id']}.md", "w") as f:
            f.write(paper["text"])
        
        points.append(PointStruct(
            id=i,
            vector=vector,
            payload={"text": paper["text"], **paper["metadata"]}
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Indexed {len(points)} documents into Qdrant")

if __name__ == "__main__":
    ingest()
