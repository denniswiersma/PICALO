#!/usr/bin/env python3

"""
File:         calc_avg_gene_expression.py
Created:      2022/02/17
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
import numpy as np
import pandas as pd

# Local application imports.

# Metadata
__program__ = "Calculate Average Gene Expression"
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
./calc_avg_gene_expression.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.std_path = getattr(arguments, "sample_to_dataset")
        self.expression_path = getattr(arguments, "expression")

        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))), "calc_avg_gene_expression"
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        if not self.expression_path.endswith(".txt.gz"):
            print("Expression path should end with '.txt.gz'")
            exit()

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
            "-std",
            "--sample_to_dataset",
            type=str,
            required=False,
            default=None,
            help="The path to the sample-dataset link matrix.",
        )
        parser.add_argument(
            "-ex",
            "--expression",
            type=str,
            default=None,
            help="The path to the expression matrix in TMM" "format.",
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading expression data")
        expr_df = self.load_file(self.expression_path, header=0, index_col=0)
        std_df = self.load_file(self.std_path, header=0, index_col=None)
        samples = std_df.iloc[:, 0].values.tolist()

        print("Sample selection.")
        expr_df = expr_df.loc[:, samples]
        print("\tUsing {} samples".format(len(samples)))

        print("Log2 transform.")
        min_value = expr_df.min(axis=1).min()
        if min_value <= 0:
            expr_df = np.log2(expr_df - min_value + 1)
        else:
            expr_df = np.log2(expr_df + 1)

        print("Calculate average.")
        avg_df = expr_df.mean(axis=1).to_frame()
        avg_df.columns = ["average"]

        print("Saving file.")
        print(avg_df)
        filename = os.path.basename(self.expression_path).replace(".txt.gz", "")
        self.save_file(
            df=avg_df,
            outpath=os.path.join(
                self.outdir,
                "{}.Log2Transformed.AverageExpression.txt.gz".format(filename),
            ),
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
        print("  > Expression: {}".format(self.expression_path))
        print("  > Sample-to-dataset path: {}".format(self.std_path))
        print("  > Output directory: {}".format(self.outdir))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
