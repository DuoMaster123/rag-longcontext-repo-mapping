import json
import os
import re
from pathlib import Path

class ModelEvaluator:
    def __init__(self):
        pass

    def load_json(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Recovery algorithm: If data is a string (e.g., wrapped in Markdown by the LLM)
            if isinstance(data, str):
                match = re.search(r'\[.*\]', data, re.DOTALL)
                if match:
                    clean_json_str = match.group(0)
                    try:
                        return json.loads(clean_json_str)
                    except json.JSONDecodeError:
                        print("[WARN] Data recovery failed. Invalid JSON format.")
                        return None
                else:
                    return None
            return data
        except Exception as e:
            print(f"[ERROR] Failed to read file {file_path}: {e}")
            return None

    def _normalize_string(self, text: str) -> str:
        if not text:
            return ""
        return str(text).strip().lower().rstrip('/')

    def evaluate_task(self, ground_truth_path: str, prediction_path: str, task_type: str) -> dict:
        print(f"\n[INFO] Evaluating target: {Path(prediction_path).name}")
        
        ground_truth = self.load_json(ground_truth_path)
        predictions = self.load_json(prediction_path)

        if ground_truth is None:
            print("[ERROR] Ground truth file is missing or invalid.")
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}
            
        if not isinstance(predictions, list):
            print("[WARN] AI output is not a valid JSON list. Treating as an empty result.")
            predictions = []

        gt_set = set()
        pred_set = set()

        if task_type == "API":
            gt_set = {f"{self._normalize_string(item.get('method'))}|{self._normalize_string(item.get('path'))}" for item in ground_truth if isinstance(item, dict)}
            pred_set = {f"{self._normalize_string(item.get('method'))}|{self._normalize_string(item.get('path'))}" for item in predictions if isinstance(item, dict)}
        elif task_type == "DB":
            gt_set = {self._normalize_string(item.get('model')) for item in ground_truth if isinstance(item, dict)}
            pred_set = {self._normalize_string(item.get('model')) for item in predictions if isinstance(item, dict)}
        elif task_type == "ENV":
            gt_set = {self._normalize_string(item.get('env_var')) for item in ground_truth if isinstance(item, dict)}
            pred_set = {self._normalize_string(item.get('env_var')) for item in predictions if isinstance(item, dict)}

        if len(gt_set) == 0:
            if len(pred_set) == 0:
                print("       [SPECIAL] Empty Ground Truth and Empty AI Output. Perfect Match!")
                precision, recall, f1_score = 100.0, 100.0, 100.0
            else:
                precision, recall, f1_score = 0.0, 0.0, 0.0
        else:
            true_positives = len(gt_set.intersection(pred_set))
            false_positives = len(pred_set - gt_set)
            false_negatives = len(gt_set - pred_set)

            precision = (true_positives / (true_positives + false_positives)) * 100 if (true_positives + false_positives) > 0 else 0
            recall = (true_positives / (true_positives + false_negatives)) * 100 if (true_positives + false_negatives) > 0 else 0
            f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print(f"       Precision: {precision:.2f}% | Recall: {recall:.2f}% | F1-Score: {f1_score:.2f}%")
        
        return {
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1_score, 2)
        }