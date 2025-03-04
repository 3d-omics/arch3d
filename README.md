# arch3d

**Arch3d** is a Python software for archiving 3D'omics data and metadata in the public EBI databases ENA, BioSamples, Bioarchive Image and Metabolights.

```
pip install git+https://github.com/3d-omics/arch3d.git
```

## Upload of nucleotide data to ENA

```
arch3d nucleotide \
  -d {data_directory} \
  -s {sample_checklist} \
  -e {experiment_checklist} \
  -o {output_directory} \
  -u {username} \
  -p {password}
```

## Upload of sample metadata to Biosamples

```
arch3d sample \
  -i {input_table} \
  -o {output_directory} \
  -u {username} \
  -p {password}
```
