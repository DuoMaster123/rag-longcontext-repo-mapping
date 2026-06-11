import os
import subprocess
import shutil
from pathlib import Path

class GitManager:
    def __init__(self, workspace_dir: str = "data/live_workspace"):
        self.workspace_dir = Path(workspace_dir)
        # Guardrail Configurations to prevent API Rate Limits
        self.MAX_FILES_ALLOWED = 150
        self.MAX_SIZE_MB_ALLOWED = 2.0

    def clean_workspace(self, repo_name: str):
        """Removes the specific repo workspace to ensure a fresh clone."""
        target_dir = self.workspace_dir / repo_name
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception as e:
                print(f"[WARN] Could not completely clean workspace: {e}")
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def clone_repo(self, repo_url: str) -> str:
        """Clones a GitHub repository into the local workspace (raw folder)."""
        if not repo_url.startswith("https://github.com/"):
            raise ValueError("[ERROR] Security restriction: Only 'https://github.com/' URLs are supported.")

        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        # Structure: data/live_workspace/{repo_name}/raw/
        base_dir = self.clean_workspace(repo_name)
        raw_path = base_dir / "raw"
        
        print(f"[INFO] Initializing git clone for: {repo_url}")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(raw_path)], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            print(f"[SUCCESS] Repository cloned to {raw_path}")
            return str(raw_path), str(base_dir)
        except subprocess.CalledProcessError as e:
            error_details = e.stderr.decode('utf-8').strip()
            raise RuntimeError(f"[ERROR] Git clone failed. Details: {error_details}")

    def validate_repo_limits(self, repo_path: str, file_ext: str):
        """Scans the repository to ensure it does not exceed API context limits."""
        path = Path(repo_path)
        total_size_bytes = 0
        file_count = 0
        
        ignored_dirs = {'.git', 'venv', '__pycache__', 'node_modules', 'dist', 'target', '.idea'}

        for file_path in path.rglob(file_ext):
            if not any(ignored in file_path.parts for ignored in ignored_dirs):
                file_count += 1
                total_size_bytes += file_path.stat().st_size

        total_size_mb = total_size_bytes / (1024 * 1024)
        print(f"[INFO] Validation Scan: Found {file_count} valid files ({total_size_mb:.2f} MB).")

        if file_count > self.MAX_FILES_ALLOWED:
            raise OverflowError(f"[GUARDRAIL] Repository too large! Found {file_count} files (Max allowed: {self.MAX_FILES_ALLOWED}). Please test a smaller project.")
        
        if total_size_mb > self.MAX_SIZE_MB_ALLOWED:
            raise OverflowError(f"[GUARDRAIL] Repository too heavy! Size is {total_size_mb:.2f} MB (Max allowed: {self.MAX_SIZE_MB_ALLOWED} MB).")

    def detect_framework(self, repo_path: str) -> str:
        """Heuristic engine to identify the software framework."""
        path = Path(repo_path)
        
        # NestJS (TypeScript)
        package_json = path / "package.json"
        if package_json.exists() and "@nestjs/core" in package_json.read_text(encoding="utf-8", errors="ignore"):
            self.validate_repo_limits(repo_path, "*.ts")
            return "NestJS (TypeScript)"

        # Spring Boot (Java)
        pom_xml = path / "pom.xml"
        build_gradle = path / "build.gradle"
        if (pom_xml.exists() and "spring-boot" in pom_xml.read_text(encoding="utf-8", errors="ignore")) or \
           (build_gradle.exists() and "spring-boot" in build_gradle.read_text(encoding="utf-8", errors="ignore")):
            self.validate_repo_limits(repo_path, "*.java")
            return "Spring Boot (Java)"
            
        for java_file in path.rglob("*.java"):
            if "@SpringBootApplication" in java_file.read_text(encoding="utf-8", errors="ignore"):
                self.validate_repo_limits(repo_path, "*.java")
                return "Spring Boot (Java)"

        # FastAPI (Python)
        req_txt = path / "requirements.txt"
        pyproject = path / "pyproject.toml"
        if (req_txt.exists() and "fastapi" in req_txt.read_text(encoding="utf-8", errors="ignore").lower()) or \
           (pyproject.exists() and "fastapi" in pyproject.read_text(encoding="utf-8", errors="ignore").lower()):
            self.validate_repo_limits(repo_path, "*.py")
            return "FastAPI (Python)"
            
        for py_file in path.rglob("*.py"):
            if "fastapi" in py_file.read_text(encoding="utf-8", errors="ignore").lower():
                self.validate_repo_limits(repo_path, "*.py")
                return "FastAPI (Python)"

        raise ValueError("[REJECTED] The repository architecture is not supported. Only FastAPI, NestJS, and Spring Boot are allowed.")