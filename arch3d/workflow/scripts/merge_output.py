import sys
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

def extract_data(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data = Path(xml_file).parent.name  # Extracts sample folder name (e.g., 'M302118b')

    # Extract values from XML
    experiment_accession = root.find(".//EXPERIMENT").attrib.get("accession", "N/A")
    run_accession = root.find(".//RUN").attrib.get("accession", "N/A")

    sample_element = root.find(".//SAMPLE")
    sample_accession = sample_element.attrib.get("accession", "N/A") if sample_element is not None else "N/A"
    sample = sample_element.attrib.get("alias", "N/A") if sample_element is not None else "N/A"

    biosample_element = root.find(".//SAMPLE/EXT_ID[@type='biosample']")
    biosample_accession = biosample_element.attrib.get("accession", "N/A") if biosample_element is not None else "N/A"

    submission_element = root.find(".//SUBMISSION")
    submission_accession = submission_element.attrib.get("accession", "N/A") if submission_element is not None else "N/A"

    return {
        "data": data,
        "sample": sample,
        "run_accession": run_accession,
        "experiment_accession": experiment_accession,
        "sample_accession": sample_accession,
        "biosample_accession": biosample_accession,
        "submission_accession": submission_accession,
    }

def main():
    input_files = sys.argv[1:-1]  # All input XML files
    output_file = sys.argv[-1]    # Last argument is the output file

    records = [extract_data(xml) for xml in input_files]

    df = pd.DataFrame(records)
    df.to_csv(output_file, sep="\t", index=False)

if __name__ == "__main__":
    main()
