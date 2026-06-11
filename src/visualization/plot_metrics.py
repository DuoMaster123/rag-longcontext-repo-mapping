import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import warnings

# Suppress unnecessary Seaborn/Pandas warnings
warnings.filterwarnings("ignore")

class ExperimentVisualizer:
    def __init__(self, output_dir: str = "data/outputs/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure professional academic theme
        sns.set_theme(style="whitegrid")
        plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif'})

    def plot_f1_scores(self):
        print("[INFO] Generating F1-Score comparison charts for all repositories...")
        
        # Experimental dataset for the 3 project levels
        data = {
            "Repository": ["FastAPI (Python)", "FastAPI (Python)", "FastAPI (Python)", 
                           "NestJS (TypeScript)", "NestJS (TypeScript)", "NestJS (TypeScript)",
                           "Spring Boot (Java)", "Spring Boot (Java)", "Spring Boot (Java)"],
            "Task": ["API", "DB", "ENV", "API", "DB", "ENV", "API", "DB", "ENV"],
            "RAG (GPT-4o)": [16.67, 66.67, 0.00, 32.00, 88.89, 0.00, 0.00, 0.00, 0.00],
            "Long-Context (Gemini)": [16.67, 80.00, 100.00, 0.00, 100.00, 0.00, 0.00, 90.91, 100.00]
        }
        
        df = pd.DataFrame(data)
        df_melted = pd.melt(df, id_vars=["Repository", "Task"], 
                            value_vars=["RAG (GPT-4o)", "Long-Context (Gemini)"],
                            var_name="Architecture", value_name="F1-Score")

        repos = df['Repository'].unique()
        
        for repo in repos:
            repo_data = df_melted[df_melted['Repository'] == repo]
            
            plt.figure(figsize=(10, 6))
            ax = sns.barplot(x="Task", y="F1-Score", hue="Architecture", data=repo_data, palette=["#3498db", "#e74c3c"])
            
            plt.title(f"F1-Score Comparison: {repo}", pad=20, fontweight='bold')
            plt.ylim(0, 115)
            plt.ylabel("F1-Score (%)")
            plt.xlabel("Extraction Task")
            plt.legend(title="AI Architecture", loc='upper left')
            
            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f%%', padding=3)
                
            # Safely handle file naming
            safe_repo_name = repo.split()[0].lower()
            file_name = f"f1_comparison_{safe_repo_name}.png"
            output_path = self.output_dir / file_name
            plt.tight_layout()
            plt.savefig(output_path, dpi=300)
            plt.close()
            print(f"[SUCCESS] Saved chart to {output_path}")

    def plot_hallucination_trap(self):
        print("[INFO] Generating Hallucination (False Positives) chart for NestJS ENV...")
        architectures = ["RAG (GPT-4o)", "Long-Context (Gemini)"]
        false_positives = [3, 9]
        
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=architectures, y=false_positives, hue=architectures, palette=["#95a5a6", "#c0392b"], legend=False)
        
        plt.title("Hallucination Trap: Imagined ENV Variables (NestJS)", pad=20, fontweight='bold')
        plt.ylabel("Number of False Positives")
        plt.ylim(0, 12)
        
        for container in ax.containers:
            ax.bar_label(container, fmt='%d vars', padding=3, color='black', fontweight='bold')
            
        output_path = self.output_dir / "hallucination_trap_nestjs.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"[SUCCESS] Saved chart to {output_path}")

    def plot_precision_recall(self):
        print("[INFO] Generating Precision vs Recall breakdown charts for Database Tasks...")
        
        # Detailed DB extraction data across repositories
        data_db = {
            "Metric": ["Precision", "Recall", "F1-Score", "Precision", "Recall", "F1-Score",
                       "Precision", "Recall", "F1-Score", "Precision", "Recall", "F1-Score",
                       "Precision", "Recall", "F1-Score", "Precision", "Recall", "F1-Score"],
            "Score": [100.0, 50.0, 66.7, 66.7, 100.0, 80.0,  # FastAPI
                      100.0, 80.0, 88.9, 100.0, 100.0, 100.0, # NestJS
                      0.0, 0.0, 0.0, 83.3, 100.0, 90.9], # Spring Boot
            "Architecture": ["RAG (GPT-4o)", "RAG (GPT-4o)", "RAG (GPT-4o)", 
                             "Long-Context (Gemini)", "Long-Context (Gemini)", "Long-Context (Gemini)",
                             "RAG (GPT-4o)", "RAG (GPT-4o)", "RAG (GPT-4o)", 
                             "Long-Context (Gemini)", "Long-Context (Gemini)", "Long-Context (Gemini)",
                             "RAG (GPT-4o)", "RAG (GPT-4o)", "RAG (GPT-4o)", 
                             "Long-Context (Gemini)", "Long-Context (Gemini)", "Long-Context (Gemini)"],
            "Repository": ["FastAPI", "FastAPI", "FastAPI", "FastAPI", "FastAPI", "FastAPI",
                           "NestJS", "NestJS", "NestJS", "NestJS", "NestJS", "NestJS",
                           "Spring Boot", "Spring Boot", "Spring Boot", "Spring Boot", "Spring Boot", "Spring Boot"]
        }
        df_db = pd.DataFrame(data_db)
        
        repos = df_db['Repository'].unique()
        for repo in repos:
            plt.figure(figsize=(10, 6))
            repo_data = df_db[df_db['Repository'] == repo]
            
            ax = sns.barplot(x="Metric", y="Score", hue="Architecture", data=repo_data, palette=["#2ecc71", "#f39c12"])
            plt.title(f"Detailed Metrics Breakdown: Database Task ({repo})", pad=20, fontweight='bold')
            plt.ylim(0, 115)
            plt.ylabel("Percentage (%)")
            plt.legend(title="AI Architecture", loc='upper left')
            
            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f%%', padding=3)
                
            safe_repo_name = repo.replace(" ", "_").lower()
            file_name = f"precision_recall_db_{safe_repo_name}.png"
            output_path = self.output_dir / file_name
            plt.tight_layout()
            plt.savefig(output_path, dpi=300)
            plt.close()
            print(f"[SUCCESS] Saved detailed chart to {output_path}")

if __name__ == "__main__":
    print("\n[INFO] INITIALIZING DATA VISUALIZATION MODULE")
    
    visualizer = ExperimentVisualizer()
    visualizer.plot_f1_scores()
    visualizer.plot_hallucination_trap()
    visualizer.plot_precision_recall()
    
    print("\n[SUCCESS] ALL CHARTS GENERATED. READY FOR REPORTING.")