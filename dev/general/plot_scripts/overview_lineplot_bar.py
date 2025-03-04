#!/usr/bin/env python3

"""
"""

# Standard imports.
from __future__ import print_function

import argparse
import json
import os

import matplotlib
# Third-party imports.
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.input_directory = getattr(arguments, "indir")
        self.palette_path = getattr(arguments, "palette")
        self.out_filename = getattr(arguments, "outfile")

        # Set output directory.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))), "plot"
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        # Load color palette.
        self.palette = None
        if self.palette_path is not None:
            with open(self.palette_path) as f:
                self.palette = json.load(f)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(description="Overview Lineplot Script")

        # Command-line arguments.
        parser.add_argument(
            "-i", "--indir", type=str, required=True, help="Input directory"
        )
        parser.add_argument(
            "-p",
            "--palette",
            type=str,
            required=False,
            default=None,
            help="Color palette JSON",
        )
        parser.add_argument(
            "-o", "--outfile", type=str, required=True, help="Output filename"
        )
        return parser.parse_args()

    def start(self):
        print("Loading data")

        info_dict = {}
        df_m_list = []
        for i in range(1, 50):
            fpath = os.path.join(self.input_directory, f"PIC{i}", "info.txt.gz")
            if os.path.exists(fpath):
                df = self.load_file(fpath, header=0, index_col=0)
                info_dict[f"PIC{i}"] = df.loc["iteration0", "covariate"]

                df["index"] = np.arange(1, (df.shape[0] + 1))
                df["component"] = f"PIC{i}"
                df_m_list.append(df)

        print("Merging data")
        if len(df_m_list) > 1:
            df_m = pd.concat(df_m_list, axis=0)
        else:
            df_m = df_m_list[0]
            print("No valid data found!")

        print("Available columns in df_m:", df_m.columns.tolist())

        # df_m["log10 value"] = np.log10(df_m["value"])
        df_m["log10 value"] = np.log10(df_m["N"])

        # Generate plots.
        for variable in df_m["variable"].unique():
            print(f"\tProcessing: {variable}")
            subset_m = df_m[df_m["variable"] == variable]
            if variable in ["N Overlap", "Overlap %"]:
                subset_m = subset_m[subset_m["index"] != 1]

            self.lineplot(
                subset_m, "index", "value", "component", self.palette, variable
            )

            if variable == "N":
                self.barplot(subset_m, "component", "value", self.palette)

    @staticmethod
    def load_file(inpath, header, index_col, sep="\t"):
        df = pd.read_csv(inpath, sep=sep, header=header, index_col=index_col)
        print(f"\tLoaded: {os.path.basename(inpath)} | Shape: {df.shape}")
        return df

    def lineplot(self, df_m, x, y, hue, palette, ylabel):
        print(f"\tCreating line plot: {ylabel}")

        fig, ax = plt.subplots(figsize=(12, 8))
        sns.lineplot(
            data=df_m, x=x, y=y, hue=hue, palette=palette, ax=ax, legend=None
        )

        ax.set_xlabel("Iteration", fontsize=18)
        ax.set_ylabel(ylabel, fontsize=18)
        ax.tick_params(axis="x", labelsize=18)
        ax.tick_params(axis="y", labelsize=18)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.outdir,
                f"{self.out_filename}_lineplot_{ylabel.replace(' ', '_').lower()}.png",
            )
        )
        plt.close()

    # new version
    def barplot(self, df_m, x, y, palette):
        print("\tCreating bar plot for last iteration")

        # Ensure column exists
        if y not in df_m.columns:
            raise KeyError(
                f"Expected column '{y}' not found in DataFrame! Available columns: {df_m.columns.tolist()}"
            )

        # Find last iteration
        # last_iteration = df_m[df_m["index"] == df_m["index"].max()]
        last_iteration = last_iteration.sort_values("N", ascending=False)
        if last_iteration.empty:
            raise ValueError("No data found for the last iteration.")

        # Sort by effect count
        last_iteration = last_iteration.sort_values(y, ascending=False)

        # Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.bar(
            last_iteration[x],
            last_iteration[y],
            color=[palette.get(ct, "#56B4E9") for ct in last_iteration[x]],
            edgecolor="black",
        )

        # Labels
        ax.set_xlabel("PIC", fontsize=18)
        ax.set_ylabel("Number of Effects", fontsize=18)
        ax.set_title(
            "Number of Effects per PIC (Last Iteration)",
            fontsize=20,
            fontweight="bold",
        )
        ax.tick_params(axis="x", rotation=45, labelsize=18)
        ax.tick_params(axis="y", labelsize=18)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Annotate bars
        for bar, value in zip(bars, last_iteration[y]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 50,
                f"{int(value):,}",
                ha="center",
                va="bottom",
                fontsize=12,
            )

        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.outdir, f"{self.out_filename}_barplot_effects.png"
            )
        )
        plt.close()

    # old version
    # def barplot(self, df_m, x, y, palette):
    #     print("\tCreating bar plot for last iteration")
    #
    #     last_iteration = df_m[df_m["index"] == df_m["index"].max()]
    #     last_iteration = last_iteration.sort_values(y, ascending=False)
    #
    #     fig, ax = plt.subplots(figsize=(12, 8))
    #     bars = ax.bar(
    #         last_iteration[x],
    #         last_iteration[y],
    #         color=[palette.get(ct, "#56B4E9") for ct in last_iteration[x]],
    #         edgecolor="black",
    #     )
    #
    #     # Labels
    #     ax.set_xlabel("PIC", fontsize=18)
    #     ax.set_ylabel("Number of Effects", fontsize=18)
    #     ax.set_title(
    #         "Number of Effects per PIC (Last Iteration)",
    #         fontsize=20,
    #         fontweight="bold",
    #     )
    #     ax.tick_params(axis="x", rotation=45, labelsize=18)
    #     ax.tick_params(axis="y", labelsize=18)
    #     ax.grid(axis="y", linestyle="--", alpha=0.7)
    #
    #     # Annotate bars
    #     for bar, value in zip(bars, last_iteration[y]):
    #         ax.text(
    #             bar.get_x() + bar.get_width() / 2,
    #             value + 50,
    #             f"{int(value):,}",
    #             ha="center",
    #             va="bottom",
    #             fontsize=12,
    #         )
    #
    #     plt.tight_layout()
    #     plt.savefig(
    #         os.path.join(
    #             self.outdir, f"{self.out_filename}_barplot_effects.png"
    #         )
    #     )
    #     plt.close()


if __name__ == "__main__":
    m = main()
    m.start()
