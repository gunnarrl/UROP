import os
import json
import sqlite3
import subprocess
import pandas as pd

# Directory containing the .txt files.
directory = r"C:\Users\gunna\OneDrive\Documents\coding_projects\UROP\Jupyter_Notebooks\test_notebooks"
# Name of the SQLite database file to create.
db_filename = "code_reviews.db"

# Base prompt text for the code review.
base_prompt = (
    "You are a code review assistant. Given the following code, please review it "
    "line by line and output a JSON array. Each element in the array should be an object "
    "with keys: 'line_number', 'comment', and 'suggested_fix'. If no issues are found on a line, "
    "you can leave the comment and suggested_fix empty. Here is the code:\n\n"
)

# List to store review entries.
reviews = []

# Process each .txt file in the directory.
for filename in os.listdir(directory):
    if filename.lower().endswith(".txt"):
        filepath = os.path.join(directory, filename)
        print(f"Processing file: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                code_content = file.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            continue

        # Construct the prompt by appending the code content.
        prompt = base_prompt + code_content

        # Build the ollama command.
        # According to your input, the prompt is passed as the final positional argument.
        command = ["ollama", "run", "llama3.2", prompt]

        try:
            # Run the command and capture its output.
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            print(f"Output from model for file {filename}:\n{output}\n")
        except subprocess.CalledProcessError as e:
            print(f"Error running ollama command for file {filename}: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            continue

        # Parse the JSON output.
        try:
            review_data = json.loads(output)
            if not isinstance(review_data, list):
                print(f"Unexpected JSON format for file {filename}: Expected a list, got {type(review_data)}")
                continue
        except json.JSONDecodeError as e:
            print(f"JSON decode error for file {filename}: {e}")
            continue

        # Add each review entry from the model to our list.
        for entry in review_data:
            line_number = entry.get("line_number")
            comment = entry.get("comment", "")
            suggested_fix = entry.get("suggested_fix", "")
            reviews.append({
                "file": filename,
                "line_number": line_number,
                "comment": comment,
                "suggested_fix": suggested_fix
            })

# Create a pandas DataFrame from the reviews.
df = pd.DataFrame(reviews)
print("Final DataFrame:")
print(df)

# Save the DataFrame to an SQLite database.
try:
    conn = sqlite3.connect(db_filename)
    df.to_sql("code_reviews", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"Data successfully saved to database: {db_filename}")
except Exception as e:
    print(f"Error saving data to database: {e}")
