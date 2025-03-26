# Paper-QA-Zotero: A tool to query your Zotero library using PaperQA2
Copyright (c) 2024, Joshua J. Hamilton  
Email: <joshamilton@gmail.com>  
URL: <https://www.linkedin.com/in/joshamilton/>  
URL: <https://github.com/joshamilton/>  
All rights reserved.

## Overview
This repository contains a tool to query your Zotero library using [PaperQA2](https://github.com/Future-House/paper-qa). The tool allows you to download documents from your Zotero library, index them, and query them.

The Zotero library is downloaded using PyZotero, and PaperQA2 is used to index and query the documents. The tool is designed to be run from the command line and uses a configuration file to specify the necessary parameters.

When downloading documents from your Zotero library, the tool will check for an existing manifest file and only download new documents.

## Setup
### Clone the Repository
```bash
git clone git@github.com:joshamilton/paper-qa-zotero.git
cd paper-qa-zotero
```

### Setup Mamba
```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

### Environment Setup
Installs paper-qa and dependencies required by paper-qa-zotero.
```bash
mamba env create -f config/paper-qa.yml
mamba activate paper-qa
```

### Configure the Application
Create a `config/config.yml` file to specify the necessary parameters for the application.

#### Example `config/config.yml`:
```yaml
zotero_library_id: "YOUR_LIBRARY_ID"
zotero_api_key: "YOUR_API_KEY"
library_type: "user"  # Use "group" for personal libraries
index_dir: "pari_bio/index"
papers_dir: "pari_bio/papers"
manifest_path: "pari_bio/manifest.csv"
```

- **library_id**: Your Zotero library ID. For group libraries, find it by hovering over the settings link on your Zotero group page.
- **zotero_api_key**: Your Zotero API key with read access to the library.
- **zotero_library_type**: Set to `"user"` for personal libraries or `"group"` for group libraries.
- **paperqa_index_dir**: Directory where the index will be stored.
- **paperqa_papers_dir**: Directory where downloaded papers will be stored.
- **paperqa_manifest_path**: Path to the manifest file that tracks metadata for the papers.

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

### License
This project is licensed under the MIT License.