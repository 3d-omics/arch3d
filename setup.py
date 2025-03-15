from setuptools import setup, find_packages

setup(
    name="arch3d",
    version="1.0.0",
    author="Antton Alberdi",
    author_email="antton.alberdi@sund.ku.dk",
    description="Python software for archiving 3D'omics data and metadata in public databases",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy",
        "pandas",
        "argparse",
        "PyYAML",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "arch3d=arch3d.cli:main",
        ],
    },
    python_requires=">=3.6",
)
