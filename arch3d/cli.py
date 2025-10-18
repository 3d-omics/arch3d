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
# arch3d installation path
#####

PACKAGE_DIR = Path(__file__).parent
CONFIG_PATH = PACKAGE_DIR / "workflow" / "config.yaml"

def load_config():
    """Load fixed variables from config.yaml."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return {}

config_vars = load_config()

#####
# Function definitions
#####

def unlock_snakemake(output_dir, profile):
    unlock_command = [
        "/bin/bash", "-c",  # Ensures the module system works properly
        f"module load {config_vars['SNAKEMAKE_MODULE']} && "
        "snakemake "
        f"-s {PACKAGE_DIR / 'workflow' / 'Snakefile'} "
        f"--directory {output_dir} "
        f"--configfile {CONFIG_PATH} "
        f"--workflow-profile {PACKAGE_DIR / 'profile' / profile} "
        f"--unlock"
    ]

    subprocess.run(unlock_command, shell=False, check=True)
    print(f"The output directory {output_dir} has been succesfully unlocked.")

def run_snakemake(workflow, output_dir, connections, profile):
    snakemake_command = [
        "/bin/bash", "-c",
        f"module load {config_vars['SNAKEMAKE_MODULE']} && "
        "snakemake "
        f"-s {PACKAGE_DIR / 'workflow' / 'Snakefile'} "
        f"--directory {output_dir} "
        f"--jobs {connections} "
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

    # Arguments for MACRO sample data
    subparser_macro = subparsers.add_parser("macrosample", help="Upload macro-scale nucleotide data to ENA")
    subparser_macro.add_argument("-d", "--data", required=True, help="Data directory")
    subparser_macro.add_argument("-m", "--metadata", required=True, help="Metadata table")
    subparser_macro.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_macro.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_macro.add_argument("-p", "--password", required=True, help="EBI Webin password")
    subparser_macro.add_argument("-c", "--connections", required=False, default=16, help="Number of concurrent connections for uploading data")

    # Arguments for MICRO sample data
    subparser_micro = subparsers.add_parser("microsample", help="Upload micro-scale nucleotide data to ENA")
    subparser_micro.add_argument("-d", "--data", required=True, help="Data directory")
    subparser_micro.add_argument("-m", "--metadata", required=True, help="Metadata table")
    subparser_micro.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_micro.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_micro.add_argument("-p", "--password", required=True, help="EBI Webin password")
    subparser_micro.add_argument("-c", "--connections", required=False, default=16, help="Number of concurrent connections for uploading data")

    # Arguments for BioSample data
    subparser_animal = subparsers.add_parser("biosample", help="Upload specimen, segment of microsection metadata to BioSamples")
    subparser_animal.add_argument("-i", "--input", required=True, help="Input metadata table")
    subparser_animal.add_argument("-o", "--output", required=True, type=pathlib.Path, help="Output directory")
    subparser_animal.add_argument("-u", "--username", required=True, help="EBI Webin username. e.g, Webin-12345")
    subparser_animal.add_argument("-p", "--password", required=True, help="EBI Webin password")

    # Arguments for unlock
    subparser_unlock = subparsers.add_parser("unlock", help="Unlock output directory")
    subparser_unlock.add_argument("-o", "--output", required=False, type=pathlib.Path, default=os.getcwd(), help="Output directory. Default is the directory from which drakkar is called.")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.command == "macrosample":
        input_dir = args.output / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        create_secret(args.username, args.password, str(Path(args.output).resolve() / 'input' / '.secret.yml'))
        create_data_dict(args.metadata, args.data, str(Path(args.output).resolve() / 'input' / 'input.json'))
        create_run_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'run'))
        create_experiment_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'experiment'))
        create_sample_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'sample'))
        run_snakemake(args.command, Path(args.output).resolve(),args.connections, 'slurm')

    if args.command == "microsample":
        input_dir = args.output / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        create_secret(args.username, args.password, str(Path(args.output).resolve() / 'input' / '.secret.yml'))
        create_data_dict(args.metadata, args.data, str(Path(args.output).resolve() / 'input' / 'input.json'))
        create_run_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'run'))
        create_experiment_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'experiment'))
        create_microsample_checklists(args.metadata, str(Path(args.output).resolve() / 'checklists' / 'sample'))
        run_snakemake(args.command, Path(args.output).resolve(),args.connections, 'slurm')

    if args.command == "biosample":
        process_biosample(args.input, args.output, args.username, args.password)

    ###
    # Unlock
    ###

    if args.command == "unlock":
        unlock_snakemake(Path(args.output).resolve(), 'slurm')

if __name__ == "__main__":
    main()
