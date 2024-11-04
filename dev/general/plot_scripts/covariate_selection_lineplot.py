#!/usr/bin/env python3

"""
File:         covariate_selection_lineplot.py
Created:      2021/12/06
Last Changed: 2022/02/10
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function
import argparse
import json
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
__program__ = "Covariate Selection Lineplot"
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
./covariate_selection_lineplot.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.input_directory = getattr(arguments, "indir")
        self.palette_path = getattr(arguments, "palette")
        self.out_filename = getattr(arguments, "outfile")

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))), "plot"
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        # Loading palette.
        self.palette = None
        if self.palette_path is not None:
            with open(self.palette_path) as f:
                self.palette = json.load(f)
            f.close()

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
            "-i",
            "--indir",
            type=str,
            required=True,
            help="The path to the input directory.",
        )
        parser.add_argument(
            "-p",
            "--palette",
            type=str,
            required=False,
            default=None,
            help="The path to a json file with the" "dataset to color combinations.",
        )
        parser.add_argument(
            "-o", "--outfile", type=str, required=True, help="The name of the outfile."
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading data")
        df_list = []
        for i in range(1, 50):
            fpath = os.path.join(
                self.input_directory, "PIC{}".format(i), "covariate_selection.txt.gz"
            )
            if os.path.exists(fpath):
                df = self.load_file(fpath, header=0, index_col=None)
                df["index"] = i
                df_list.append(df)

        print("Merging data")
        if len(df_list) > 1:
            df = pd.concat(df_list, axis=0)
        else:
            df = df_list[0]
        print(df)

        print("Plotting")
        self.lineplot(
            df_m=df,
            x="index",
            y="N-ieQTLs",
            units="Covariate",
            xlabel="PIC",
            ylabel="#ieQTLs (FDR <=0.05)",
            filename=self.out_filename + "covariate_selection_lineplot",
            outdir=self.outdir,
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
    def lineplot(
        df_m,
        x="x",
        y="y",
        units=None,
        hue=None,
        palette=None,
        title="",
        xlabel="",
        ylabel="",
        filename="plot",
        info=None,
        outdir=None,
    ):
        sns.set(rc={"figure.figsize": (12, 9)})
        sns.set_style("ticks")
        fig, (ax1, ax2) = plt.subplots(
            nrows=1, ncols=2, gridspec_kw={"width_ratios": [0.99, 0.01]}
        )
        sns.despine(fig=fig, ax=ax1)

        g = sns.lineplot(
            data=df_m,
            x=x,
            y=y,
            units=units,
            hue=hue,
            palette=palette,
            estimator=None,
            legend=None,
            ax=ax1,
        )

        ax1.set_title(title, fontsize=14, fontweight="bold")
        ax1.set_xlabel(xlabel, fontsize=10, fontweight="bold")
        ax1.set_ylabel(ylabel, fontsize=10, fontweight="bold")

        if palette is not None:
            handles = []
            for key, color in palette.items():
                if key in df_m[hue].values.tolist():
                    label = key
                    if info is not None and key in info:
                        label = "{} [{}]".format(key, info[key])
                    handles.append(mpatches.Patch(color=color, label=label))
            ax2.legend(handles=handles, loc="center")
        ax2.set_axis_off()

        plt.tight_layout()
        outpath = "{}.png".format(filename)
        if outdir is not None:
            outpath = os.path.join(outdir, outpath)
        fig.savefig(outpath)
        plt.close()

    def print_arguments(self):
        print("Arguments:")
        print("  > Input directory: {}".format(self.input_directory))
        print("  > Palette path: {}".format(self.palette_path))
        print("  > Outpath {}".format(self.outdir))
        print("  > Output filename: {}".format(self.out_filename))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
