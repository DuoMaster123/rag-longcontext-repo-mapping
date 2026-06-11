import os
import json
import re
from pathlib import Path

class NestJSEnvParser:
    def __init__(self):
        # Matches native Node.js process.env calls
        self.process_env_pattern = re.compile(r'process\.env\.([A-Z0-9_]+)')
        
        # Matches NestJS ConfigService calls, handling optional generic types <T>
        self.config_service_pattern = re.compile(r'\.get(?:<[^>]+>)?\(\s*[\'"]([A-Z0-9_]+)[\'"]\s*\)')

    def parse_file(self, file_path: Path) -> list:
        env_vars = set() # Using set to prevent duplicate variables within the same file
        try:
            content = file_path.read_text(encoding='utf-8')
            
            for match in self.process_env_pattern.finditer(content):
                env_vars.add(match.group(1))
                
            for match in self.config_service_pattern.finditer(content):
                env_vars.add(match.group(1))
                
        except Exception as e:
            print(f"[ERROR] Failed to parse file {file_path.name}: {e}")
            
        return [{"file": file_path.name, "env_var": var} for var in env_vars]

    def scan_repository(self, repo_path: str) -> list:
        all_envs = []
        repo_dir = Path(repo_path)
        
        for file_path in repo_dir.rglob("*.ts"):
            if "node_modules" not in file_path.parts and "dist" not in file_path.parts:
                all_envs.extend(self.parse_file(file_path))
                
        return all_envs

    def export_to_json(self, data: list, output_path: str):
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported NestJS ENV Ground Truth to: {out_file.name}")

if __name__ == "__main__":
    parser = NestJSEnvParser()
    PATH_TO_REPO = "data/raw/nestjs-realworld-example-app"
    OUTPUT_JSON = "data/ground_truth/nestjs_realworld_env.json"
    
    print("[INFO] Scanning NestJS Environment Variables...")
    if os.path.exists(PATH_TO_REPO):
        results = parser.scan_repository(PATH_TO_REPO)
        print(f"[INFO] Found {len(results)} environment variables.")
        parser.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found.")