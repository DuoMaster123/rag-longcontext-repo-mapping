import os
import json
import time
from pathlib import Path

from src.core.rag_engine import RAGQueryEngine
from src.core.long_context_engine import LongContextEngine
from src.evaluation.evaluator import ModelEvaluator
from src.core.git_manager import GitManager
from src.data_prep.build_vector_db import UniversalVectorBuilder

from src.data_prep.fastapi_api_parser import FastAPIParser
from src.data_prep.fastapi_db_parser import DBModelParser as FastAPIDBParser
from src.data_prep.fastapi_env_parser import EnvVarParser as FastAPIEnvParser

from src.data_prep.nestjs_api_parser import NestJSAPIParser
from src.data_prep.nestjs_db_parser import NestJSDatabaseParser
from src.data_prep.nestjs_env_parser import NestJSEnvParser

from src.data_prep.spring_api_parser import SpringBootAPIParser
from src.data_prep.spring_db_parser import SpringBootDBParser
from src.data_prep.spring_env_parser import SpringBootEnvParser

# Project Configurations for Static Research Mode
PROJECT_CONFIGS = {
    "fastapi_crud_async": {
        "raw_path": "data/raw/fastapi-crud-async",
        "collection_name": "fastapi_crud_codebase",
        "gt_prefix": "fastapi_crud"
    },
    "nestjs_realworld": {
        "raw_path": "data/raw/nestjs-realworld-example-app",
        "collection_name": "nestjs_realworld_codebase",
        "gt_prefix": "nestjs_realworld"
    },
    "spring_realworld": {
        "raw_path": "data/raw/spring-boot-realworld-example-app",
        "collection_name": "spring_realworld_codebase",
        "gt_prefix": "spring_realworld"
    }
}

TASKS = ["API", "DB", "ENV"]

def run_dynamic_experiment():
    """
    MODE 1: Pre-computed Experiment (Executes the predefined repositories to gather reporting metrics)
    """
    print("\n[INFO] INITIALIZING DYNAMIC AUTOMATED EXPERIMENT PIPELINE")

    evaluator = ModelEvaluator()
    lc_engine = LongContextEngine()

    for project_name, config in PROJECT_CONFIGS.items():
        print(f"\n[INFO] STARTING EXPERIMENT SUITE FOR: {project_name.upper()}")

        repo_path = config["raw_path"]
        collection_name = config["collection_name"]
        gt_prefix = config["gt_prefix"]

        if not os.path.exists(repo_path):
            print(f"[WARN] Source repository not found: {repo_path}. Skipping project...")
            continue

        print(f"[INFO] Initializing RAG Engine for collection: {collection_name}...")
        try:
            rag_engine = RAGQueryEngine(collection_name=collection_name)
        except Exception as e:
            print(f"[ERROR] Failed to load Vector DB collection '{collection_name}': {e}")
            continue

        for task in TASKS:
            print(f"\n[INFO] Executing extraction task: {task}")

            base_dir = Path(f"data/{project_name}")
            gt_file = base_dir / "ground_truth" / f"{gt_prefix}_{task.lower()}.json"
            
            rag_out = base_dir / "outputs" / f"rag_{task.lower()}_pred.json"
            lc_out = base_dir / "outputs" / f"lc_{task.lower()}_pred.json"

            # 1. RAG Extraction
            print(f"[INFO] [RAG] Extracting context...")
            try:
                rag_result = rag_engine.extract_information(task_type=task)
                with open(rag_out, "w", encoding="utf-8") as f:
                    json.dump(rag_result, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"[ERROR] RAG Pipeline fatal error on {task}: {e}")
                with open(rag_out, "w", encoding="utf-8") as f: json.dump([], f)

            # 2. Long-Context Extraction
            print(f"[INFO] [Long-Context] Parsing full repository...")
            try:
                lc_result = lc_engine.extract_information(repo_path=repo_path, task_type=task)
                with open(lc_out, "w", encoding="utf-8") as f:
                    json.dump(lc_result, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"[ERROR] Long-Context Pipeline fatal error on {task}: {e}")
                with open(lc_out, "w", encoding="utf-8") as f: json.dump([], f)

            # 3. Metrics Calculation
            print(f"\n[INFO] Triggering Evaluation Metrics for {task}:")
            if gt_file.exists():
                evaluator.evaluate_task(ground_truth_path=str(gt_file), prediction_path=str(rag_out), task_type=task)
                evaluator.evaluate_task(ground_truth_path=str(gt_file), prediction_path=str(lc_out), task_type=task)
            else:
                print(f"[ERROR] Ground truth missing at {gt_file}. Cannot compute metrics.")

            # Cooldown to respect API limits
            time.sleep(10)

    print("\n[SUCCESS] ALL PROJECT EXPERIMENTS COMPLETED SUCCESSFULLY.")


def run_live_analysis(repo_url: str):
    """
    MODE 2: Live Analyzer (Accepts a GitHub URL -> Fully automated extraction pipeline)
    """
    print(f"\n[INFO] INITIATING LIVE ANALYSIS FOR: {repo_url}")

    git_manager = GitManager()
    
    # 1. Clone & Identify Framework
    raw_path, base_dir_str = git_manager.clone_repo(repo_url)
    framework = git_manager.detect_framework(raw_path)
    print(f"[INFO] Verified Architecture Framework: {framework}")

    # 2. Select dynamic parsers based on framework
    if framework == "FastAPI (Python)":
        api_parser, db_parser, env_parser = FastAPIParser(), FastAPIDBParser(), FastAPIEnvParser()
        file_ext = "*.py"
    elif framework == "NestJS (TypeScript)":
        api_parser, db_parser, env_parser = NestJSAPIParser(), NestJSDatabaseParser(), NestJSEnvParser()
        file_ext = "*.ts"
    elif framework == "Spring Boot (Java)":
        api_parser, db_parser, env_parser = SpringBootAPIParser(), SpringBootDBParser(), SpringBootEnvParser()
        file_ext = "*.java"
    else:
        raise ValueError("[ERROR] Framework is currently unsupported for live evaluation.")

    # 3. Auto-Generate Ground Truth via AST heuristics
    repo_name = Path(base_dir_str).name
    base_dir = Path(base_dir_str)
    gt_dir = base_dir / "ground_truth"
    out_dir = base_dir / "outputs"
    gt_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Engaging AST/Regex Engines to auto-generate Ground Truth...")
    api_parser.export_to_json(api_parser.scan_repository(raw_path), str(gt_dir / f"{repo_name}_api.json"))
    db_parser.export_to_json(db_parser.scan_repository(raw_path), str(gt_dir / f"{repo_name}_db.json"))
    env_parser.export_to_json(env_parser.scan_repository(raw_path), str(gt_dir / f"{repo_name}_env.json"))

    # 4. Build Vector DB dynamically
    safe_collection_name = f"live_{repo_name.replace('-', '_').replace('.', '_').lower()[:40]}_db"
    vector_builder = UniversalVectorBuilder(collection_name=safe_collection_name)
    vector_builder.build_database(raw_path, file_extension=file_ext)

    # 5. Initialize AI Engines
    rag_engine = RAGQueryEngine(collection_name=safe_collection_name)
    lc_engine = LongContextEngine()
    evaluator = ModelEvaluator()

    live_metrics = {"API": {}, "DB": {}, "ENV": {}}

    # 6. Execute Extractions and Score
    for task in TASKS:
        print(f"\n[INFO] Executing live extraction task: {task}")
        
        gt_file = gt_dir / f"{repo_name}_{task.lower()}.json"
        rag_out = out_dir / f"rag_{task.lower()}_pred.json"
        lc_out = out_dir / f"lc_{task.lower()}_pred.json"

        # RAG Execution
        print(f"[INFO] [RAG] Parsing context...")
        try:
            rag_result = rag_engine.extract_information(task_type=task)
            with open(rag_out, "w", encoding="utf-8") as f:
                json.dump(rag_result, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] RAG extraction failed: {e}")
            with open(rag_out, "w", encoding="utf-8") as f: json.dump([], f)

        # Long-Context Execution
        print(f"[INFO] [Long-Context] Parsing context...")
        try:
            lc_result = lc_engine.extract_information(repo_path=raw_path, task_type=task)
            with open(lc_out, "w", encoding="utf-8") as f:
                json.dump(lc_result, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Long-Context extraction failed: {e}")
            with open(lc_out, "w", encoding="utf-8") as f: json.dump([], f)

        # Collect scores
        print(f"\n[INFO] Automatically scoring {task}:")
        rag_scores = evaluator.evaluate_task(ground_truth_path=str(gt_file), prediction_path=str(rag_out), task_type=task)
        lc_scores = evaluator.evaluate_task(ground_truth_path=str(gt_file), prediction_path=str(lc_out), task_type=task)
        
        live_metrics[task] = {"RAG": rag_scores, "LC": lc_scores}
        
        # Prevent hitting API rate limits on free tiers by adding a cooldown
        if task != "ENV":
            print("[INFO] Cooldown active. Waiting 15 seconds to prevent rate limiting...")
            time.sleep(15)

    print(f"\n[SUCCESS] LIVE ANALYSIS COMPLETED FOR: {repo_name}")
    
    return {
        "repo_name": repo_name,
        "framework": framework,
        "base_dir": str(base_dir),
        "metrics": live_metrics
    }

if __name__ == "__main__":
    run_dynamic_experiment() 
    # run_live_analysis("https://github.com/tiangolo/fastapi")