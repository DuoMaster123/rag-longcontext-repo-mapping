import os
import json
import re
from pathlib import Path

class NestJSDatabaseParser:
    def __init__(self):
        # Matches @Entity() or @Entity('table_name')
        self.entity_pattern = re.compile(r'@Entity\(\s*(?:[\'"]([^\'"]*)[\'"])?\s*\)')
        
        # Matches TypeORM column decorators and extracts the property name
        self.column_pattern = re.compile(
            r'@(?:Column|PrimaryGeneratedColumn|CreateDateColumn|UpdateDateColumn)(?:[^)]*)\)?\s*(?:(?:export|public|private|protected|readonly)\s+)?([a-zA-Z0-9_]+)\s*[!?:=]',
            re.MULTILINE
        )
        
        # Matches the class name
        self.class_pattern = re.compile(r'class\s+([a-zA-Z0-9_]+)')

    def parse_file(self, file_path: Path) -> dict:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if file contains a database Entity
            if not self.entity_pattern.search(content):
                return None
                
            # Extract Model (Class) Name
            class_match = self.class_pattern.search(content)
            model_name = class_match.group(1) if class_match else "UnknownModel"
            
            # Extract Fields
            fields = []
            for match in self.column_pattern.finditer(content):
                field_name = match.group(1).strip()
                fields.append({
                    "name": field_name,
                    "type": "extracted_via_regex" # Type resolution is complex in regex, name is sufficient
                })
                
            if fields:
                return {
                    "file": file_path.name,
                    "model": model_name,
                    "fields": fields
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to parse file {file_path.name}: {e}")
            
        return None

    def scan_repository(self, repo_path: str) -> list:
        all_models = []
        repo_dir = Path(repo_path)
        
        for file_path in repo_dir.rglob("*.ts"):
            if "node_modules" not in file_path.parts and "dist" not in file_path.parts:
                result = self.parse_file(file_path)
                if result:
                    all_models.append(result)
                    
        return all_models

    def export_to_json(self, data: list, output_path: str):
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported NestJS DB Ground Truth to: {out_file.name}")

if __name__ == "__main__":
    parser = NestJSDatabaseParser()
    PATH_TO_REPO = "data/raw/nestjs-realworld-example-app"
    OUTPUT_JSON = "data/ground_truth/nestjs_realworld_db.json"
    
    print("[INFO] Scanning NestJS Database Models...")
    if os.path.exists(PATH_TO_REPO):
        results = parser.scan_repository(PATH_TO_REPO)
        print(f"[INFO] Found {len(results)} database models.")
        parser.export_to_json(results, OUTPUT_JSON)
    else:
        print("[ERROR] Repository not found.")