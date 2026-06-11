import os
import sys
import json
import chromadb
from chromadb.utils import embedding_functions

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.llm_pipeline import AIEngine

class RAGQueryEngine:
    def __init__(self, db_path: str = "data/vector_db", collection_name: str = "nestjs_realworld_codebase"):
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        
        # Initialize LLM Engine
        self.ai_engine = AIEngine()

    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        """Retrieves top_k relevant chunks from Vector DB."""
        print(f"[INFO] Retrieving source code context for query: '{query}'...")
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        context_chunks = []
        if results.get('documents') and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                file_name = results['metadatas'][0][i]['file_name']
                context_chunks.append(f"--- Start excerpt from file: {file_name} ---\n{doc}\n--- End excerpt ---")
                
        return "\n\n".join(context_chunks)

    def extract_information(self, task_type: str) -> str:
        """Executes RAG query based on task type (API, DB, ENV)."""
        
        # Configure prompts based on task type
        if task_type == "API":
            system_prompt = "You are an expert software architect. Return a strict JSON array of objects with keys: file, method, path, handler. Do NOT include Markdown formatting or explanations."
            query = "Analyze the code and extract all API endpoints."
            
        elif task_type == "DB":
            system_prompt = "You are an expert data engineer. Return a strict JSON array of objects with keys: file, model, fields (array of {name, type}). Do NOT include Markdown formatting or explanations."
            query = "Identify all database models, schemas, or ORM definitions and their fields."
            
        elif task_type == "ENV":
            system_prompt = "You are an expert DevOps engineer. Return a strict JSON array of objects with keys: file, env_var. Do NOT include Markdown formatting or explanations."
            query = "Identify all environment variables required to run this application."
            
        else:
            raise ValueError("[ERROR] Invalid task type. Valid options are 'API', 'DB', or 'ENV'.")

        # Retrieve context from Vector DB
        context = self.retrieve_context(query, top_k=7)
        if not context:
            return "[]" 

        # Construct final prompt
        final_user_prompt = f"Context from repository:\n{context}\n\nTask: {query}"
        
        # Invoke LLM
        print(f"[INFO] Analyzing context ({len(context)} characters) with AI engine...")
        response = self.ai_engine.ask_gpt4o(system_prompt, final_user_prompt)
        
        return response

# Execution block for testing
if __name__ == "__main__":
    rag_engine = RAGQueryEngine()
    
    print("\n--- Test: Extracting Database Models via RAG ---")
    db_result = rag_engine.extract_information(task_type="DB")
    
    print("\n[INFO] AI Response (JSON format expected):")
    print(db_result)
    
    try:
        parsed_json = json.loads(db_result)
        print(f"\n[SUCCESS] JSON parsed successfully. Found {len(parsed_json)} models.")
    except Exception as e:
        print(f"\n[WARN] Failed to parse JSON: {e}")