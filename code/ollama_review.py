import ollama
import os
import json


def review_code(file_path, model='llama3.2'):
    """Sends a Python file to an Ollama model for code review."""

    try:
        # Read the file contents
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except (UnicodeDecodeError, FileNotFoundError):
        print(f"Skipping {file_path} due to unreadable characters or missing file.")
        return None

    # Define the prompt
    prompt = f"""
    You are a professional Python developer reviewing the following code.
    Identify issues in the code, mentioning the line numbers where the issues occur.
    For each issue, provide a comment explaining the problem and suggest a fix.

    Code:
    ```python
    {code}
    ```

    Return the output as JSON in the following format:
    {{
        "file": "{os.path.basename(file_path)}",
        "issues": [
            {{"line": <line_number>, "comment": "<issue description>", "fix": "<suggested fix>"}},
            ...
        ]
    }}
    """

    # Send request to Ollama
    response = ollama.chat(
        model=model,
        messages=[
            {'role': 'user', 'content': prompt}
        ]
    )

    # Extract response content
    content = response['message']['content']

    try:
        # Convert response to JSON format
        issues_data = json.loads(content)
    except json.JSONDecodeError:
        print(f"Error parsing model response for {file_path}. Raw output:", content)
        return {"file": os.path.basename(file_path), "issues": []}

    return issues_data


def review_folder(folder_path, output_json="code_review_results.json", model='llama3.2'):
    """Runs code review on all Python files in the given folder and saves results to a JSON file."""
    results = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(f"Reviewing {file_path}...")
                issues_data = review_code(file_path, model)
                if issues_data:
                    results.append(issues_data)

                    for issue in issues_data["issues"]:
                        print(f"File: {issues_data['file']}")
                        print(f"Line {issue['line']}: {issue['comment']}")
                        print(f"Suggested Fix: {issue['fix']}\n")

    # Save results to a JSON file
    with open(output_json, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Review results saved to {output_json}")


# Example usage
if __name__ == "__main__":
    folder_path = r"C:\\Users\\gunna\\OneDrive\\Documents\\coding_projects\\UROP\\Jupyter_Notebooks\\converted_notebooks"
    review_folder(folder_path)