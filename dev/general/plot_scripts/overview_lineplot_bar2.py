#!/usr/bin/env python3

import argparse
import os

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class main:
    def __init__(self):
        # Get command-line arguments
        arguments = self.create_argument_parser()
        self.input_directory = arguments.indir
        self.out_filename = arguments.outfile

        # Set output directory
        self.outdir = os.path.join(os.getcwd(), "plot")
        os.makedirs(self.outdir, exist_ok=True)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(
            description="Barplot of Number of Effects per PIC"
        )
        parser.add_argument(
            "-i", "--indir", type=str, required=True, help="Input directory"
        )
        parser.add_argument(
            "-o", "--outfile", type=str, required=True, help="Output filename"
        )
        return parser.parse_args()

    def start(self):
        print("Loading data...")

        # Collect N values for each PIC
        data = []
        for i in range(1, 50):  # Loop over possible PICs
            fpath = os.path.join(self.input_directory, f"PIC{i}", "info.txt.gz")
            if os.path.exists(fpath):
                df = pd.read_csv(fpath, sep="\t", header=0)
                if "N" in df.columns:
                    last_n = df["N"].iloc[-1]  # Take last row of column N
                    data.append(["PIC" + str(i), last_n])

        # Create a DataFrame
        df_n = pd.DataFrame(data, columns=["PIC", "N"])
        df_n = df_n.sort_values(
            "N", ascending=False
        )  # Sort for better visualization

        self.barplot(df_n)

    def barplot(self, df_n):
        print("Creating bar plot...")

        fig, ax = plt.subplots(figsize=(14, 8))
        bars = ax.bar(
            df_n["PIC"], df_n["N"], color="#56B4E9", edgecolor="black"
        )

        # Labels
        # ax.set_xlabel("PIC", fontsize=18)
        ax.set_ylabel("Number of Effects per PIC", fontsize=18)
        # ax.set_title(
        #     "Number of Effects per PIC (Last Iteration)",
        #     fontsize=20,
        #     fontweight="bold",
        # )
        ax.tick_params(axis="x", rotation=90, labelsize=14)
        ax.tick_params(axis="y", labelsize=16)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Annotate bars with exact numbers
        for bar, value in zip(bars, df_n["N"]):
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
            os.path.join(self.outdir, f"{self.out_filename}_barplot.png")
        )
        plt.close()
        print(f"Saved plot: {self.outdir}/{self.out_filename}_barplot.png")


if __name__ == "__main__":
    m = main()
    m.start()
