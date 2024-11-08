#!/usr/bin/env python3

"""
File:         harmonzize_genotype.py
Created:      2021/11/13
Last Changed:
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
__program__ = "Harmonize Genotype"
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
./harmonize_genotype.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.discovery_genotype_path = getattr(arguments, "discovery_genotype")
        self.replication_genotype_path = getattr(arguments, "replication_genotype")
        self.output_filename = getattr(arguments, "output_filename")

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))), "harmonize_genotype"
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(prog=__program__, description=__description__)

        # Add optional arguments.
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="{} {}".format(__program__, __version__),
            help="show program's version number and exit.",
        )
        parser.add_argument(
            "-dg",
            "--discovery_genotype",
            type=str,
            required=True,
            help="The path to the discovery genotype matrix",
        )
        parser.add_argument(
            "-rg",
            "--replication_genotype",
            type=str,
            required=True,
            help="The path to the discovery genotype matrix",
        )
        parser.add_argument(
            "-o",
            "--output_filename",
            type=str,
            required=True,
            help="The name of the output file.",
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading genotype data.")
        d_data_df = self.load_file(self.discovery_genotype_path, header=0, index_col=0)
        d_data_df = d_data_df.groupby(d_data_df.index).first()
        r_data_df = self.load_file(
            self.replication_genotype_path, header=0, index_col=0
        )
        r_data_df = r_data_df.groupby(r_data_df.index).first()
        print(d_data_df)
        print(r_data_df)

        print("Split the dataframes.")
        d_alleles_df = d_data_df.iloc[:, :2]
        r_alleles_df = r_data_df.iloc[:, :2]
        r_geno_df = r_data_df.iloc[:, 2:]
        del d_data_df, r_data_df

        print("Access the minor allele")
        alleles_df = r_alleles_df[["MinorAllele"]].merge(
            d_alleles_df[["MinorAllele"]], left_index=True, right_index=True
        )
        alleles_df["flip"] = alleles_df.iloc[:, 0] != alleles_df.iloc[:, 1]
        flip_mask = alleles_df["flip"].to_numpy(dtype=bool)
        snps_of_interest = list(alleles_df.index)

        print("Processing genotype file.")
        r_geno_df = r_geno_df.loc[snps_of_interest, :]

        # Flip genotypes.
        geno_m = r_geno_df.to_numpy()
        missing_mask = geno_m == -1
        geno_m[flip_mask, :] = 2 - geno_m[flip_mask, :]
        geno_m[missing_mask] = -1
        r_geno_df = pd.DataFrame(
            geno_m, index=r_geno_df.index, columns=r_geno_df.columns
        )
        r_geno_df.index.name = None
        del geno_m

        # Delete rows with all NaN.
        mask = r_geno_df.isnull().all(1).to_numpy()
        r_geno_df = r_geno_df.loc[~mask, :]

        print("Combine alleles and genotype file.")
        out_data_df = d_alleles_df.loc[snps_of_interest, :].merge(
            r_geno_df, left_index=True, right_index=True
        )
        print(out_data_df)

        print("\tSaving output file.")
        self.save_file(
            df=out_data_df,
            outpath=os.path.join(self.outdir, "{}.txt.gz".format(self.output_filename)),
        )

    @staticmethod
    def load_file(
        inpath, header, index_col, sep="\t", low_memory=True, nrows=None, skiprows=None
    ):
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

        df.to_csv(outpath, sep=sep, index=index, header=header, compression=compression)
        print(
            "\tSaved dataframe: {} "
            "with shape: {}".format(os.path.basename(outpath), df.shape)
        )

    def print_arguments(self):
        print("Arguments:")
        print("  > Discovery genotype path: {}".format(self.discovery_genotype_path))
        print(
            "  > Replication genotype path: {}".format(self.replication_genotype_path)
        )
        print("  > Output directory: {}".format(self.outdir))
        print("  > Output filename: {}".format(self.output_filename))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
