import logging
import os
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Singleton pattern for embedding model
embedding_model = None
FAISS_DIR = "./faiss_index"

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    global embedding_model
    if embedding_model is None:
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return embedding_model

def store_mcps_in_faiss(mcps: List[Dict[str, str]], persist_path: str = FAISS_DIR, collection_name: str = "mcp_servers"):
    """
    Stores MCP server info as embeddings in a FAISS index using LangChain.
    Each MCP dict should have 'name', 'description', 'link'.
    """
    # Ensure the persist directory exists
    dir_path = persist_path if os.path.splitext(persist_path)[1] == "" else os.path.dirname(persist_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)    
    model = get_embedding_model()
    texts = [f"{mcp['name']}: {mcp['description']}" for mcp in mcps]
    metadatas = [{"name": mcp["name"], "link": mcp["link"], "description": mcp["description"]} for mcp in mcps]
    ids = [mcp["link"] for mcp in mcps]  # Use link as unique id
    try:
        db = FAISS.from_texts(texts=texts, embedding=model, metadatas=metadatas)
        db.save_local(persist_path)
        logger.info(f"Upserted {len(ids)} MCP entries into FAISS index '{collection_name}' using LangChain.")
    except Exception as e:
        logger.error(f"Failed to upsert MCPs into FAISS via LangChain: {e}")

def semantic_search_mcps(query: str, mcps: list = None, persist_path: str = FAISS_DIR, n_results: int = 5):
    model = get_embedding_model()
    logger.info(f"Performing semantic search for query: {query}")
    try:
        db = FAISS.load_local(persist_path, model, allow_dangerous_deserialization=True)
        logger.info(f"FAISS index loaded successfully from {persist_path}.")
    except Exception as e:
        logger.warning(f"FAISS index not found or failed to load: {e}. Attempting to build index...")
        if mcps is not None:
            store_mcps_in_faiss(mcps, persist_path=persist_path)
            try:
                db = FAISS.load_local(persist_path, model, allow_dangerous_deserialization=True)
                logger.info(f"FAISS index built and loaded successfully from {persist_path}.")
            except Exception as e2:
                logger.error(f"Failed to build/load FAISS index: {e2}")
                return []
        else:
            logger.error("No MCP data provided to build FAISS index.")
            return []
    try:
        results = db.similarity_search(query, k=n_results)
        logger.info(f"Found {len(results)} results for query: {query}")
        return results
    except Exception as e:
        logger.error(f"Failed to perform semantic search with FAISS: {e}")
        return []
