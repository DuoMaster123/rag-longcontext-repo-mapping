import json
import re
from pathlib import Path

class EnvVarParser:
    def __init__(self):
        # Regex to match environment variable fetching patterns 
        # e.g., os.getenv("DATABASE_URL") or os.environ.get('API_KEY')
        self.env_pattern = re.compile(r'(?:os\.getenv|os\.environ\.get)\(\s*["\']([^"\']+)["\']')
        
    def parse_file(self, file_path: Path) -> list:
        env_vars = set()
        try:
            content = file_path.read_text(encoding='utf-8')
            
            matches = self.env_pattern.findall(content)
            for match in matches:
                env_vars.add(match)
                
        except Exception as e:
            print(f"[WARN] Skipped file {file_path.name} due to error: {e}")
            
        return [{"file": file_path.name, "env_var": var} for var in env_vars]

    def scan_repository(self, repo_path: str) -> list:
        all_envs = []
        repo_dir = Path(repo_path)
        ignored_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache', 'tests'}
        
        for file_path in repo_dir.rglob("*.py"):
            if not any(ignored in file_path.parts for ignored in ignored_dirs):
                all_envs.extend(self.parse_file(file_path))
                
        return all_envs

    def export_to_json(self, data: list, output_path: str):
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Environment variables exported to: {out_file.resolve()}")

# Execution block for testing
if __name__ == "__main__":
    parser_tool = EnvVarParser()
    PATH_TO_REPO = "data/raw/fastapi-crud-async" 
    OUTPUT_JSON = "data/ground_truth/fastapi_crud_env.json"
    
    repo_path = Path(PATH_TO_REPO)
    if repo_path.exists():
        print(f"[INFO] Scanning environment variables at: {repo_path}...")
        results = parser_tool.scan_repository(PATH_TO_REPO)
        
        print(f"\n--- Found {len(results)} Environment Variables ---")
        for env in results:
            print(f"Variable: {env['env_var']} (File: {env['file']})")
            
        print("\n[INFO] Saving results...")
        parser_tool.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found. Please verify the path.")