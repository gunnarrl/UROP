# Automatic Code Review for Jupyter Notebook Python Code using LLMS and Ollama

This repository contains a Python script that automates code reviews on Python code extracted from Jupyter Notebooks. It leverages the [Ollama](https://ollama.ai/) LLM to analyze individual functions from your code and provide feedback on potential issues and improvements.

The workflow is as follows:
1. **Extract Python code from Jupyter Notebooks:** Convert your notebooks to Python scripts.
2. **Clean the extracted code:** Remove any Jupyter-specific artifacts (e.g., magic commands, cell markers).
3. **Split the code into functions:** Identify and extract individual function definitions.
4. **Review each function:** Send the function to the Ollama model to perform an automatic code review.
5. **Save the reviews:** Store the review results in an SQLite database.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Extracting Python Code from Jupyter Notebooks](#extracting-python-code-from-jupyter-notebooks)
- [Setting Up Ollama](#setting-up-ollama)
- [Usage](#usage)
- [Code Overview](#code-overview)
- [License](#license)

## Prerequisites

- **Python 3.7+**
- **pip** (for installing Python packages)
- A local installation of **Ollama** and the required model (e.g., `llama3.2`)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your_username/your_repository.git
   cd your_repository
   ```

2. **Install the required Python packages:**

   ```bash
   pip install pandas
   pip install ollama
   ```

   *(Note: `sqlite3` and `ast` are part of the Python Standard Library.)*

## Extracting Python Code from Jupyter Notebooks

Before you run the review script, you need to extract the Python code from your Jupyter Notebooks. You can do this using the `nbconvert` tool, which is included with Jupyter.

For example, to convert a notebook (`notebook.ipynb`) to a Python script, run:

```bash
jupyter nbconvert --to script notebook.ipynb
```

This will generate a `notebook.py` file in the same directory. You may want to rename or move this file (or even convert it to a `.txt` file) so that the script can find and process it. The provided code expects files with a `.txt` extension, so you might need to update the file extension check or convert your `.py` file accordingly.

## Setting Up Ollama

The script uses Ollama to perform automatic code reviews. Follow these steps to install and set up Ollama:

1. **Install Ollama:**

   ```bash
   pip install ollama
   ```

   Alternatively, check the [Ollama documentation](https://ollama.ai/) for the latest installation instructions if you’re using a different platform.

2. **Download the Required Model:**

   The code uses the `llama3.2` model by default. To download this model, use the Ollama CLI:

   ```bash
   ollama pull llama3.2
   ```

   Make sure that the model name in your script matches the model you have downloaded. If you want to use a different model, update the `model` parameter in the code.

## Usage

1. **Configure the Folder Path:**

   In the `__main__` block of the script, update the `folder_path` variable to point to the directory containing your converted Jupyter Notebook files.

   ```python
   folder_path = r"C:\Path\To\Your\Notebooks"
   ```

2. **Run the Script:**

   ```bash
   python your_script.py
   ```

   The script will:
   - Walk through the specified folder to find files with a `.txt` extension.
   - Extract and clean Python code from these files.
   - Identify and extract individual functions.
   - Use Ollama to review each function.
   - Save the review results to an SQLite database (`reviews.db`).

3. **Review the Results:**

   The output SQLite database (`reviews.db`) will contain a table named `code_reviews` with the following columns:
   - `file`: The name of the file.
   - `function_name`: The name of the function reviewed.
   - `line_number`: The exact line number where an issue was detected.
   - `comments`: A description of the issue.
   - `fix`: A suggested fix for the issue.

## Code Overview

- **`clean_code_from_notebook(file_path)`**:  
  Reads a Jupyter Notebook-converted script and removes artifacts like magic commands, cell markers, and unnecessary comments.

- **`split_methods_from_file(file_path)`**:  
  Uses Python’s `ast` module to parse the cleaned source code and extract individual function definitions along with their source code and line numbers.

- **`review_function(function_name, start_line, function_source, model='llama3.2')`**:  
  Sends each function to the Ollama model for review using a carefully formatted prompt. It ensures that the response is valid JSON containing a list of issues (if any).

- **`save_reviews_to_db(df, db_path="reviews.db")`**:  
  Stores the review results in an SQLite database using pandas.

- **`process_file(file_path, model='llama3.2')`**:  
  Combines the steps to clean the file, split it into functions, review each function, and then save the results.
