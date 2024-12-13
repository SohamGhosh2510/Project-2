# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "seaborn",
#   "pandas",
#   "matplotlib",
#   "requests",
#   "numpy"
# ]
# ///

import os
import sys
import subprocess

# Install dependencies inline
def install_dependencies():
    packages = ['pandas', 'seaborn', 'matplotlib', 'requests', 'numpy']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

install_dependencies()



import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests


# Set up AI Proxy
AI_PROXY_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]

if not AIPROXY_TOKEN:
    raise EnvironmentError("AIPROXY_TOKEN environment variable not set.")

headers = {
    "Authorization": f"Bearer {AIPROXY_TOKEN}",
    "Content-Type": "application/json"
}

def send_to_ai_proxy(summary_stats, columns_info, corr):
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": """You are a data scientist analyzing data. Provide in-depth insight on correlation between columns,
        which columns we can omit based on correlation, Presence of outliers based on the summary statistics and other information provided to you.
        Focus your entire analysis mainly on using the numerical data (summary statistics) and correlation matrix provided to you. Draw appropriate conclusion.
        Briefly touch other topics like Suggesting some other forms of analysis that can be done.
        If dates or timepoints are provided, judge which columns may or may not give a significant time series analysis and trends.
        Conclude with how your analysis may prove useful in real world."""},
            {"role": "user", "content": f"Dataset overview: {columns_info}\nSummary: {summary_stats}\nCorrelation matrix info: {corr}"}
        ]
    }
    response = requests.post(AI_PROXY_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def analyze_csv(file_path):
    # Read CSV
    data = pd.read_csv(file_path, encoding='utf-8', encoding_errors='replace')

    # Summary statistics
    summary_stats = data.describe(include='all').to_string()
    columns_info = {col: str(data[col].dtype) for col in data.columns}
    categ_info = {}
    for col in data.columns:
        if data[col].dtype == 'object':
            categ_info[col] = data[col].value_counts().head(5).to_dict()
    print("Summary statistics generated.")

    # Visualization: Correlation heatmap
    correlation_file = file_path[:-4] + "_matrix.png"
    plt.figure(figsize=(8, 7))
    sns.heatmap(data.select_dtypes(include=np.number).corr(), annot=True, cmap='coolwarm')
    plt.title("Correlation Matrix")
    plt.savefig(correlation_file, bbox_inches='tight')
    print(f"Correlation matrix saved as {correlation_file}.")
    corr = data.select_dtypes(include=np.number).corr()

    # Send summary to AI Proxy
    analysis_story = send_to_ai_proxy(summary_stats, columns_info, corr)
    with open('README.md', 'w') as f:
        f.write(analysis_story)

    print("Analysis completed and saved to README.md.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    analyze_csv(csv_file)
