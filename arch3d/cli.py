
def main():
    parser = argparse.ArgumentParser(
        description="arch3d: Python software for archiving 3D'omics data and metadata in public databases",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available workflows")

    # Define subcommands for each workflow
    subparser_complete = subparsers.add_parser("nucleotide", help="Upload nucleotide data to ENA")
    subparser_complete.add_argument("-i", "--input", required=True, help="Input directory")
    subparser_preprocessing.add_argument("-f", "--file", required=False, help="Sample detail file (required if no input directory is provided)")
    subparser_complete.add_argument("-p", "--profile", required=False, default="slurm", help="Snakemake profile. Default is slurm")

    subparser_preprocessing = subparsers.add_parser("sample", help="Upload sample metadata to BioSamples")
    subparser_preprocessing.add_argument("-i", "--input", required=False, help="Input directory (required if no sample detail file is provided)")
    subparser_preprocessing.add_argument("-f", "--file", required=False, help="Sample detail file (required if no input directory is provided)")
    subparser_preprocessing.add_argument("-p", "--profile", required=False, default="slurm", help="Snakemake profile. Default is slurm")

    args = parser.parse_args()

if __name__ == "__main__":
    main()
