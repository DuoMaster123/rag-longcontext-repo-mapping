import os
import json
import re
from pathlib import Path

class SpringBootEnvParser:
    def scan_repository(self, repo_path: str) -> list:
        env_vars = set()
        for file_path in Path(repo_path).rglob("*.java"):
            content = file_path.read_text(encoding='utf-8')
            # Match environment variables injected via @Value("${...}")
            for match in re.finditer(r'@Value\s*\(\s*"\$\{([^:}]+)', content):
                env_vars.add(match.group(1))
        
        return [{"file": "multiple_files", "env_var": var} for var in env_vars]

    def export_to_json(self, data: list, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] Exported Spring ENV Ground Truth: {len(data)} variables.")

if __name__ == "__main__":
    parser = SpringBootEnvParser()
    parser.export_to_json(parser.scan_repository("data/raw/spring-boot-realworld-example-app"), "data/ground_truth/spring_realworld_env.json")