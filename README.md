# Live Analyzer: Automated Repository Mapping

This is the proof-of-concept prototype for my Bachelor Thesis: "Research on RAG and Long-Context Architectures for Automated Repository Mapping". 

The tool evaluates and compares how different AI architectures (GPT-4o using RAG vs. Gemini 2.5 Flash using Long-Context) understand complex codebases and extract software architecture components like API endpoints, Database schemas, and Environment variables.

## Key Features

* **AST Ground Truth Generation:** Uses Tree-sitter to parse source code and establish a deterministic, human-bias-free baseline.
* **RAG Pipeline:** Implements a sliding-window chunking strategy with ChromaDB and GPT-4o for semantic retrieval.
* **Long-Context Pipeline:** Ingests the entire repository directly into Gemini 2.5 Flash to test holistic comprehension.
* **Interactive Dashboard:** Built with Streamlit and Plotly to visualize Precision, Recall, and F1-Scores in real-time, featuring a side-by-side JSON comparison.
* **Fault Tolerance:** Includes API key rotation and request debouncing to handle cloud provider rate limits smoothly.

## Local Setup

1. Clone the repository and navigate to the project folder.
2. Install dependencies:
   pip install -r requirements.txt

3. Create a `.env` file in the root directory and configure your API keys:
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key

## Usage

Start the Streamlit server:
   streamlit run app.py

Once the dashboard loads in your browser, paste any public GitHub repository URL into the input field to trigger the analysis pipeline.