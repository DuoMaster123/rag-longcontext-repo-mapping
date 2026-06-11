import json
from pathlib import Path
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

class FastAPIParser:
    def __init__(self):
        self.py_language = Language(tspython.language())
        self.parser = Parser(self.py_language)
        
        self.query_string = """
        (decorated_definition
          (decorator
            (call
              function: (attribute
                object: (identifier) @router
                attribute: (identifier) @method)
              arguments: (argument_list
                (string) @path)))
          definition: (function_definition
            name: (identifier) @function_name))
        """
        self.query = Query(self.py_language, self.query_string)
        
        # Valid HTTP methods to filter out event handlers
        self.valid_http_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"}

    def parse_file(self, file_path: Path) -> list:
        """Parses API endpoints from a specified file."""
        endpoints = []
        try:
            source_code = file_path.read_bytes()
            tree = self.parser.parse(source_code)
            cursor = QueryCursor(self.query)
            
            for match in cursor.matches(tree.root_node):
                captures = match[1]
                method_node = captures.get("method", [None])[0]
                path_node = captures.get("path", [None])[0]
                func_node = captures.get("function_name", [None])[0]
                
                if method_node and path_node and func_node:
                    method_name = method_node.text.decode('utf8').upper()
                    
                    if method_name in self.valid_http_methods:
                        endpoints.append({
                            "file": file_path.name,
                            "method": method_name,
                            "path": path_node.text.decode('utf8').strip('"\''),
                            "handler": func_node.text.decode('utf8')
                        })
        except Exception as e:
            print(f"[WARN] Skipped file {file_path.name} due to error: {e}")
            
        return endpoints

    def scan_repository(self, repo_path: str) -> list:
        """Scans the repository, skipping ignored directories."""
        all_endpoints = []
        repo_dir = Path(repo_path)
        ignored_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache', 'tests'}
        
        for file_path in repo_dir.rglob("*.py"):
            if not any(ignored in file_path.parts for ignored in ignored_dirs):
                all_endpoints.extend(self.parse_file(file_path))
                
        return all_endpoints

    def export_to_json(self, data: list, output_path: str):
        """Persists the parsed endpoint data to a JSON file."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Ground truth saved to: {out_file.resolve()}")

# Execution block for testing
if __name__ == "__main__":
    parser_tool = FastAPIParser()
    PATH_TO_REPO = "data/raw/fastapi-crud-async" 
    OUTPUT_JSON = "data/ground_truth/fastapi_crud_api.json"
    
    repo_path = Path(PATH_TO_REPO)
    if repo_path.exists():
        print(f"[INFO] Scanning API endpoints at: {repo_path}...")
        results = parser_tool.scan_repository(PATH_TO_REPO)
        
        print(f"\n--- Found {len(results)} API Endpoints ---")
        for api in results:
            print(f"[{api['method']}] {api['path']} (File: {api['file']})")
            
        print("\n[INFO] Saving results...")
        parser_tool.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found. Please verify the path.")