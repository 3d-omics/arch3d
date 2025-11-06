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
from datetime import datetime
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
def create_run_checklists(metadata: str, output_dir: str):
    df = pd.read_csv(metadata, sep=',')
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        alias = row['alias']
        output_file = os.path.join(output_dir, f"{alias}.tsv")
        transformed_data = [
            [alias, alias, row['forward_filename'], 'fastq'],
            [alias, alias, row['reverse_filename'], 'fastq']
        ]
        output_df = pd.DataFrame(transformed_data, columns=['alias', 'experiment_alias', 'file_name', 'file_type'])
        output_df.to_csv(output_file, sep='\t', index=False)

# Create separate experiment checklist files for each sample
def create_experiment_checklists(metadata: str, output_dir: str):
    df = pd.read_csv(metadata, sep=',')
    df = df[['alias','title','study_alias','sample_alias','design_description','library_name','library_strategy','library_source','library_selection','library_layout','insert_size','library_construction_protocol','platform','instrument_model']]
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        alias = row['alias']
        output_file = os.path.join(output_dir, f"{alias}.tsv")
        output_df = pd.DataFrame([row])
        output_df.to_csv(output_file, sep='\t', index=False)

# Create separate sample checklist files for each sample
def create_sample_checklists(metadata: str, output_dir: str):
    df = pd.read_csv(metadata, sep=',')
    df = df[['alias','sample_alias','taxon_id','sample_description','sample collection method','project name','collection date','geographic location (latitude)','geographic location (longitude)','geographic location (region and locality)','broad-scale environmental context','local environmental context','environmental medium','geographic location (country and/or sea)','host common name','host subject id','host taxid','host body site','host life stage','host sex']]
    df = df.rename(columns={'alias': 'filename'})
    df = df.rename(columns={'sample_alias': 'alias'})
    df['title'] = df['alias']
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        filename = row['filename']
        output_file = os.path.join(output_dir, f"{filename}.tsv")
        output_df = pd.DataFrame([row.drop('filename')])
        output_df.to_csv(output_file, sep='\t', index=False)

def create_microsample_checklists(metadata: str, output_dir: str):
    df = pd.read_csv(metadata, sep=',')
    df = df[['alias','sample_alias','taxon_id','sample_description','sample collection method','project name','collection date','geographic location (latitude)','geographic location (longitude)','geographic location (region and locality)','broad-scale environmental context','local environmental context','environmental medium','geographic location (country and/or sea)','host common name','host subject id','host taxid','host body site','host life stage','host sex','sample_attribute[cryosection]','sample_attribute[Xcoord]','sample_attribute[Ycoord]','sample_attribute[Xpixel]','sample_attribute[Ypixel]','sample_attribute[size]','sample_attribute[buffer]','sample_attribute[sampletype]']]
    df = df.rename(columns={'alias': 'filename'})
    df = df.rename(columns={'sample_alias': 'alias'})
    df['title'] = df['alias']
    os.makedirs(output_dir, exist_ok=True)
    for _, row in df.iterrows():
        filename = row['filename']
        output_file = os.path.join(output_dir, f"{filename}.tsv")
        output_df = pd.DataFrame([row.drop('filename')])
        output_df.to_csv(output_file, sep='\t', index=False)

def create_data_dict(metadata: str, directory: str, output_json: str):
    df = pd.read_csv(metadata, sep=',')
    sample_dict = {
        row['alias']: [
            os.path.abspath(os.path.join(directory, row['forward_filename'])),
            os.path.abspath(os.path.join(directory, row['reverse_filename']))
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
BIOSAMPLE_URL = "https://www.ebi.ac.uk/biosamples/samples"
STRUCTUREDDATA_URL = "https://www.ebi.ac.uk/biosamples/structureddata"

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
    response = requests.post(BIOSAMPLE_URL, headers=headers, data=json.dumps(sample_json))
    return response

def update_sample(updated_json, accession, token):
    """Send PUT request to update a sample with relationships."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    update_url = f"{BIOSAMPLE_URL}/{accession}"
    response = requests.put(update_url, headers=headers, data=json.dumps(updated_json))
    return response

def update_structured_data(accession, structured_data_json, token):
    """Add/update structured data for a given BioSample accession."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    url = f"{STRUCTUREDDATA_URL}/{accession}"
    response = requests.put(url, headers=headers, data=json.dumps(structured_data_json))
    return response

def save_json(data, output_dir, filename):
    """Save JSON data to a file."""
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"    Saved: {filepath}")

# BioSample types

def process_biosample(input_csv, output_dir, username, password):
    """Reads a CSV file, obtains a token, processes rows, posts to API, and updates relationships."""

    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Error: The input file '{input_csv}' does not exist.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Ensure output/json directory exists
    json_dir = output_dir / "json"
    os.makedirs(json_dir, exist_ok=True)

    # Get API token
    token = get_token(username, password)
    print("Successfully obtained authentication token.")

    # Read CSV
    df = pd.read_csv(input_csv, sep=",")  # Use tab-separated values

    # Ensure "accession" column exists in CSV
    if "accession" not in df.columns:
        df["accession"] = ""

    for index, row in df.iterrows():
        sample_name = row["name"]
        accession = row["accession"] if pd.notna(row["accession"]) and row["accession"] != "" else None

        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M")

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

        # Process structured data
        structured_raw = {}
        for col in df.columns:
            if col.startswith("data@"):
                parts = col.split("@")
                if len(parts) == 4:
                    _, data_type, label, value_type = parts
                    structured_raw.setdefault(data_type, {}).setdefault(label, {})[value_type] = row[col]

        # Now format into data_payload with {"metric": ..., "value": ...} structure
        data_payload = []
        for data_type, entries in structured_raw.items():
            content = []
            for label, pair in entries.items():
                metric = pair.get("metric")
                value = pair.get("value")
                link = pair.get("link")
                if pd.notna(metric) and pd.notna(value):
                    content.append({
                        "metric": {"value": metric, "iri": None},
                        "value": {"value": value, "iri": link if pd.notna(link) else None}
                    })
            if content:
                data_payload.append({
                    "domain": None,
                    "webinSubmissionAccountId": row["webinSubmissionAccountId"],
                    "type": data_type,
                    "schema": None,
                    "content": content
                })

        # Add or edit BioSample

        if accession:
            # If accession exists, only update the sample
            print(f"Updating existing BioSample: {sample_name} ({accession})")

            updated_json = {
                "accession": accession,
                "name": row["name"],
                "release": row["release"],
                "webinSubmissionAccountId": row["webinSubmissionAccountId"],
                "taxId": str(row["taxId"]),
                "characteristics": sample_json["characteristics"],
                "relationships": []
            }

            # Process child samples
            if "child_samples" in row and pd.notna(row["child_samples"]):
                child_accessions = [child.strip() for child in str(row["child_samples"]).split(",")]
                for child in child_accessions:
                    updated_json["relationships"].append({
                        "source": child,
                        "type": "derived from",
                        "target": accession 
                    })

            # Process parent samples
            if "parent_sample" in row and pd.notna(row["parent_sample"]):
                parent_accessions = [parent.strip() for parent in str(row["parent_sample"]).split(",")]
                for parent in parent_accessions:
                    updated_json["relationships"].append({
                        "source": accession, 
                        "type": "derived from",
                        "target": parent 
                    })

            # API Call: Update existing sample
            update_response = update_sample(updated_json, accession, token)

            if update_response.status_code == 200:
                update_response_json = update_response.json()
                save_json(update_response_json, json_dir, f"{sample_name}_{timestamp}.json")
            else:
                save_json({"error": update_response.text}, json_dir, f"{sample_name}_{timestamp}.json")

        else:
            # If accession does not exist, create a new BioSample
            print(f"Creating new BioSample: {sample_name}")

            response = post_sample(sample_json, token)

            #If initial request is successful
            if response.status_code == 201:  # Success
                response_json = response.json()
                accession = response_json.get("accession")
                df["accession"] = df["accession"].astype(str)
                df.at[index, "accession"] = accession  # Store accession in DataFrame

                # Save original response JSON
                #save_json(response_json, output_dir, f"{sample_name}.json")

                # Now update the sample with relationships
                updated_json = {
                    "accession": accession,
                    "name": row["name"],
                    "release": row["release"],
                    "webinSubmissionAccountId": row["webinSubmissionAccountId"],
                    "taxId": str(row["taxId"]),
                    "characteristics": sample_json["characteristics"],
                    "relationships": []
                }

                # Process child samples - FIXED ORDER
                if "child_samples" in row and pd.notna(row["child_samples"]):
                    child_accessions = [child.strip() for child in str(row["child_samples"]).split(",") if child.strip()]
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
                    save_json(update_response_json, json_dir, f"{sample_name}_{timestamp}.json")
                else:
                    save_json({"error": update_response.text}, json_dir, f"{sample_name}_{timestamp}.json")

            #If initial request yields an error
            else:
                 save_json({"error": response.text}, json_dir, f"{sample_name}_{timestamp}.json")

        # Add or edit Structured data
        if data_payload:
            print(f"    Updating structured data")
            timestamp_iso = datetime.utcnow().isoformat(timespec='microseconds') + "Z"
            structured_payload = {
                "accession": accession,
                "create": timestamp_iso,
                "update": timestamp_iso,
                "data": data_payload
            }
            structured_response = update_structured_data(accession, structured_payload, token)
            if structured_response.status_code in [200, 201]:
                save_json(structured_response.json(), json_dir, f"{sample_name}_data_{timestamp}.json")
            else:
                print(f"❌ Structured data update failed for {accession}: {structured_response.status_code}")
                save_json({"error": structured_response.text}, json_dir, f"{sample_name}_structured_error_{timestamp}.json")

    # Save updated CSV with accession numbers
    updated_csv_path = os.path.join(output_dir, "updated_" + os.path.basename(input_csv))
    df.to_csv(updated_csv_path, sep=",", index=False)
    print(f"Updated CSV (with accession numbers) saved: {updated_csv_path}")
