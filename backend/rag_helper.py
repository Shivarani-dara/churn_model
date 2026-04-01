from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def load_knowledge_base(path="rag_data/retention_knowledge.txt"):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

knowledge_chunks = load_knowledge_base()
knowledge_embeddings = embed_model.encode(knowledge_chunks)

def retrieve_relevant_knowledge(query, top_k=3):
    query_embedding = embed_model.encode([query])
    scores = cosine_similarity(query_embedding, knowledge_embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [knowledge_chunks[i] for i in top_indices]
