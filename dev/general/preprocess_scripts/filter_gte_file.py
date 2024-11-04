#!/usr/bin/env python3

"""
File:         filter_gte_file.py
Created:      2021/10/28
Last Changed: 2021/11/10
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function

import argparse
import os

# Third party imports.
import pandas as pd

# Local application imports.

# Metadata
__program__ = "Filter GTE file"
__author__ = "Martijn Vochteloo"
__maintainer__ = "Martijn Vochteloo"
__email__ = "m.vochteloo@rug.nl"
__license__ = "BSD (3-Clause)"
__version__ = 1.0
__description__ = (
    "{} is a program developed and maintained by {}. "
    "This program is licensed under the {} license and is "
    "provided 'as-is' without any warranty or indemnification "
    "of any kind.".format(__program__, __author__, __license__)
)

"""
Syntax:
./filter_gte_file.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.gte_path = getattr(arguments, "genotype_to_expression")
        self.e_gte_path = getattr(arguments, "exclude_genotype_to_expression")
        self.n_samples = getattr(arguments, "n_samples")
        outdir = getattr(arguments, "outdir")

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))),
            "filter_gte_file",
            outdir,
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(
            prog=__program__,
            description=__description__,
        )

        # Add optional arguments.
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="{} {}".format(__program__, __version__),
            help="show program's version number and exit.",
        )
        parser.add_argument(
            "-gte",
            "--genotype_to_expression",
            type=str,
            required=False,
            default=None,
            help="The path to the genotype-to-expression" " link matrix.",
        )
        parser.add_argument(
            "-e",
            "--exclude_genotype_to_expression",
            type=str,
            default=None,
            help="The path to the samples to remove" "in GTE format.",
        )
        parser.add_argument(
            "-ns",
            "--n_samples",
            type=int,
            default=30,
            help="The number of required samples per dataet. " "Default: 30.",
        )
        parser.add_argument(
            "-o",
            "--outdir",
            type=str,
            required=True,
            help="The path to the output directory.",
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading data.")
        gte_df = self.load_file(
            self.gte_path,
            header=None,
            names=["genotype_id", "rnaseq_id", "dataset"],
            index_col=None,
        )
        print("dit is gte df")
        print(gte_df)
        se_df = None
        if self.e_gte_path is not None:
            se_df = self.load_file(self.e_gte_path, header=0, index_col=None)
            print("dit is se df")
            print(se_df)
            print(se_df["dataset"].value_counts())

        ########################################################################

        if se_df is not None:
            print("Removing samples.")
            remove_rnaseq_ids = set(se_df["rnaseq_id"])
            mask = [
                False if sample in remove_rnaseq_ids else True
                for sample in gte_df["rnaseq_id"]
            ]
            gte_df = gte_df.loc[mask, :]

        print("Filtering on dataset sample size")
        dataset_sizes = gte_df["dataset"].value_counts().to_frame()
        remove_datasets = []
        for dataset, row in dataset_sizes.iterrows():
            if row["dataset"] < self.n_samples:
                print("Removing {}".format(dataset))
                remove_datasets.append(dataset)

        if len(remove_datasets) > 0:
            subset_gte_df = gte_df[~gte_df["dataset"].isin(remove_datasets)]

        dataset_sizes = gte_df["dataset"].value_counts().to_frame()
        print(dataset_sizes)

        ########################################################################

        print("Saving files.")
        # Gene-to-expression file.
        self.save_file(
            df=gte_df,
            outpath=os.path.join(self.outdir, "GenotypeToExpression.txt.gz"),
            index=False,
        )

        # Sample-to-dataset file.
        std_df = gte_df.loc[:, ["rnaseq_id", "dataset"]]
        std_df.columns = ["sample", "dataset"]
        self.save_file(
            df=std_df,
            outpath=os.path.join(self.outdir, "SampleToDataset.txt.gz"),
            index=False,
        )

        # Family-genotype file (for MDS analyses).
        gte_fid_df = gte_df.loc[:, ["genotype_id"]].copy()
        gte_fid_df.insert(0, "family_id", 0)
        self.save_file(
            df=gte_fid_df,
            outpath=os.path.join(self.outdir, "FamilyToGenotype.txt"),
            header=False,
            index=False,
        )

    @staticmethod
    def load_file(
        inpath,
        header,
        index_col,
        sep="\t",
        low_memory=True,
        nrows=None,
        skiprows=None,
    ):
        if inpath.endswith(".pkl"):
            df = pd.read_pickle(inpath)
        else:
            df = pd.read_csv(
                inpath,
                sep=sep,
                header=header,
                index_col=index_col,
                low_memory=low_memory,
                nrows=nrows,
                skiprows=skiprows,
            )
        print(
            "\tLoaded dataframe: {} "
            "with shape: {}".format(os.path.basename(inpath), df.shape)
        )
        return df

    @staticmethod
    def save_file(df, outpath, header=True, index=True, sep="\t"):
        compression = "infer"
        if outpath.endswith(".gz"):
            compression = "gzip"

        df.to_csv(
            outpath,
            sep=sep,
            index=index,
            header=header,
            compression=compression,
        )
        print(
            "\tSaved dataframe: {} "
            "with shape: {}".format(os.path.basename(outpath), df.shape)
        )

    def print_arguments(self):
        print("Arguments:")
        print("  > GTE path: {}".format(self.gte_path))
        print("  > Exclude GTE path: {}".format(self.e_gte_path))
        print("  > N-samples: {}".format(self.n_samples))
        print("  > Output directory: {}".format(self.outdir))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
