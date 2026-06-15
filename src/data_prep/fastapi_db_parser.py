import json
from pathlib import Path
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

class DBModelParser:
    def __init__(self):
        self.py_language = Language(tspython.language())
        self.parser = Parser(self.py_language)
        
        self.class_query = Query(self.py_language, """
        (class_definition
          name: (identifier) @model_name
          body: (block) @model_body)
        """)

    def parse_file(self, file_path: Path) -> list:
        """Parses database models and schema definitions from a specified file."""
        models = []
        try:
            source_code = file_path.read_bytes()
            tree = self.parser.parse(source_code)
            cursor = QueryCursor(self.class_query)
            
            for match in cursor.matches(tree.root_node):
                captures = match[1]
                model_node = captures.get("model_name", [None])[0]
                body_node = captures.get("model_body", [None])[0]
                
                if not model_node or not body_node:
                    continue
                
                model_name = model_node.text.decode('utf8')
                fields = []
                
                for child in body_node.named_children:
                    if child.type == "expression_statement":
                        code_line = child.text.decode('utf8').strip()
                        
                        # Ignore docstrings
                        if code_line.startswith('"""') or code_line.startswith("'''"):
                            continue
                            
                        # Parse Pydantic-style type hints
                        if ":" in code_line and "=" not in code_line:
                            f_name, f_type = code_line.split(":", 1)
                            fields.append({"name": f_name.strip(), "type": f_type.strip()})
                        
                        # Parse ORM-style assignments
                        elif "=" in code_line:
                            f_name, f_value = code_line.split("=", 1)
                            if f_name.strip() != "model_config": 
                                fields.append({"name": f_name.strip(), "type": f_value.strip()})
                
                # Append if valid fields exist
                if fields:
                    models.append({
                        "file": file_path.name,
                        "model": model_name,
                        "fields": fields
                    })
        except Exception as e:
            print(f"[WARN] Skipped file {file_path.name} due to error: {e}")
            
        return models

    def scan_repository(self, repo_path: str) -> list:
        """Scans the repository for database models."""
        all_models = []
        repo_dir = Path(repo_path)
        ignored_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache', 'tests'}
        
        for file_path in repo_dir.rglob("*.py"):
            if not any(ignored in file_path.parts for ignored in ignored_dirs):
                all_models.extend(self.parse_file(file_path))
                
        return all_models

    def export_to_json(self, data: list, output_path: str):
        """Persists the parsed model data to a JSON file."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Database structure saved to: {out_file.resolve()}")

# Execution block for testing
if __name__ == "__main__":
    parser_tool = DBModelParser()
    PATH_TO_REPO = "data/raw/fastapi-crud-async" 
    OUTPUT_JSON = "data/ground_truth/fastapi_crud_db.json"
    
    repo_path = Path(PATH_TO_REPO)
    if repo_path.exists():
        print(f"[INFO] Scanning database structures at: {repo_path}...")
        results = parser_tool.scan_repository(PATH_TO_REPO)
        
        print(f"\n--- Found {len(results)} Database Models ---")
        for db in results:
            field_names = [f["name"] for f in db["fields"]]
            print(f"Table: {db['model']} | Fields: {', '.join(field_names)} (File: {db['file']})")
            
        print("\n[INFO] Saving results...")
        parser_tool.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found. Please verify the path.")