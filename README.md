# arch3d

**Arch3d** is a Python software for archiving 3D'omics data and metadata in the public EBI databases ENA, BioSamples, Bioarchive Image and Metabolights.

## Installation

**Arch3d** can be installed using pip directly from this Github repository. You might need to create a conda environment to ensure all dependencies are accessible.

```
conda create -n arch3d python=3.12 pip -y

conda activate arch3d

pip install git+https://github.com/3d-omics/arch3d.git

#if you need to uninstall it:
pip uninstall arch3d -y
```

## Usage

**Arch3d** currently has two main operation modes. The commands `arch3d macro` and `arch3d micro` upload macro-scale and micro-scale data and metadata to the **European Nucleotide Archive (ENA)**, respectively, while the command `arch3d biosample` uploads sample metadata to the database **BioSamples**. Both databases are connected and the data and samples at different levels are connected through BioSamples accessions.

The most straightforward usage is to:

1. Create the Bioproject accession (not included here)
2. Upload nucleic acid data > and retrieve their sample accessions
3. Upload specimen metadata > and link nucleic acid sample accessions

Add username and, most importantly, password wrapped with single quotes (e.g. 'Webin-XXXXX'), to ensure shell does not interpret special characters before passing them to **Arch3d**

### Upload nucleic acid data to ENA

The commands upload data and metadata and yield a table with the run, experiment, sample and biosample accession numbers.

#### Macro-scale data

This commands uploads the raw macro-scale data and the required metadata to **ENA**. The metadata columns are defined and must be strictly followed for the sake of standardisation.

```
arch3d macro \
  -d {data_directory} \
  -t {metadata_table} \
  -o {output_directory} \
  -u '{username}' \
  -p '{password}'
```

#### Micro-scale data

This commands uploads the raw macro-scale data and the required metadata to **ENA**. The main difference to `arch3d macro` is the requirement of more metadata about the spatial location of the microsamples.

```
arch3d micro \
  -d {data_directory} \
  -t {metadata_table} \
  -o {output_directory} \
  -u '{username}' \
  -p '{password}'
```

### Upload specimen metadata to Biosamples

The following commands activate a different procedure not to upload data, but only metadata of individual animals, intestinal sections and microsections. The metadata for each level is fetched from its corresponding table irtable (internal 3D'omics database) base Arch3d.

#### Microsection metadata

```
arch3d biosample \
  -i {input_table} \
  -o {output_directory} \
  -u '{username}' \
  -p '{password}'
```

#### Intestinal section metadata

```
arch3d biosample \
  -i {input_table} \
  -o {output_directory} \
  -u '{username}' \
  -p '{password}'
```

#### Animal specimen metadata

```
arch3d biosample \
  -i {input_table} \
  -o {output_directory} \
  -u '{username}' \
  -p '{password}'
```
