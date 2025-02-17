import ollama
import os
import json
import sqlite3
import pandas as pd


def clean_code_from_notebook(file_path):
    """
    Reads a Jupyter Notebook-converted script file and removes remnants of notebook execution.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove Jupyter-specific artifacts (magic commands, cell markers, blank lines)
    cleaned_lines = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped.startswith(('%', '!', '# In[')):
            cleaned_lines.append(line)

    return "".join(cleaned_lines)


def review_file(file_source, model='llama3.2'):
    """
    Sends the entire file to the Ollama model for code review.
    Retries until a valid JSON response is received.
    """
    while True:
        prompt = f"""
You are an expert Python code reviewer. I will provide you with a Python script, and your task is to identify issues in the code and suggest improvements. Please analyze the entire file and output a JSON object that strictly adheres to the following format without any additional text, commentary, or markdown formatting:

{{
  "issues": [
    {{
      "line": <line_number>, 
      "comment": "<issue description>", 
      "fix": "<suggested fix>"
    }}
  ]
}}

Requirements:
1. The "issues" key must be an array. Each element in the array must be a dictionary with exactly three keys:
   - "line": an integer representing the exact line number in the file where the issue occurs.
   - "comment": a string that clearly describes the issue.
   - "fix": a string that provides a suggested fix for the issue.
2. If there are no issues found, return "issues": [].
3. Do not include any additional keys or extra text outside of the JSON object.
4. Output only the valid JSON object, without any markdown code blocks or additional formatting.

Below is the Python script to review:

```python
{file_source}
```
        """

        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )

        content = response['message']['content']

        try:
            review_data = json.loads(content)
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            continue

        return review_data


def save_reviews_to_db(df, db_path="file_reviews.db"):
    """
    Saves review data to an SQLite database using pandas.
    """
    conn = sqlite3.connect(db_path)
    df.to_sql("code_reviews", conn, if_exists="append", index=False)
    conn.close()


def process_file(file_path, model='llama3.2'):
    """
    Reads the file, reviews it, and saves results in a DataFrame.
    """
    notebook_name = os.path.basename(file_path)
    file_source = clean_code_from_notebook(file_path)
    review = review_file(file_source, model)

    review_data = []
    issues = review.get("issues", [])

    if not isinstance(issues, list):
        print("Unexpected response format:", issues)  # Debugging output
        return  # Skip saving if the data is malformed

    for issue in issues:
        if isinstance(issue, dict):  # Ensure it's a dictionary before accessing keys
            review_data.append([
                notebook_name, issue.get("line", -1),  # Default to -1 if missing
                issue.get("comment", "No comment provided."),
                issue.get("fix", "No fix suggested.")
            ])
        else:
            print("Skipping unexpected issue format:", issue)  # Debugging output

    # The DataFrame includes a 'line_number' column for where the comment was made.
    df = pd.DataFrame(review_data, columns=["file", "line_number", "comments", "fix"])
    save_reviews_to_db(df)


if __name__ == "__main__":
    db_path = "file_reviews.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    folder_path = r"C:\\Users\\gunna\\OneDrive\\Documents\\coding_projects\\UROP\\Jupyter_Notebooks\\test_notebooks"  # Update with actual path

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                process_file(file_path)
