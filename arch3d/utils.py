import argparse
import os
import sys
import subprocess
import yaml
import re
import json
import requests
import pandas as pd
from pathlib import Path
from collections import defaultdict

######
# nucleotide
######

# Create secret file with username and password for ena-upload-cli
def create_secret(username: str, password: str, output_file: str):
    data = {
        'username': username,
        'password': password
    }

    with open(output_file, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

# Create separate run checklist files for each sample
def create_run_checklists(experiment_checklist: str, output_dir: str):
    df = pd.read_csv(input_tsv, sep='\t')
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        alias = row['alias']
        output_file = os.path.join(output_dir, f"{alias}.tsv")
        transformed_data = [
            [alias, alias, row['forward_file'], 'fastq'],
            [alias, alias, row['reverse_file'], 'fastq']
        ]
        output_df = pd.DataFrame(transformed_data, columns=['alias', 'experiment_alias', 'file_name', 'file_type'])
        output_df.to_csv(output_file, sep='\t', index=False)

# Create separate experiment checklist files for each sample
def create_experiment_checklists(experiment_checklist: str, output_dir: str):
    df = pd.read_csv(input_tsv, sep='\t')
    df = df[['alias','title','study_alias','sample_alias','design_description','library_name','library_strategy','library_source','library_selection','library_layout','insert_size','library_construction_protocol','platform','instrument_model']]
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        alias = row['alias']
        output_file = os.path.join(output_dir, f"{alias}.tsv")
        output_df = pd.DataFrame([row])
        output_df.to_csv(output_file, sep='\t', index=False)

# Create separate sample checklist files for each sample
def create_sample_checklists(sample_checklist: str, output_dir: str):
    df = pd.read_csv(input_tsv, sep='\t')
    df = df[['alias','title','taxon_id','sample_description','sample collection method','project name','collection date','geographic location (latitude)','geographic location (longitude)','geographic location (region and locality)','broad-scale environmental context','local environmental context','environmental medium','geographic location (country and/or sea)','host common name','host subject id','host taxid','host body site','host life stage','host sex']]
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        alias = row['alias']
        output_file = os.path.join(output_dir, f"{alias}.tsv")
        output_df = pd.DataFrame([row])
        output_df.to_csv(output_file, sep='\t', index=False)

def create_data_dict(metadata: str, directory: str, output_json: str):
    df = pd.read_csv(metadata, sep='\t')
    sample_dict = {
        row['alias']: [
            os.path.abspath(os.path.join(directory, row['forward_file'])),
            os.path.abspath(os.path.join(directory, row['reverse_file']))
        ]
        for _, row in df.iterrows()
    }
    with open(output_json, 'w') as json_file:
        json.dump(sample_dict, json_file, indent=4)

######
# sample
######

# API Endpoints
AUTH_URL = "https://www.ebi.ac.uk/ena/submit/webin/auth/token"
API_URL = "https://www.ebi.ac.uk/biosamples/samples"

def get_token(username, password):
    """Obtain a temporary authentication token from EBI API."""
    payload = {
        "authRealms": ["ENA"],
        "username": username,
        "password": password
    }
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json"
    }

    response = requests.post(AUTH_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.text.strip()  # Extract token as a string
    else:
        print(f"Error fetching token: HTTP {response.status_code}")
        print(f"Response content: {response.text}")
        sys.exit(1)

def post_sample(sample_json, token):
    """Send POST request to create a sample."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(sample_json))
    return response

def update_sample(updated_json, accession, token):
    """Send PUT request to update a sample with relationships."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    update_url = f"{API_URL}/{accession}"
    response = requests.put(update_url, headers=headers, data=json.dumps(updated_json))
    return response

def save_json(data, output_dir, filename):
    """Save JSON data to a file."""
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {filepath}")

def process_tsv(input_tsv, output_dir, username, password):
    """Reads a TSV file, obtains a token, processes rows, posts to API, and updates relationships."""

    # Check if input file exists
    if not os.path.exists(input_tsv):
        print(f"Error: The input file '{input_tsv}' does not exist.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get API token
    token = get_token(username, password)
    print("Successfully obtained authentication token.")

    # Read TSV
    df = pd.read_csv(input_tsv, sep="\t")  # Use tab-separated values

    # Ensure "accession" column exists in TSV
    if "accession" not in df.columns:
        df["accession"] = ""

    for index, row in df.iterrows():
        sample_name = row["name"]
        accession = row["accession"] if pd.notna(row["accession"]) and row["accession"] != "" else None

        # Construct sample JSON payload (either for submission or update)
        sample_json = {
            "name": row["name"],
            "taxId": str(row["taxId"]),
            "release": row["release"],
            "webinSubmissionAccountId": row["webinSubmissionAccountId"],
            "characteristics": {}
        }

        # Process characteristics
        for col in df.columns:
            if col.startswith("characteristics@"):
                char_key = col.split("@")[1]  # Extract field name
                char_value = row[col]
                if pd.notna(char_value):  # Ignore empty fields
                    sample_json["characteristics"][char_key] = [{"text": str(char_value)}]

        if accession:
            # If accession exists, only update the sample
            print(f"Updating existing sample: {accession}")

            sample_name_updated = f"{sample_name}_updated"
            updated_json = {
                "accession": accession,
                "name": sample_name_updated,
                "release": row["release"],
                "webinSubmissionAccountId": row["webinSubmissionAccountId"],
                "taxId": str(row["taxId"]),
                "characteristics": sample_json["characteristics"],
                "relationships": []
            }

            # Process child samples (formerly derived_from) - FIXED ORDER
            if "child_samples" in row and pd.notna(row["child_samples"]):
                child_accessions = [child.strip() for child in str(row["child_samples"]).split(",")]
                for child in child_accessions:
                    updated_json["relationships"].append({
                        "source": child,  # Child sample (previously was parent)
                        "type": "derived from",
                        "target": accession  # Parent sample (current sample)
                    })

            # API Call: Update existing sample
            update_response = update_sample(updated_json, accession, token)

            if update_response.status_code == 200:
                update_response_json = update_response.json()
                save_json(update_response_json, output_dir, f"{sample_name}_update.json")
            else:
                save_json({"error": update_response.text}, output_dir, f"{sample_name}_update.json")

        else:
            # If accession does not exist, create a new BioSample
            print(f"Creating new sample: {sample_name}")

            response = post_sample(sample_json, token)

            #If initial request is successful
            if response.status_code == 201:  # Success
                response_json = response.json()
                accession = response_json.get("accession")
                df.at[index, "accession"] = accession  # Store accession in DataFrame

                # Save original response JSON
                save_json(response_json, output_dir, f"{sample_name}_original.json")

                # Now update the sample with relationships
                sample_name_updated = f"{sample_name}_updated"
                updated_json = {
                    "accession": accession,
                    "name": sample_name_updated,
                    "release": row["release"],
                    "webinSubmissionAccountId": row["webinSubmissionAccountId"],
                    "taxId": str(row["taxId"]),
                    "characteristics": sample_json["characteristics"],
                    "relationships": []
                }

                # Process child samples - FIXED ORDER
                if "child_samples" in row and pd.notna(row["child_samples"]):
                    child_accessions = [child.strip() for child in str(row["child_samples"]).split(",")]
                    for child in child_accessions:
                        updated_json["relationships"].append({
                            "source": child,  # Child sample
                            "type": "derived from",
                            "target": accession  # Parent sample
                        })

                # Second API Call: Update sample with relationships
                update_response = update_sample(updated_json, accession, token)

                if update_response.status_code == 200:
                    update_response_json = update_response.json()
                    save_json(update_response_json, output_dir, f"{sample_name}_update.json")
                else:
                    save_json({"error": update_response.text}, output_dir, f"{sample_name}_update.json")

            #If initial request yields an error
            else:
                 save_json({"error": response.text}, output_dir, f"{sample_name}.json")

    # Save updated TSV with accession numbers
    updated_tsv_path = os.path.join(output_dir, "updated_" + os.path.basename(input_tsv))
    df.to_csv(updated_tsv_path, sep="\t", index=False)
    print(f"Updated TSV saved: {updated_tsv_path}")
