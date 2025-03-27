################################################################################
### paper-qa.py
### Copyright (c) 2025, Joshua J Hamilton
################################################################################

################################################################################
### Import packages
################################################################################

import argparse
import asyncio
import csv
import os
import pandas as pd
import yaml
from paperqa import Settings, ask
from paperqa.agents import build_index
from paperqa.settings import AgentSettings, AnswerSettings, IndexSettings, ParsingSettings
from pyzotero import zotero

################################################################################
### Functions
################################################################################

def load_config(config_path):
    """
    Loads a YAML configuration file from the given path.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Parsed configuration as a dictionary.
    """
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def get_zotero_items(library_id, api_key, library_type):
    """
    Retrieves all items from a Zotero library.

    Args:
        library_id (str): Zotero library ID.
        api_key (str): Zotero API key.
        library_type (str): Type of Zotero library (e.g., 'user' or 'group').

    Returns:
        tuple: A tuple containing the list of items and the Zotero client instance.
    """
    zot = zotero.Zotero(library_id, library_type, api_key)
    items = zot.everything(zot.top())
    return items, zot

def extract_metadata(items, zot, papers_dir):
    """
    Extracts metadata from Zotero items, downloads associated files, and updates
    the local metadata to reflect changes in the Zotero library.

    Args:
        items (list): List of Zotero items.
        zot (zotero.Zotero): Zotero client instance.
        papers_dir (str): Directory to store downloaded papers.

    Returns:
        list: Metadata for each item, including file location, DOI, and title.

    Description:
        - Downloads attachments for items in the Zotero library if they do not
          already exist locally.
        - Tracks the current files in Zotero and compares them with the existing
          files in the local directory.
        - Removes files from the local directory that are no longer present in
          the Zotero library.
        - Updates the metadata list with the file location, DOI, and title for
          each item in the Zotero library.
    """
    metadata = []
    existing_files = set(os.listdir(papers_dir)) if os.path.exists(papers_dir) else set()

    if not os.path.exists(papers_dir):
        os.makedirs(papers_dir)

    current_files = set()  # Track files currently in Zotero

    for item in items:
        if 'data' in item:
            doi = item['data'].get('DOI', 'N/A')
            title = item['data'].get('title', 'N/A')

            # Find attachment
            attachments = zot.children(item['key'])
            for att in attachments:
                if 'filename' in att['data']:
                    file_name = att['data']['filename']
                    file_location = os.path.join(papers_dir, file_name)
                    current_files.add(file_name)

                    # Download file if it doesn't exist
                    if not os.path.exists(file_location):
                        download_attachment(zot, att['key'], file_location)

                    metadata.append([file_location, doi, title])

    # Remove files that are no longer in Zotero
    files_to_remove = existing_files - current_files
    for file_name in files_to_remove:
        file_path = os.path.join(papers_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    return metadata

def download_attachment(zot, attachment_key, file_location):
    """
    Downloads an attachment from Zotero to the specified file location.

    Args:
        zot (zotero.Zotero): Zotero client instance.
        attachment_key (str): Key of the attachment to download.
        file_location (str): Path to save the downloaded file.

    Returns:
        None
    """
    if not os.path.exists(file_location):
        zot.dump(attachment_key, file_location)

def save_metadata_csv(metadata, csv_path="manifest.csv"):
    """
    Saves metadata to a CSV file.

    Args:
        metadata (list): List of metadata entries (for each file: file location, DOI, and title)
        csv_path (str): Path to the CSV file (default: "manifest.csv").

    Returns:
        None
    """
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["file_location", "doi", "title"])
        writer.writerows(metadata)

def index_library(settings):
    """
    Builds a PaperQA index of documents using the provided settings.

    Args:
        settings (Settings): PaperQA settings for indexing.

    Returns:
        None
    """
    built_index = build_index(settings = settings)

def query_library(settings, query):
    """
    Queries the indexed documents using PaperQA, using the provided settings and query.

    Args:
        settings (Settings): PaperQA settings for querying.
        query (str): Query string to search the indexed documents.

    Returns:
        None
    """
    answer_response = ask(
        query,
        settings = settings
    )

################################################################################
### Main function
################################################################################

def main():
    parser = argparse.ArgumentParser(description="PaperQA Utility")
    parser.add_argument("mode", choices=["download", "index", "query"], help="Mode to run the script in: 'download', 'index', or 'query'")
    parser.add_argument("--config", default="config/paper-qa.yml", help="Path to the configuration file (default: config/config.yml)")
    parser.add_argument("--query", help = "Query to ask the model")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    LIBRARY_ID = config["zotero_library_id"]
    API_KEY = config["zotero_api_key"]
    LIBRARY_TYPE = config["zotero_library_type"]
    INDEX_DIR = config["paperqa_index_dir"]
    PAPERS_DIR = config["paperqa_papers_dir"]
    MANIFEST_PATH = config["paperqa_manifest_path"]

    # Define the settings for PaperQA
    settings = Settings(
            llm_config={"rate_limit": {"gpt-4o-2024-11-20": "30000 per 1 minute"}},
            summary_llm_config={"rate_limit": {"gpt-4o-2024-11-20": "30000 per 1 minute"}},
            agent=AgentSettings(
                index=IndexSettings(
                    paper_directory=PAPERS_DIR,
                    manifest_file=MANIFEST_PATH,
                    index_directory=INDEX_DIR,
                )
            ),
            parsing=ParsingSettings(
                use_doc_details=False
            ),
            answer=AnswerSettings(
                answer_length="Around 1000 words",
            )
        )

    if args.mode == "download":
        print("Retrieving Zotero items...")
        items, zot = get_zotero_items(LIBRARY_ID, API_KEY, LIBRARY_TYPE)

        print("Extracting metadata...")
        metadata = extract_metadata(items, zot, PAPERS_DIR)

        print("Saving metadata to manifest...")
        save_metadata_csv(metadata, csv_path=MANIFEST_PATH)

    elif args.mode == "index":
        print("Indexing documents with PaperQA...")
        index_library(settings)

    elif args.mode == "query":
        if not args.query:
            print("Error: You must provide a query using the --query argument in 'query' mode.")
            return

        print(f"Querying the indexed documents with: {args.query}")
        query_library(settings, args.query)

if __name__ == "__main__":
    main()