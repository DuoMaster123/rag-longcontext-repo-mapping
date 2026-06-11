import os
import json
import re
from pathlib import Path

class SpringBootAPIParser:
    def __init__(self):
        # Match ALL Spring Boot mapping annotations
        self.mapping_pattern = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(\s*([^)]*)\s*\))?')
        
        # Match class/interface boundary to evaluate base paths
        self.class_pattern = re.compile(r'\b(?:class|interface)\s+[A-Za-z0-9_]+')

    def parse_file(self, file_path: Path) -> list:
        endpoints = []
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Optimization: Skip files without API configuration
            if "Mapping" not in content:
                return []
                
            # 1. Find the class boundary
            class_match = self.class_pattern.search(content)
            class_start_idx = class_match.start() if class_match else len(content)
            
            base_path = ""
            
            # 2. Scan all mapping annotations
            for match in self.mapping_pattern.finditer(content):
                mapping_type = match.group(1).upper()
                inner_args = match.group(2) or ""
                match_pos = match.start()
                
                # Extract sub-path
                sub_path = ""
                path_match = re.search(r'(?:value\s*=\s*|path\s*=\s*)?[\'"]([^\'"]+)[\'"]', inner_args)
                if path_match:
                    sub_path = path_match.group(1).strip('/')
                    
                # Boundary Check 1: Above Class -> Base Path
                if match_pos < class_start_idx:
                    if mapping_type == "REQUEST":
                        base_path = sub_path
                    continue 
                    
                # Boundary Check 2: Below Class -> API Endpoint
                http_method = ""
                if mapping_type == "REQUEST":
                    # Manually read HTTP method from RequestMethod
                    method_match = re.search(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)', inner_args)
                    if method_match:
                        http_method = method_match.group(1)
                    else:
                        http_method = "GET" # Default Spring configuration
                else:
                    http_method = mapping_type
                    
                full_path = self._build_path(base_path, sub_path)
                
                endpoints.append({
                    "file": file_path.name,
                    "method": http_method,
                    "path": full_path,
                    "handler": "extracted_via_java_regex"
                })
                
        except Exception as e:
            print(f"[ERROR] Failed to parse file {file_path.name}: {e}")
            
        return endpoints

    def _build_path(self, base_path: str, sub_path: str) -> str:
        # Smart path concatenation, remove redundant slashes
        parts = [p for p in (base_path, sub_path) if p]
        if not parts:
            return "/"
        return "/" + "/".join(parts)

    def scan_repository(self, repo_path: str) -> list:
        all_endpoints = []
        repo_dir = Path(repo_path)
        
        for file_path in repo_dir.rglob("*.java"):
            if "src/test" not in str(file_path.as_posix()):
                all_endpoints.extend(self.parse_file(file_path))
                
        return all_endpoints

    def export_to_json(self, data: list, output_path: str):
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Filter duplicates (Java Interface vs Implementation)
        unique_endpoints = []
        seen = set()
        for ep in data:
            key = f"{ep['method']}|{ep['path']}"
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)
                
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(unique_endpoints, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported Spring Boot API Ground Truth to: {out_file.name}")

if __name__ == "__main__":
    parser = SpringBootAPIParser()
    PATH_TO_REPO = "data/raw/spring-boot-realworld-example-app"
    OUTPUT_JSON = "data/ground_truth/spring_realworld_api.json"
    
    print("[INFO] Scanning Spring Boot APIs with deep heuristics...")
    if os.path.exists(PATH_TO_REPO):
        results = parser.scan_repository(PATH_TO_REPO)
        print(f"[INFO] Found {len(results)} unique API endpoints.")
        parser.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found.")