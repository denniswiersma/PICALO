#!/usr/bin/env python3

"""
File:         plot_df_per_column.py
Created:      2021/10/26
Last Changed: 2021/10/28
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
import seaborn as sns
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Local application imports.

# Metadata
__program__ = "Plot DataFrame per Column"
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
./plot_df_per_column.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.data_path = getattr(arguments, "data")
        self.n_columns = getattr(arguments, "n_columns")
        self.std_path = getattr(arguments, "sample_to_dataset")
        self.transpose = getattr(arguments, "transpose")
        self.extensions = getattr(arguments, "extension")
        self.output_filename = getattr(arguments, "output")
        self.sd = 3

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))), "plot"
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        self.palette = {
            "AMPAD-MAYO-V2": "#9C9FA0",
            "CMC_HBCC_set2": "#0877B4",
            "GTEx": "#0FA67D",
            "AMPAD-ROSMAP-V2": "#6950A1",
            "BrainGVEX-V2": "#48B2E5",
            "TargetALS": "#D5C77A",
            "AMPAD-MSBB-V2": "#5CC5BF",
            "NABEC-H610": "#6D743A",
            "LIBD_1M": "#808080",
            "LIBD_5M": "#808080",
            "ENA": "#D46727",
            "LIBD_h650": "#808080",
            "GVEX": "#48B2E5",
            "NABEC-H550": "#6D743A",
            "CMC_HBCC_set3": "#0877B4",
            "UCLA_ASD": "#F36D2A",
            "CMC": "#EAE453",
            "CMC_HBCC_set1": "#0877B4",
            "Braineac": "#E49D26",
            "Bipseq_1M": "#000000",
            "Bipseq_h650": "#000000",
            "Brainseq": "#C778A6",
            "LL": "#0fa67d",
            "RS": "#d46727",
            "LLS_660Q": "#000000",
            "NTR_AFFY": "#0877b4",
            "LLS_OmniExpr": "#9c9fa0",
            "CODAM": "#6d743a",
            "PAN": "#6950a1",
            "NTR_GONL": "#48b2e5",
            "GONL": "#eae453",
            0.0: "#DC106C",
            1.0: "#03165e",
        }

        self.dataset_to_cohort = {
            "GTE-EUR-AMPAD-MAYO-V2": "MAYO",
            "GTE-EUR-CMC_HBCC_set2": "CMC HBCC",
            "GTE-EUR-GTEx": "GTEx",
            "GTE-EUR-AMPAD-ROSMAP-V2": "ROSMAP",
            "GTE-EUR-BrainGVEX-V2": "Brain GVEx",
            "GTE-EUR-TargetALS": "Target ALS",
            "GTE-EUR-AMPAD-MSBB-V2": "MSBB",
            "GTE-EUR-NABEC-H610": "NABEC",
            "GTE-EUR-LIBD_1M": "LIBD",
            "GTE-EUR-ENA": "ENA",
            "GTE-EUR-LIBD_h650": "LIBD",
            "GTE-EUR-GVEX": "GVEX",
            "GTE-EUR-NABEC-H550": "NABEC",
            "GTE-EUR-CMC_HBCC_set3": "CMC HBCC",
            "GTE-EUR-UCLA_ASD": "UCLA ASD",
            "GTE-EUR-CMC": "CMC",
            "GTE-EUR-CMC_HBCC_set1": "CMC HBCC",
        }

        # Set the right pdf font for exporting.
        matplotlib.rcParams["pdf.fonttype"] = 42
        matplotlib.rcParams["ps.fonttype"] = 42

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
            "-d", "--data", type=str, required=True, help="The path to the input data."
        )
        parser.add_argument(
            "-n",
            "--n_columns",
            type=int,
            default=None,
            help="The number of columns to plot.",
        )
        parser.add_argument(
            "-std",
            "--sample_to_dataset",
            type=str,
            required=True,
            help="The path to the sample-to-dataset matrix.",
        )
        parser.add_argument(
            "-transpose",
            action="store_true",
            help="Combine the created files with force." " Default: False.",
        )
        parser.add_argument(
            "-e",
            "--extension",
            nargs="+",
            type=str,
            choices=["png", "pdf", "eps"],
            default=["png"],
            help="The figure file extension. " "Default: 'png'.",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default="PlotPerColumn_ColorByCohort",
            help="The name of the output file.",
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading data.")
        df = self.load_file(self.data_path, header=0, index_col=0)
        if self.transpose:
            df = df.T
        if self.n_columns is not None:
            df = df.iloc[:, : self.n_columns]
        columns = list(df.columns)

        print("Loading sample to dataset")
        std_df = self.load_file(self.std_path, header=0, index_col=None)
        std_dict = dict(zip(std_df.iloc[:, 0], std_df.iloc[:, 1]))

        print("\tAdding color.")
        overlap = set(df.index.values).intersection(set(std_df.iloc[:, 0].values))
        if len(overlap) != df.shape[0]:
            print("Error, some samples do not have a dataset.")
            exit()
        df["dataset"] = df.index.map(std_dict)

        print("\tPlotting")
        self.plot(
            df=df,
            columns=columns,
            hue="dataset",
            palette=self.palette,
            name=self.output_filename,
        )

        print("\tAdding z-score color")
        for name in columns:
            df["{} z-score".format(name)] = (df[name] - df[name].mean()) / df[
                name
            ].std()

        df["outlier"] = "False"
        df.loc[
            (df["{} z-score".format(columns[0])].abs() > self.sd)
            | (df["{} z-score".format(columns[1])].abs() > self.sd)
            | (df["{} z-score".format(columns[2])].abs() > self.sd)
            | (df["{} z-score".format(columns[3])].abs() > self.sd),
            "outlier",
        ] = "True"
        print(df)
        outlier_df = df.loc[df["outlier"] == "True", :].copy()
        print(outlier_df)
        print(outlier_df["dataset"].value_counts())
        outlier_df.to_csv(
            os.path.join(self.outdir, self.output_filename + "_outliers.txt.gz"),
            compression="gzip",
            sep="\t",
            header=True,
            index=True,
        )

        print("\tPlotting")
        self.plot(
            df=df,
            columns=columns,
            hue="outlier",
            palette={"True": "#b22222", "False": "#000000"},
            name=self.output_filename + "_Outlier",
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

    def plot(self, df, columns, hue, palette, name, title=""):
        ncols = len(columns)
        nrows = len(columns)

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            sharex="col",
            sharey="row",
            figsize=(10 * ncols, 10 * nrows),
        )
        sns.set(color_codes=True)
        sns.set_style("ticks")

        for i, y_col in enumerate(columns):
            for j, x_col in enumerate(columns):
                print(i, j)
                ax = axes[i, j]
                if i == 0 and j == (ncols - 1):
                    ax.set_axis_off()
                    if hue is not None and palette is not None:
                        groups_present = df[hue].unique()
                        handles = []
                        added_handles = []
                        for key, value in palette.items():
                            if key in groups_present:
                                label = str(key)
                                if key in self.dataset_to_cohort:
                                    label = self.dataset_to_cohort[key]
                                if value + label not in added_handles:
                                    handles.append(
                                        mpatches.Patch(color=value, label=label)
                                    )
                                    added_handles.append(value + label)
                        ax.legend(handles=handles, loc=4, fontsize=25)

                elif i < j:
                    ax.set_axis_off()
                    continue
                elif i == j:
                    ax.set_axis_off()

                    ax.annotate(
                        y_col,
                        xy=(0.5, 0.5),
                        ha="center",
                        xycoords=ax.transAxes,
                        color="#000000",
                        fontsize=40,
                        fontweight="bold",
                    )
                else:
                    sns.despine(fig=fig, ax=ax)

                    sns.scatterplot(
                        x=x_col,
                        y=y_col,
                        hue=hue,
                        data=df,
                        s=100,
                        palette=palette,
                        linewidth=0,
                        legend=False,
                        ax=ax,
                    )

                    ax.set_ylabel("", fontsize=20, fontweight="bold")
                    ax.set_xlabel("", fontsize=20, fontweight="bold")

        fig.suptitle(title, fontsize=40, fontweight="bold")

        for extension in self.extensions:
            fig.savefig(os.path.join(self.outdir, "{}.{}".format(name, extension)))
        plt.close()

    def print_arguments(self):
        print("Arguments:")
        print("  > Data path: {}".format(self.data_path))
        print("  > N-columns: {}".format(self.n_columns))
        print("  > Sample-to-dataset path: {}".format(self.std_path))
        print("  > Transpose: {}".format(self.transpose))
        print("  > Extension: {}".format(self.extensions))
        print("  > Output filename: {}".format(self.output_filename))
        print("  > Output directory {}".format(self.outdir))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
