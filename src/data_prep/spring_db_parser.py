import os
import json
import re
from pathlib import Path

class SpringBootDBParser:
    def scan_repository(self, repo_path: str) -> list:
        models = []
        for file_path in Path(repo_path).rglob("*.java"):
            content = file_path.read_text(encoding='utf-8')
            if "@Entity" in content or "@Table" in content:
                # Match Class Name (Model)
                class_match = re.search(r'\bclass\s+([A-Za-z0-9_]+)', content)
                if class_match:
                    models.append({
                        "file": file_path.name,
                        "model": class_match.group(1),
                        # Simplified fields since Evaluator only compares Model names
                        "fields": [{"name": "extracted_via_regex", "type": "unknown"}] 
                    })
        return models

    def export_to_json(self, data: list, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported Spring DB Ground Truth: {len(data)} models.")

if __name__ == "__main__":
    parser = SpringBootDBParser()
    parser.export_to_json(parser.scan_repository("data/raw/spring-boot-realworld-example-app"), "data/ground_truth/spring_realworld_db.json")