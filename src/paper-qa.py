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
from paperqa.settings import AgentSettings, IndexSettings, ParsingSettings
from pyzotero import zotero

################################################################################
### Functions
################################################################################

def load_config(config_path):
    """Load configuration from a YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def get_zotero_items(library_id, api_key, library_type):
    zot = zotero.Zotero(library_id, library_type, api_key)
    items = zot.everything(zot.top())
    return items, zot

def extract_metadata(items, zot, papers_dir):
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
                    file_location = os.path.join(PAPERS_DIR, file_name)
                    current_files.add(file_name)

                    # Download file if it doesn't exist
                    if not os.path.exists(file_location):
                        download_attachment(zot, att['key'], file_location)

                    metadata.append([file_location, doi, title])

    # Remove files that are no longer in Zotero
    files_to_remove = existing_files - current_files
    for file_name in files_to_remove:
        file_path = os.path.join(PAPERS_DIR, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    return metadata

def download_attachment(zot, attachment_key, file_location):
    if not os.path.exists(file_location):
        zot.dump(attachment_key, file_location)

def save_metadata_csv(metadata, csv_path="manifest.csv"):
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["file_location", "doi", "title"])
        writer.writerows(metadata)

def index_library(settings):
    built_index = build_index(settings = settings)

def query_library(settings, query):

    answer_response = ask(
        query,
        settings = settings
    )

    print(answer_response)

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
        )

    if args.mode == "download":
        print("Retrieving Zotero items...")
        items, zot = get_zotero_items(LIBRARY_ID, API_KEY)

        print("Extracting metadata...")
        metadata = extract_metadata(items, zot, PAPERS_DIR=PAPERS_DIR)

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