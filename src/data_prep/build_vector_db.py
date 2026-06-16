import os
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

class UniversalVectorBuilder:
    def __init__(self, db_path: str = "data/vector_db", collection_name: str = "spring_realworld_codebase"):
        print(f"[INFO] Initializing ChromaDB client for collection: {collection_name}...")
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Clean up existing collection if it exists
        try:
            self.client.delete_collection(name=collection_name)
            print(f"[INFO] Reset existing collection: {collection_name}")
        except Exception:
            pass
            
        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def simple_chunker(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
        """Safe sliding window chunking algorithm for code blocks."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def build_database(self, repo_path: str, file_extension: str = "*.java"):
        print(f"[INFO] Scanning source code at: {repo_path}")
        repo_dir = Path(repo_path)
        
        # Enhanced token optimization: Ignore boilerplate and testing directories
        ignored_dirs = {'target', '.git', 'src/test', 'test', 'tests', '.idea', 'node_modules', 'dist', 'venv', '.venv', 'env', '__pycache__', 'migrations', 'coverage', 'build'}
        
        documents = []
        metadatas = []
        ids = []
        chunk_id_counter = 0
        
        for file_path in repo_dir.rglob(file_extension):
            if not any(ignored in file_path.parts for ignored in ignored_dirs):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Token Optimization: Strip empty lines to maximize token density per chunk
                    optimized_content = "\n".join(line for line in content.splitlines() if line.strip())
                    
                    chunks = self.simple_chunker(optimized_content)
                    
                    for chunk in chunks:
                        documents.append(chunk)
                        metadatas.append({
                            "file_name": file_path.name, 
                            "rel_path": str(file_path.relative_to(repo_dir))
                        })
                        ids.append(f"chunk_{chunk_id_counter}")
                        chunk_id_counter += 1
                        
                except Exception as e:
                    print(f"[WARN] Read error on file {file_path.name}: {e}")

        if documents:
            print(f"[INFO] Embedding {len(documents)} chunks into Vector DB...")
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                self.collection.add(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
            print("[SUCCESS] Vector DB built successfully.")
        else:
            print("[ERROR] No valid source files found.")

if __name__ == "__main__":
    builder = UniversalVectorBuilder(collection_name="spring_realworld_codebase")
    PATH_TO_REPO = "data/raw/spring-boot-realworld-example-app"
    builder.build_database(PATH_TO_REPO, file_extension="*.java")