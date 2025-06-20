import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    Distance,
)
from qdrant_client.models import PayloadSchemaType
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Load ENV
QDRANT_URL = settings.VECTOR_DB_URL
QDRANT_API_KEY = settings.VECTOR_DB_API_KEY
COLLECTION = settings.VECTOR_DB_COLLECTION

# Initialize Qdrant Client
qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# Load embedding model
encoder = SentenceTransformer("all-MiniLM-L6-v2")


def ensure_collection_and_indexes(vector_size: int):
    collections = qdrant.get_collections().collections
    collection_exists = COLLECTION in [c.name for c in collections]
    
    if not collection_exists:
        # Create collection
        qdrant.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
    
    # Always try to create indexes (they will be ignored if they already exist)
    try:
        qdrant.create_payload_index(
            collection_name=COLLECTION,
            field_name="chat_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        # Index might already exist, ignore the error
        pass
    
    try:
        qdrant.create_payload_index(
            collection_name=COLLECTION,
            field_name="filename",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        # Index might already exist, ignore the error
        pass


# Search similar chunks by chat
def search_context(query: str, chat_id):
    query_vector = encoder.encode(query).tolist()

    # Ensure collection and index exist
    ensure_collection_and_indexes(vector_size=len(query_vector))

    # Perform search
    results = qdrant.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=5,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="chat_id",
                    match=MatchValue(value=str(chat_id)),
                )
            ]
        ),
    )

    contexts = [hit.payload.get("text", "") for hit in results]
    return "\n".join(contexts)


# Store embeddings in Qdrant
def embed_and_store(text: str, chat_id, filename: str):
    chunks = [text[i:i + 1000] for i in range(0, len(text), 1000)]
    vectors = encoder.encode(chunks)

    # Ensure collection and index exist
    ensure_collection_and_indexes(vector_size=len(vectors[0]))

    points = []
    for i, vector in enumerate(vectors):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": chunks[i],
                "chat_id": str(chat_id),
                "filename": filename
            }
        ))

    qdrant.upsert(
        collection_name=COLLECTION,
        points=points
    )


# Delete embeddings for a file
def delete_document_vectors(chat_id: uuid.UUID, filename: str):
    qdrant.delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="chat_id",
                    match=MatchValue(value=str(chat_id)),
                ),
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=filename),
                ),
            ]
        ),
    )
