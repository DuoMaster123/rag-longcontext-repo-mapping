import os
import sys
import json
from pathlib import Path

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.llm_pipeline import AIEngine

class LongContextEngine:
    def __init__(self):
        self.ai_engine = AIEngine()

    def pack_repository(self, repo_path: str) -> str:
        """Packages the entire repository (.py, .ts, .java) into a single string wrapped in XML-like tags."""
        repo_dir = Path(repo_path)
        ignored_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache', 'tests', 'node_modules', 'dist', 'target', '.idea'}
        valid_extensions = {'.py', '.ts', '.java'}
        
        full_context = []
        for file_path in repo_dir.rglob("*.*"):
            if file_path.suffix in valid_extensions and not any(ignored in file_path.parts for ignored in ignored_dirs):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    rel_path = file_path.relative_to(repo_dir)
                    full_context.append(f'<file path="{rel_path}">\n{content}\n</file>')
                except Exception as e:
                    print(f"[WARN] Skipped file {file_path.name} due to read error: {e}")
                    
        return "\n\n".join(full_context)

    def extract_information(self, repo_path: str, task_type: str) -> str:
        """Parses the entire repository using Gemini 2.5 Flash to extract information."""
        
        # Determine prompts based on task type
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
            raise ValueError("[ERROR] Invalid task type.")

        # Pack the repository context
        print(f"[INFO] Packaging source code at: {repo_path}...")
        context = self.pack_repository(repo_path)
        print(f"[INFO] Packaging complete. Total context size: {len(context)} characters.")

        # Construct final prompt
        final_user_prompt = f"Context from the entire repository:\n{context}\n\nTask: {query}"
        
        # Invoke LLM
        response = self.ai_engine.ask_gemini(system_prompt, final_user_prompt)
        
        return response

# Execution block for testing
if __name__ == "__main__":
    lc_engine = LongContextEngine()
    PATH_TO_REPO = "data/raw/fastapi-crud-async"
    
    if os.path.exists(PATH_TO_REPO):
        print("\n--- Test: Extracting Database Models via Long-Context ---")
        db_result = lc_engine.extract_information(repo_path=PATH_TO_REPO, task_type="DB")
        
        print("\n[INFO] Gemini 2.5 Flash Response (JSON format expected):")
        print(db_result)
        
        try:
            parsed_json = json.loads(db_result)
            print(f"\n[SUCCESS] JSON parsed successfully. Found {len(parsed_json)} models.")
        except Exception as e:
            print(f"\n[WARN] Failed to parse JSON: {e}")
    else:
        print("[ERROR] Repository not found. Please verify the path.")