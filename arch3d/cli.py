import argparse
import os
import sys
import subprocess
import yaml
import re
import json
import requests
import pandas as pd
import pathlib
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

    # Arguments for MACRO data
    subparser_macro = subparsers.add_parser("macro", help="Upload macro-scale nucleotide data to ENA")
    subparser_macro.add_argument("-d", "--data", required=True, help="Data directory")
    subparser_macro.add_argument("-m", "--metadata", required=True, help="Metadata table")
    subparser_macro.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_macro.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_macro.add_argument("-p", "--password", required=True, help="EBI Webin password")

    # Arguments for MICRO data
    subparser_micro = subparsers.add_parser("micro", help="Upload micro-scale nucleotide data to ENA")
    subparser_micro.add_argument("-d", "--data", required=True, help="Data directory")
    subparser_micro.add_argument("-m", "--metadata", required=True, help="Metadata table")
    subparser_micro.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_micro.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_micro.add_argument("-p", "--password", required=True, help="EBI Webin password")

    # Arguments for cryosection
    subparser_cryosection = subparsers.add_parser("cryosection", help="Upload cryosection metadata to BioSamples")
    subparser_cryosection.add_argument("-i", "--input", required=True, help="Input metadata table")
    subparser_cryosection.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_cryosection.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_cryosection.add_argument("-p", "--password", required=True, help="EBI Webin password")

    # Arguments for intestinal section
    subparser_section = subparsers.add_parser("section", help="Upload cryosection metadata to BioSamples")
    subparser_section.add_argument("-i", "--input", required=True, help="Input metadata table")
    subparser_section.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_section.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_section.add_argument("-p", "--password", required=True, help="EBI Webin password")

    # Arguments for animal
    subparser_animal = subparsers.add_parser("animal", help="Upload cryosection metadata to BioSamples")
    subparser_animal.add_argument("-i", "--input", required=True, help="Input metadata table")
    subparser_animal.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_animal.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_animal.add_argument("-p", "--password", required=True, help="EBI Webin password")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    ###
    # Nucleotide data
    ###

    input_dir = args.output / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    if args.command == "macro":
        create_secret(args.username, args.password, str(args.output / 'input' / '.secret.yml'))
        create_data_dict(args.metadata, args.data, str(args.output / 'input' / 'input.json'))
        create_run_checklists(args.metadata, {args.output / 'checklists' / 'run'})
        create_experiment_checklists(args.metadata, {args.output / 'checklists' / 'experiment'})
        create_sample_checklists(args.metadata, {args.output / 'checklists' / 'sample'})

    if args.command == "micro":
        create_secret(args.username, args.password, str(args.output / 'input' / '.secret.yml'))
        create_data_dict(args.metadata, args.data, str(args.output / 'input' / 'input.json'))
        create_run_checklists(args.metadata, {args.output / 'checklists' / 'run'})
        create_experiment_checklists(args.metadata, {args.output / 'checklists' / 'experiment'})
        create_microsample_checklists(args.metadata, {args.output / 'checklists' / 'sample'})

    ###
    # Spcimen metadata
    ###

    if args.command == "cryosection":
        process_cryosection(args.input, args.output, args.username, args.password)

    if args.command == "section":
        process_section(args.input, args.output, args.username, args.password)

    if args.command == "animal":
        process_animal(args.input, args.output, args.username, args.password)

if __name__ == "__main__":
    main()
