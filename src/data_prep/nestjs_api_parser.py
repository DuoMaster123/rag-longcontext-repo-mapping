import os
import json
import re
from pathlib import Path

class NestJSAPIParser:
    def __init__(self):
        # Allow optional parameters inside controller parentheses
        self.controller_pattern = re.compile(r'@Controller\(\s*(?:[\'"]([^\'"]*)[\'"])?\s*\)')
        self.method_pattern = re.compile(r'@(Get|Post|Put|Delete|Patch|Options)\(\s*(?:[\'"]([^\'"]*)[\'"])?\s*\)')

    def parse_file(self, file_path: Path) -> list:
        endpoints = []
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 1. Capture Controller Base Path
            controller_match = self.controller_pattern.search(content)
            if not controller_match:
                return []
                
            # Safely handle empty @Controller() declarations
            base_path = controller_match.group(1).strip('/') if controller_match.group(1) else ""
            
            # 2. Capture API Endpoints
            lines = content.split('\n')
            for line in lines:
                method_match = self.method_pattern.search(line)
                if method_match:
                    http_method = method_match.group(1).upper()
                    sub_path = method_match.group(2).strip('/') if method_match.group(2) else ""
                    
                    # Smart path concatenation
                    if base_path and sub_path:
                        full_path = f"/{base_path}/{sub_path}".rstrip('/')
                    elif base_path:
                        full_path = f"/{base_path}".rstrip('/')
                    elif sub_path:
                        full_path = f"/{sub_path}".rstrip('/')
                    else:
                        full_path = "/"
                        
                    endpoints.append({
                        "file": file_path.name,
                        "method": http_method,
                        "path": full_path,
                        "handler": "unknown_in_regex"
                    })
        except Exception as e:
            print(f"[ERROR] Cannot read file {file_path.name}: {e}")
            
        return endpoints

    def scan_repository(self, repo_path: str) -> list:
        all_endpoints = []
        repo_dir = Path(repo_path)
        
        for file_path in repo_dir.rglob("*.ts"):
            if "node_modules" not in file_path.parts and "dist" not in file_path.parts:
                all_endpoints.extend(self.parse_file(file_path))
                
        return all_endpoints

    def export_to_json(self, data: list, output_path: str):
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported NestJS API Ground Truth to: {out_file.name}")

if __name__ == "__main__":
    parser = NestJSAPIParser()
    PATH_TO_REPO = "data/raw/nestjs-realworld-example-app"
    OUTPUT_JSON = "data/ground_truth/nestjs_realworld_api.json"
    
    if os.path.exists(PATH_TO_REPO):
        print("[INFO] Scanning NestJS APIs...")
        results = parser.scan_repository(PATH_TO_REPO)
        
        print(f"[INFO] Found {len(results)} API endpoints.")
        parser.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found.")