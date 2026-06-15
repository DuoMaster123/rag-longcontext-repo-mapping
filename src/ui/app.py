import streamlit as st
import json
import os
import sys
import re
import plotly.express as px
import pandas as pd
from pathlib import Path
from PIL import Image

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from master_runner import run_live_analysis
    backend_err = ""
except Exception as e:
    import traceback
    run_live_analysis = None
    backend_err = traceback.format_exc()

# Page configuration
st.set_page_config(
    page_title="Architecture Evaluator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimalist and professional UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Fira+Code:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #111827; 
        background-color: #f9fafb; 
    }

    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #111827 !important;
    }
    
    h1 { font-size: 1.75rem !important; margin-bottom: 0.5rem !important; }
    h3 { font-size: 1.1rem !important; margin-top: 1.5rem !important; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem; }

    p { color: #4b5563; font-size: 0.95rem; }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 0 1.5rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    .sidebar-brand-text {
        font-size: 1.1rem;
        font-weight: 600;
        color: #111827;
    }
    
    .sidebar-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: #374151;
        margin-bottom: 0.5rem;
    }
    
    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981; 
    }

    .chart-container {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem !important;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
        padding: 0.75rem 0 !important;
        background: transparent !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2563eb !important; 
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #2563eb !important;
        height: 2px !important;
    }

    .json-header {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        border-left: 3px solid;
        margin-bottom: 1rem;
        background-color: #ffffff;
        box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
    }
    
    .header-gt { border-left-color: #10b981; color: #065f46; } 
    .header-rag { border-left-color: #3b82f6; color: #1e3a8a; } 
    .header-lc { border-left-color: #8b5cf6; color: #78350f; } 

    pre, code {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.85rem !important;
    }
    
    .stJson {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
    }

    .custom-alert {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 1rem;
        margin: 1.5rem 0;
    }
    
    .custom-alert-title {
        color: #991b1b;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    
    .custom-alert-body {
        color: #b91c1c;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Utility functions
@st.cache_data
def load_json(file_path: str):
    path = Path(file_path)
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, str):
                    match = re.search(r'\[.*\]', data, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except json.JSONDecodeError:
                            pass
                return data
        except Exception:
            return {"error": "Invalid JSON format."}
    return {"error": f"File not found: {file_path}"}

# Sidebar navigation
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            <span class="sidebar-brand-text">Arch Evaluator</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Application Mode</div>', unsafe_allow_html=True)
    app_mode = st.radio(
        "Mode", 
        ["Research & Evaluation", "Live Analyzer"], 
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    selected_repo = None
    if app_mode == "Research & Evaluation":
        st.markdown('<div class="sidebar-label">Repository</div>', unsafe_allow_html=True)
        selected_repo = st.selectbox(
            "Select Repository",
            options=["FastAPI (Python)", "NestJS (TypeScript)", "Spring Boot (Java)"],
            label_visibility="collapsed"
        )
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">System Status</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="status-item"><div class="status-indicator"></div> Vector DB Connected</div>
        <div class="status-item"><div class="status-indicator"></div> GPT-4o Ready</div>
        <div class="status-item"><div class="status-indicator"></div> Gemini 2.5 Ready</div>
    """, unsafe_allow_html=True)

# Main content routing
if app_mode == "Research & Evaluation":
    repo_mapping = {
        "FastAPI (Python)": {"folder": "fastapi_crud_async", "prefix": "fastapi_crud", "chart_suffix": "fastapi", "out_infix": ""},
        "NestJS (TypeScript)": {"folder": "nestjs_realworld", "prefix": "nestjs_realworld", "chart_suffix": "nestjs", "out_infix": "nestjs_"},
        "Spring Boot (Java)": {"folder": "spring_realworld", "prefix": "spring_realworld", "chart_suffix": "spring", "out_infix": "spring_"}
    }
    current_repo = repo_mapping[selected_repo]

    st.markdown(f"<h1>{selected_repo}</h1>", unsafe_allow_html=True)
    st.markdown("<p>Evaluating architecture extraction capabilities: <b>RAG (GPT-4o)</b> vs. <b>Long-Context (Gemini 2.5)</b>.</p>", unsafe_allow_html=True)

    tab_analytics, tab_data = st.tabs(["Performance Analytics", "Raw JSON Explorer"])

    with tab_analytics:
        st.markdown("### Evaluation Metrics")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown('<div class="sidebar-label">F1-Score Overview</div>', unsafe_allow_html=True)
            f1_chart_path = Path(f"data/charts/f1_comparison_{current_repo['chart_suffix']}.png")
            if f1_chart_path.exists():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.image(Image.open(f1_chart_path), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Chart missing.")

        with col_chart2:
            st.markdown('<div class="sidebar-label">Precision & Recall (Database)</div>', unsafe_allow_html=True)
            pr_suffix = "spring_boot" if selected_repo == "Spring Boot (Java)" else current_repo['chart_suffix']
            pr_chart_path = Path(f"data/charts/precision_recall_db_{pr_suffix}.png")
            if pr_chart_path.exists():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.image(Image.open(pr_chart_path), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                 st.error("Chart missing.")

        base_dir = Path(f"data/{current_repo['folder']}")
        rag_api_path = base_dir / "outputs" / "rag_api_pred.json"
        rag_data = load_json(str(rag_api_path))
        
        if isinstance(rag_data, list) and len(rag_data) == 0:
            st.markdown("""
                <div class="custom-alert">
                    <div class="custom-alert-title">Systemic Failure Detected (RAG Architecture)</div>
                    <div class="custom-alert-body">The RAG model returned empty extractions. This indicates severe context fragmentation and format hallucination.</div>
                </div>
            """, unsafe_allow_html=True)

        if selected_repo == "NestJS (TypeScript)":
            st.markdown("""
                <div class="custom-alert" style="background-color: #fffbeb; border-color: #fef3c7; border-left-color: #f59e0b;">
                    <div class="custom-alert-title" style="color: #92400e;">Hallucination Detected (Environment Variables)</div>
                    <div class="custom-alert-body" style="color: #b45309;">The Long-Context model (Gemini) hallucinated non-existent variables.</div>
                </div>
            """, unsafe_allow_html=True)
            
            hal_chart_path = Path("data/charts/hallucination_trap_nestjs.png")
            if hal_chart_path.exists():
                 col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
                 with col_h2:
                     st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                     st.image(Image.open(hal_chart_path), use_container_width=True)
                     st.markdown('</div>', unsafe_allow_html=True)

    with tab_data:
        st.markdown("### Extraction Results")
        
        selected_task = st.radio("Target:", options=["API Endpoints", "Database Models", "Environment Variables"], horizontal=True, label_visibility="collapsed")
        task_key = "api" if "API" in selected_task else "db" if "Database" in selected_task else "env"

        base_dir = Path(f"data/{current_repo['folder']}")
        gt_path = base_dir / "ground_truth" / f"{current_repo['prefix']}_{task_key}.json"
        
        out_infix = current_repo.get("out_infix", "")
        
        std_rag = base_dir / "outputs" / f"rag_{task_key}_pred.json"
        std_lc = base_dir / "outputs" / f"lc_{task_key}_pred.json"
        legacy_rag = base_dir / "outputs" / f"rag_{out_infix}{task_key}_pred.json"
        legacy_lc = base_dir / "outputs" / f"lc_{out_infix}{task_key}_pred.json"
        
        rag_path = std_rag if std_rag.exists() else legacy_rag
        lc_path = std_lc if std_lc.exists() else legacy_lc

        st.markdown("<br>", unsafe_allow_html=True)
        
        expand_json = st.toggle("Expand all JSON blocks", value=False)
        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

        col_gt, col_rag, col_lc = st.columns(3)

        with col_gt:
            st.markdown('<div class="json-header header-gt">Ground Truth</div>', unsafe_allow_html=True)
            st.json(load_json(str(gt_path)), expanded=expand_json)

        with col_rag:
            st.markdown('<div class="json-header header-rag">RAG (GPT-4o)</div>', unsafe_allow_html=True)
            st.json(load_json(str(rag_path)), expanded=expand_json)

        with col_lc:
            st.markdown('<div class="json-header header-lc">Long-Context (Gemini 2.5)</div>', unsafe_allow_html=True)
            st.json(load_json(str(lc_path)), expanded=expand_json)

elif app_mode == "Live Analyzer":
    st.markdown("<h1>Live Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p>Dynamically clone and evaluate any supported GitHub repository.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repository")
    
    if st.button("Start Analysis"):
        if not repo_url:
            st.warning("Please provide a valid GitHub URL.")
        elif run_live_analysis is None:
            st.error("🚨 Khởi động Backend thất bại! Lỗi chi tiết:")
            st.code(backend_err)
        else:
            with st.spinner("Cloning repository, building Vector DB, and running AI extraction. This may take a few minutes..."):
                try:
                    # Persist results in session state to prevent data loss on page rerun
                    st.session_state['live_result'] = run_live_analysis(repo_url)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # Render dashboard elements if analysis data exists in session state
    if 'live_result' in st.session_state:
        result_meta = st.session_state['live_result']
        st.success(f"Analysis complete for **{result_meta['repo_name']}** ({result_meta['framework']})")
        
        st.markdown("### Live Performance Metrics")
        metrics = result_meta.get("metrics", {})
        
        if metrics:
            chart_data = {
                "Task": [],
                "RAG (GPT-4o)": [],
                "Long-Context (Gemini 2.5)": []
            }
            
            # Map metric metrics to the visualization dataframe
            for task_name, scores in metrics.items():
                rag_data = scores.get("RAG") if scores.get("RAG") else {}
                lc_data = scores.get("LC") if scores.get("LC") else {}
                
                chart_data["Task"].append(task_name)
                chart_data["RAG (GPT-4o)"].append(rag_data.get("f1_score", 0.0))
                chart_data["Long-Context (Gemini 2.5)"].append(lc_data.get("f1_score", 0.0))
                
            df = pd.DataFrame(chart_data).set_index("Task")
            df_melted = pd.DataFrame(chart_data).melt(id_vars="Task", var_name="Architecture", value_name="F1-Score")
            
            # Build and configure the Plotly bar chart
            fig = px.bar(
                df_melted, 
                x="Task", 
                y="F1-Score", 
                color="Architecture", 
                barmode="group",
                color_discrete_sequence=["#3b82f6", "#8b5cf6"],
                text="F1-Score" 
            )
            
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                yaxis=dict(range=[0, 115]),
                margin=dict(t=20, b=0, l=0, r=0),
                legend_title_text=None,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
            
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-label">F1-Score Comparison (%)</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) 
            
            with st.expander("View Raw Metric Data"):
                st.dataframe(df, use_container_width=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Live Extraction Results")
        
        expand_json_live = st.toggle("Expand all JSON blocks", value=False, key="live_expand")
        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

        base_dir = Path(result_meta['base_dir'])
        gt_dir = base_dir / "ground_truth"
        out_dir = base_dir / "outputs"
        
        task_tabs = st.tabs(["API Endpoints", "Database Models", "Environment Variables"])
        tasks_info = [("API", "api"), ("DB", "db"), ("ENV", "env")]
        
        # Display individual JSON comparison blocks within tabs
        for tab, (task_name, task_key) in zip(task_tabs, tasks_info):
            with tab:
                gt_path = gt_dir / f"{result_meta['repo_name']}_{task_key}.json"
                rag_path = out_dir / f"rag_{task_key}_pred.json"
                lc_path = out_dir / f"lc_{task_key}_pred.json"
                
                col_gt, col_rag, col_lc = st.columns(3)
                
                with col_gt:
                    st.markdown('<div class="json-header header-gt">Auto Ground Truth (Parser)</div>', unsafe_allow_html=True)
                    st.json(load_json(str(gt_path)), expanded=expand_json_live)
                    
                with col_rag:
                    st.markdown('<div class="json-header header-rag">RAG (GPT-4o)</div>', unsafe_allow_html=True)
                    st.json(load_json(str(rag_path)), expanded=expand_json_live)
                    
                with col_lc:
                    st.markdown('<div class="json-header header-lc">Long-Context (Gemini 2.5)</div>', unsafe_allow_html=True)
                    st.json(load_json(str(lc_path)), expanded=expand_json_live)

st.markdown("<hr style='margin-top: 3rem;'><p style='text-align:center; color:#9ca3af; font-size:0.8rem;'>AI Software Engineering Research</p>", unsafe_allow_html=True)