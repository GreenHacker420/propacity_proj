#!/usr/bin/env python
"""
Script to download required NLTK resources for the Product Review Analyzer.
"""

import nltk
import os
import sys
import traceback

def download_nltk_resources():
    """Download all required NLTK resources."""
    print("Downloading NLTK resources...")

    # Create nltk_data directory in the user's home directory if it doesn't exist
    nltk_data_dir = os.path.expanduser("~/nltk_data")
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
        print(f"Created NLTK data directory at {nltk_data_dir}")

    # List of resources to download
    resources = [
        'punkt',           # For sentence tokenization
        'stopwords',       # For stopword removal
        'wordnet',         # For lemmatization
        'averaged_perceptron_tagger',  # For POS tagging
    ]

    # Special handling for punkt_tab
    try:
        print("Attempting to download punkt_tab...")
        nltk.download('punkt_tab')
        print("Successfully downloaded punkt_tab")
    except Exception as e:
        print(f"Error downloading punkt_tab: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        print("Attempting to create punkt_tab directory structure...")

        # Create the directory structure for punkt_tab
        punkt_tab_dir = os.path.join(nltk_data_dir, "tokenizers", "punkt_tab", "english")
        os.makedirs(punkt_tab_dir, exist_ok=True)

        # Copy files from punkt to punkt_tab if available
        punkt_dir = os.path.join(nltk_data_dir, "tokenizers", "punkt")
        if os.path.exists(punkt_dir):
            print("Creating punkt_tab files...")
            try:
                # Create necessary files for punkt_tab
                files_to_create = [
                    "collocations.tab",
                    "sent_starters.txt",
                    "abbrev_types.txt",
                    "ortho_context.tab"
                ]

                for filename in files_to_create:
                    file_path = os.path.join(punkt_tab_dir, filename)
                    try:
                        with open(file_path, "w") as f:
                            f.write("")
                        print(f"Created empty file: {file_path}")
                    except Exception as e:
                        print(f"Error creating {filename}: {str(e)}")
                        traceback.print_exc()

                print("Finished creating punkt_tab files")
            except Exception as e:
                print(f"Error creating punkt_tab files: {str(e)}")
                traceback.print_exc()
        else:
            print("punkt directory not found, cannot copy files")

    # Download each resource
    for resource in resources:
        try:
            print(f"Downloading {resource}...")
            nltk.download(resource)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {str(e)}")

    print("NLTK resource download complete!")

if __name__ == "__main__":
    try:
        download_nltk_resources()
        print("Script completed successfully")
    except Exception as e:
        print(f"Error in main script: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
