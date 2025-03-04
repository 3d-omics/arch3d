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
from arch3d.utils import *

#####
# Function definitions
#####

def nucleotide_snakemake(workflow, output_dir, profile):
    snakemake_command = [
        "/bin/bash", "-c",  # Ensures the module system works properly
        f"module load {config_vars['SNAKEMAKE_MODULE']} && "
        "snakemake "
        f"-s {PACKAGE_DIR / 'workflow' / 'Snakefile'} "
        f"--directory {output_dir} "
        f"--workflow-profile {PACKAGE_DIR / 'profile' / profile} "
        f"--configfile {CONFIG_PATH} "
        f"--config package_dir={PACKAGE_DIR} workflow={workflow} output_dir={output_dir}"
    ]
    subprocess.run(snakemake_command, shell=False, check=True)

#####
# Arch3d execution
#####

def main():
    parser = argparse.ArgumentParser(
        description="arch3d: Python software for archiving 3D'omics data and metadata in public databases",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available workflows")

    # Define subcommands for each workflow
    subparser_nucleotide = subparsers.add_parser("nucleotide", help="Upload nucleotide data to ENA")
    subparser_nucleotide.add_argument("-d", "--data", required=True, help="Data directory")
    subparser_nucleotide.add_argument("-m", "--metadata", required=True, help="Metadata table")
    subparser_nucleotide.add_argument("-o", "--output", required=True, help="Output directory")
    subparser_nucleotide.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_nucleotide.add_argument("-p", "--password", required=True, help="EBI Webin password")

    subparser_sample = subparsers.add_parser("sample", help="Upload sample metadata to BioSamples")
    subparser_sample.add_argument("-i", "--input", required=True, help="Input metadata table")
    subparser_sample.add_argument("-o", "--output", required=True, help="Output directory")
    subparser_sample.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_sample.add_argument("-p", "--password", required=True, help="EBI Webin password")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    ###
    # Nucleotide
    ###

    if args.command == "nucleotide":
        create_secret(args.username, args.password, {args.output / 'input' / '.secret.yml'})
        create_data_dict(args.metadata, args.data, {args.output / 'input' / 'input.json'})
        create_run_checklists(args.metadata, {args.output / 'checklists' / 'run'})
        create_experiment_checklists(args.metadata, {args.output / 'checklists' / 'experiment'})
        create_sample_checklists(args.metadata, {args.output / 'checklists' / 'sample'})

    ###
    # Sample
    ###

    if args.command == "sample":
        process_tsv(args.input, args.output, args.username, args.password)

if __name__ == "__main__":
    main()
