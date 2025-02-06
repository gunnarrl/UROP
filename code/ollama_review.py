import ollama
import os
import json
import sys


def review_file_rolling(file_path, model='llama3.2'):
    """
    Reviews the file in rolling 5-line windows.
    For each window, sends the snippet to the Ollama model for code review,
    and collects the model's JSON output along with the window range.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError):
        print(f"Skipping {file_path} due to unreadable characters or missing file.", file=sys.stderr)
        return None

    filename = os.path.basename(file_path)
    window_size = 5
    total_lines = len(lines)
    review_results = {
        "file": filename,
        "reviews": []  # Each element will include window info and the model's response
    }

    # Process rolling windows: lines 1-5, 2-6, etc.
    for i in range(total_lines - window_size + 1):
        start_line = i + 1
        end_line = i + window_size
        snippet = "".join(lines[i:i + window_size])

        # Print progress to stderr so that stdout remains a pure JSON output.
        print(f"reviewing lines {start_line}-{end_line} of file {filename}", file=sys.stderr)

        while True:  # Retry loop for ensuring JSON-parsable output
            prompt = f"""
You are a professional Python developer reviewing the following snippet of code.
Identify issues in the code, mentioning the line numbers (relative to the snippet) where the issues occur.
If there are no issues, return an empty list for issues. If there are issues, provide a comment explaining the problem.

Return the output as strictly JSON in the following format (the JSON must be valid and properly formatted):
{{
    "file": "{filename}",
    "window": {{
        "start_line": {start_line},
        "end_line": {end_line}
    }},
    "issues": [
        {{"line": <line_number>, "comment": "<issue description>"}}  
    ]
}}
Code:
```python
{snippet}
```
            """

            # Send request to Ollama model
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )

            content = response['message']['content']

            try:
                review_data = json.loads(content)
                break  # Successfully parsed, exit retry loop
            except json.JSONDecodeError:
                print(f"Error parsing model response for {filename} (lines {start_line}-{end_line}). Retrying...",
                      file=sys.stderr)
                prompt += "\nEnsure that the output is strictly JSON formatted with no additional text."

        review_results["reviews"].append(review_data)

    return review_results


def review_folder(folder_path, model='llama3.2'):
    """
    Runs the rolling 5-line code review on all .txt files in the given folder
    and outputs a single JSON formatted string with all results.
    """
    aggregated_results = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                result = review_file_rolling(file_path, model)
                if result:
                    aggregated_results.append(result)

    # Convert aggregated results to a JSON formatted string
    final_output = json.dumps(aggregated_results, indent=4)
    return final_output


if __name__ == "__main__":
    folder_path = r"C:\Users\gunna\OneDrive\Documents\coding_projects\UROP\Jupyter_Notebooks\test_notebooks"
    output = review_folder(folder_path)
    print(output)
