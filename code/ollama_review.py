import ollama
import os
import json
import sqlite3
import ast
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


def split_methods_from_file(file_path):
    """
    Extracts individual function/method definitions from a cleaned Python script.
    Returns a list of tuples (function_name, start_line, function_source_code).
    """
    source = clean_code_from_notebook(file_path)

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        print(f"Skipping {file_path} due to syntax errors.")
        return []

    functions = []
    lines = source.splitlines(True)  # Preserve line endings

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line = node.end_lineno
            func_source = "".join(lines[start_line - 1:end_line])
            functions.append((node.name, start_line, func_source))

    return functions


def review_function(function_name, start_line, function_source, model='llama3.2'):
    """
    Sends a function to the Ollama model for code review.
    Retries until a valid JSON response is received.
    """
    while True:
        prompt = f"""
You are reviewing the following Python function. Identify issues and suggest fixes.
Return a JSON object in this format:
{{
    "function": "{function_name}",
    "issues": [
        {{"line": <line_number>, "comment": "<issue description>", "fix": "<suggested fix>"}}
    ]
}}

Code:
```python
{function_source}
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

        # Adjust the line numbers to match the full file
        for issue in review_data.get("issues", []):
            issue["line"] = issue.get("line", start_line) + start_line - 1
            issue["comment"] = issue.get("comment", "No comment provided.")
            issue["fix"] = issue.get("fix", "No fix suggested.")

        return review_data


def save_reviews_to_db(df, db_path="reviews.db"):
    """
    Saves review data to an SQLite database using pandas.
    """
    conn = sqlite3.connect(db_path)
    df.to_sql("code_reviews", conn, if_exists="replace", index=False)
    conn.close()


def process_file(file_path, model='llama3.2'):
    """
    Extracts functions from a file, reviews them, and saves results in a DataFrame.
    """
    functions = split_methods_from_file(file_path)
    review_data = []

    for function_name, start_line, function_source in functions:
        review = review_function(function_name, start_line, function_source, model)
        if review:
            for issue in review.get("issues", []):
                review_data.append([
                    file_path, function_name, issue["line"], issue["comment"], issue["fix"]
                ])

    # The DataFrame includes a 'line_number' column for where the comment was made.
    df = pd.DataFrame(review_data, columns=["file", "function_name", "line_number", "comments", "fix"])
    save_reviews_to_db(df)


if __name__ == "__main__":
    folder_path = r"C:\\Users\\gunna\\OneDrive\\Documents\\coding_projects\\UROP\\Jupyter_Notebooks\\test_notebooks"  # Update with actual path

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                process_file(file_path)
