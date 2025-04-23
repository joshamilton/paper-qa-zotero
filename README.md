# Paper-QA-Zotero: A tool to query your Zotero library using PaperQA2
Copyright (c) 2025, Joshua J. Hamilton  
Email: <joshamilton@gmail.com>  
URL: <https://www.linkedin.com/in/joshamilton/>  
URL: <https://github.com/joshamilton/>  
All rights reserved.

## Overview
This repository contains a tool to query your Zotero library using [PaperQA2](https://github.com/Future-House/paper-qa). The tool allows you to download documents from your Zotero library, index them, and query them.

The Zotero library is downloaded using PyZotero, and PaperQA2 is used to index and query the documents. The tool is designed to be run from the command line and uses a configuration file to specify the necessary parameters.

When downloading documents from your Zotero library, the tool will check for an existing manifest file and only download new documents.

## Setup
### Clone the Repository and Install Dependencies
```bash
# clone the repository
git clone git@github.com:joshamilton/paper-qa-zotero.git
cd paper-qa-zotero

# install mamba
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# install dependencies
mamba env create -f config/paper-qa.yml

# activate the environment
mamba activate paper-qa
```

## Optional Setup: Local LLMs
By default, the application uses OpenAI's API. However, any LiteLLM compatible model can be configured to use with PaperQA2. This utility currently supports the following models:

LLMs:
- **TBD**

Embedding models:
- `mxbai-embed-large`
- `nomic-embed-text`

Models are made available through [Ollama](https://ollama.com/), which should be installed using [Homebrew](https://brew.sh/). Ollama is a local LLM server that allows you to run LLMs on your local machine. **Note**: While Ollama can be installed via conda, it does not utilize the GPU.

```bash
# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# install ollama
brew install ollama
```

To use local LLMs, download the models:
```bash
ollama serve
ollama pull llama3.3
ollama pull <embedding model>
```

### Configure the Application
Create a `config/config.yml` file to specify the necessary parameters for the application.

#### Example `config/config.yml`:
```yaml
openai_api_key: "YOUR_API_KEY"

paperqa_index_dir: "YOUR_INDEX_DIR"
paperqa_papers_dir: "YOUR_PAPERS_DIR"
paperqa_manifest_path: "YOUR_MANIFEST_PATH"

zotero_library_id: "YOUR_LIBRARY_ID"
zotero_api_key: "YOUR_API_KEY"
zotero_library_type: "user"  # Use "group" for personal libraries
```
- **openai_api_key**: Your OpenAI API key.

- **paperqa_index_dir**: Directory where the index will be stored.
- **paperqa_papers_dir**: Directory where downloaded papers will be stored.
- **paperqa_manifest_path**: Path to the manifest file that tracks metadata for the papers.

- **zotero_ibrary_id**: Your Zotero library ID. For group libraries, find it by hovering over the settings link on your Zotero group page.
- **zotero_api_key**: Your Zotero API key with read access to the library.
- **zotero_library_type**: Set to `"user"` for personal libraries or `"group"` for group libraries.



## Usage
### Download Zotero library
To download the documents from your Zotero library, run the following command:

```bash
python src/paper-qa.py download --config config/config.yml
```

This will:
1. Retrieve items from your Zotero library.
2. Download associated attachments (e.g., PDFs) to the `papers_dir`.
3. Save metadata to the `manifest_path`. This [manifest file](https://github.com/Future-House/paper-qa#manifest-files) lets PaperQA avoid LLM usage for querying such as DOIs.

**Optionally, inspect the manifest file and add any missing metadata (e.g., DOIs) manually.**

### Index the Documents Library
To index the downloaded documents for querying, run:

```bash
python src/paper-qa.py index --config config/config.yml
```

This will create an index in the `index_dir` specified in your configuration file.

### Query the Indexed Library
To query the indexed documents, use the `query` mode with the `--query` argument:

```bash
python src/paper-qa.py query --config config/config.yml --query "Your question here"
```

For example:
```bash
python src/paper-qa.py query --config config/config.yml --query "What are the four canonical DNA bases?"
```

The application will return an answer based on the indexed documents.

### Notes
- Ensure that the `config/config.yml` file is properly configured before running any commands.
- Sensitive information like `api_key` should not be committed to version control. Add `config/config.yml` to `.gitignore` to prevent accidental commits.

---

## Background: Benchmarking Ollama LLMs
I benchmarked various LLMs available through Ollama to determine their performance on my local machine (Apple M4 Pro chip with 12‑core CPU, 16‑core GPU, 48GB unified memory). LLMs were selected based on their size: PaperQA2 recommends using models with 7B parameters or greater, but the models also must fit within memory (48 GB).

1. **Run the Benchmarking Script**:
   Use the `ollama-benchmark.py` script to evaluate the performance of different models.
   ```bash
   python src/ollama-benchmark.py
   ```
   This script will:
   - Download and test a list of models defined in the script.
   - Measure runtime and speed (tokens per second) on a single query.
   - Save the results to `results/ollama_benchmark.csv`.

**Note**: The models themselves take up 320 GB of storage space, and require about 5 hours to download. Running the benchmark script will take about 35 minutes.

2. **Inspect Results**:
   Review the benchmarking results in the CSV file to exclude models that are too slow for practical use.

3. **Select Models**:
   All of the 70b parameter models had acceptable performance, returning answers in one minute or less. Therefore, the following models were selected for benchmarkign with PaperQA2:
    - deepseek-llm:67b
    - llama2:70b
    - llama3:70b
    - llama3.1:70b
    - llama3.3:70b

## Background: Benchmarking Ollama LLMs within PaperQA2

1. **Prepare the test dataset**:
The test dataset is a collection of primary research articles on the topic of microbial genome assembly. Papers can be accessed upon request via the Zotero group [LjECTEXaBa](https://www.zotero.org/groups/5961949/ljectexaba).

2. **Run the Benchmarking Script**:
   Use the `paperqa-benchmark.py` script to evaluate the performance of different models.
   ```bash
   python src/paperqa-benchmark.py
   ```
   This script will:
   - Download the Zotero library.
   - Test each model using each of two embedding models:
      - `mxbai-embed-large`
      - `nomic-embed-text`
      - Index the library
      - Query the library using a set of questions
      - Measure runtime and speed (tokens per second) on a single query.
   - Save the results to `results/paperqa_benchmark.csv`.

**Note**: Need to reindex dataset with each model. Dealing with timeout issues at the moment.

### License
This project is licensed under the MIT License.