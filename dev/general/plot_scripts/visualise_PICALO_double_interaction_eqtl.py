#!/usr/bin/env python3

"""
File:         visualise_PICALO_double_interaction_eqtl.py
Created:      2022/07/22
Last Changed: 2022/07/25
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function

import argparse
import os
from pathlib import Path

# Third party imports.
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.special import ndtri

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.regression.linear_model import OLS

# Local application imports.

# Metadata
__program__ = "Visualise PICALO Double Interaction eQTL"
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
./visualise_PICALO_double_interaction_eqtl.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.picalo_path = getattr(arguments, "picalo_path")
        self.geno_path = getattr(arguments, "genotype")
        self.alleles_path = getattr(arguments, "alleles")
        self.genotype_na = getattr(arguments, "genotype_na")
        self.expr_path = getattr(arguments, "expression")
        self.tcov_path = getattr(arguments, "tech_covariate")
        self.tcov_inter_path = getattr(arguments, "tech_covariate_with_inter")
        self.std_path = getattr(arguments, "sample_to_dataset")
        self.min_dataset_size = getattr(arguments, "min_dataset_size")
        self.call_rate = getattr(arguments, "call_rate")
        self.interest = getattr(arguments, "interest")
        self.nrows = getattr(arguments, "nrows")
        self.extensions = getattr(arguments, "extensions")

        # Set variables.
        self.outdir = os.path.join(
            str(Path(__file__).parent.parent),
            "visualise_PICALO_double_interaction_eqtl",
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        self.palette = {2.0: "#E69F00", 1.0: "#0072B2", 0.0: "#D55E00"}

        # Set the right pdf font for exporting.
        matplotlib.rcParams["pdf.fonttype"] = 42
        matplotlib.rcParams["ps.fonttype"] = 42

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(
            prog=__program__, description=__description__
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
            "-pp",
            "--picalo_path",
            type=str,
            required=True,
            help="The path to the PICALO output directory.",
        )
        parser.add_argument(
            "-ge",
            "--genotype",
            type=str,
            required=True,
            help="The path to the genotype matrix.",
        )
        parser.add_argument(
            "-al",
            "--alleles",
            type=str,
            required=True,
            help="The path to the alleles matrix",
        )
        parser.add_argument(
            "-na",
            "--genotype_na",
            type=int,
            required=False,
            default=-1,
            help="The genotype value that equals a missing "
            "value. Default: -1.",
        )
        parser.add_argument(
            "-ex",
            "--expression",
            type=str,
            required=True,
            help="The path to the expression matrix.",
        )
        parser.add_argument(
            "-tc",
            "--tech_covariate",
            type=str,
            default=None,
            help="The path to the technical covariate matrix "
            "(excluding an interaction with genotype). "
            "Default: None.",
        )
        parser.add_argument(
            "-tci",
            "--tech_covariate_with_inter",
            type=str,
            default=None,
            help="The path to the technical covariate matrix"
            "(including an interaction with genotype). "
            "Default: None.",
        )
        parser.add_argument(
            "-std",
            "--sample_to_dataset",
            type=str,
            required=False,
            default=None,
            help="The path to the sample-dataset link matrix." "Default: None.",
        )
        parser.add_argument(
            "-mds",
            "--min_dataset_size",
            type=int,
            required=False,
            default=30,
            help="The minimal number of samples per dataset. " "Default: >=30.",
        )
        parser.add_argument(
            "-cr",
            "--call_rate",
            type=float,
            required=False,
            default=0.95,
            help="The minimal call rate of a SNP (per dataset)."
            "Equals to (1 - missingness). "
            "Default: >= 0.95.",
        )
        parser.add_argument(
            "-i",
            "--interest",
            nargs="+",
            type=str,
            required=True,
            help="The IDs to plot.",
        )
        parser.add_argument(
            "-n",
            "--nrows",
            type=int,
            required=False,
            default=None,
            help="Cap the number of runs to load. " "Default: None.",
        )
        parser.add_argument(
            "-e",
            "--extensions",
            nargs="+",
            type=str,
            choices=["png", "pdf", "eps"],
            default=["png"],
            help="The figure file extension. " "Default: 'png'.",
        )

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        print("Loading data")
        geno_df = self.load_file(
            self.geno_path, header=0, index_col=0, nrows=self.nrows
        )
        alleles_df = self.load_file(
            self.alleles_path, header=0, index_col=0, nrows=self.nrows
        )

        if geno_df.index.tolist() != alleles_df.index.tolist():
            print("error in genotype allele files")
            exit()

        expr_df = self.load_file(
            self.expr_path, header=0, index_col=0, nrows=self.nrows
        )
        std_df = self.load_file(self.std_path, header=0, index_col=None)
        std_map = dict(zip(std_df.iloc[:, 0], std_df.iloc[:, 1]))

        dataset_df = self.construct_dataset_df(std_df=std_df)
        datasets = dataset_df.columns.tolist()

        ########################################################################

        samples = std_df.iloc[:, 0].values.tolist()
        snps = geno_df.index.tolist()
        genes = expr_df.index.tolist()

        geno_m = geno_df.to_numpy(np.float64)
        expr_m = expr_df.to_numpy(np.float64)
        dataset_m = dataset_df.to_numpy(np.uint8)
        del geno_df, expr_df, dataset_df

        # Fill the missing values with NaN.
        expr_m[geno_m == self.genotype_na] = np.nan
        geno_m[geno_m == self.genotype_na] = np.nan

        ########################################################################

        tcov_m = None
        tcov_labels = None
        if self.tcov_path is not None:
            tcov_df = self.load_file(self.tcov_path, header=0, index_col=0)
            tcov_m, tcov_labels = self.load_tech_cov(
                df=tcov_df, name="tech. cov. without interaction", std_df=std_df
            )

        tcov_inter_m = None
        tcov_inter_labels = None
        if self.tcov_inter_path is not None:
            tcov_inter_df = self.load_file(
                self.tcov_inter_path, header=0, index_col=0
            )
            tcov_inter_m, tcov_inter_labels = self.load_tech_cov(
                df=tcov_inter_df,
                name="tech. cov. with interaction",
                std_df=std_df,
            )

        corr_m, corr_inter_m, correction_m_labels = (
            self.construct_correct_matrices(
                dataset_m=dataset_m,
                dataset_labels=datasets,
                tcov_m=tcov_m,
                tcov_labels=tcov_labels,
                tcov_inter_m=tcov_inter_m,
                tcov_inter_labels=tcov_inter_labels,
            )
        )

        ########################################################################

        plot_ids = {}
        max_pic = 0
        for interest in self.interest:
            splitted_input = interest.split("_")
            gene = splitted_input[0]
            snp = "_".join(splitted_input[1:-1])
            cov = splitted_input[-1]
            cov1, cov2 = cov.split("+")
            pic_index = int(cov2.replace("PIC", ""))
            if pic_index > max_pic:
                max_pic = pic_index
            eqlt_id = "{}_{}".format(gene, snp)
            if cov2 in plot_ids:
                plot_ids[cov2].append(eqlt_id)
            else:
                plot_ids[cov2] = [eqlt_id]
        ########################################################################

        eqtls_loaded = [
            "{}_{}".format(gene, snp) for gene, snp in zip(genes, snps)
        ]
        pic_corr_m = np.copy(corr_m)
        pic_corr_inter_m = np.copy(corr_inter_m)
        for pic_index in range(1, max_pic + 1):
            pic = "PIC{}".format(pic_index)
            if pic_index > 1:
                # Loading previous run PIC.
                with open(
                    os.path.join(
                        self.picalo_path,
                        "PIC{}".format(pic_index - 1),
                        "component.npy",
                    ),
                    "rb",
                ) as f:
                    pic_a = np.load(f)
                f.close()

                if pic_corr_m is not None:
                    pic_corr_m = np.hstack((pic_corr_m, pic_a[:, np.newaxis]))
                else:
                    pic_corr_m = pic_a[:, np.newaxis]

                if pic_corr_inter_m is not None:
                    pic_corr_inter_m = np.hstack(
                        (pic_corr_inter_m, pic_a[:, np.newaxis])
                    )
                else:
                    pic_corr_inter_m = pic_a[:, np.newaxis]

            if pic not in plot_ids:
                print("Skipping PIC{}".format(pic_index))
                continue
            print("Plotting PIC{}".format(pic_index))
            pic_plot_ids = plot_ids[pic]

            for row_index, eqtl_id in enumerate(eqtls_loaded):
                if eqtl_id not in pic_plot_ids:
                    continue
                splitted_id = eqtl_id.split("_")
                if len(splitted_id) == 2:
                    probe_name, snp_name = splitted_id
                else:
                    probe_name = splitted_id[0]
                    snp_name = "_".join(splitted_id[1:-1])

                cov1 = None
                cov2 = None
                for interest in self.interest:
                    if interest.startswith(eqtl_id) and interest.endswith(pic):
                        cov = interest.replace(eqtl_id + "_", "")
                        cov1, cov2 = cov.split("+")

                if cov1 is None or cov2 is None:
                    continue

                print(
                    "\tWorking on: {}\t{}\t{}-{} [{}]".format(
                        snp_name, probe_name, cov1, cov2, row_index + 1
                    )
                )

                # Combine data.
                data = pd.DataFrame(
                    {
                        "intercept": 1,
                        "genotype": np.copy(geno_m[row_index, :]),
                        "expression": np.copy(expr_m[row_index, :]),
                        "dataset": [std_map[sample] for sample in samples],
                    },
                    index=samples,
                )
                data["group"] = data["genotype"].round(0)

                # Check the call rate.
                for dataset in data["dataset"].unique():
                    sample_mask = (data["dataset"] == dataset).to_numpy(
                        dtype=bool
                    )
                    n_not_na = (
                        (data.loc[sample_mask, "genotype"] != self.genotype_na)
                        .astype(int)
                        .sum()
                    )
                    call_rate = n_not_na / np.sum(sample_mask)
                    if (call_rate < self.call_rate) or (
                        n_not_na < self.min_dataset_size
                    ):
                        data.loc[sample_mask, "genotype"] = np.nan

                # Add iterations.
                iter_df = self.load_file(
                    os.path.join(self.picalo_path, pic, "iteration.txt.gz"),
                    header=0,
                    index_col=0,
                )
                iter_df = iter_df.iloc[[0, -1], :].T
                iter_df.columns = ["covariate1", "covariate2"]
                data = data.merge(iter_df, left_index=True, right_index=True)

                # Remove missing values.
                mask = (~data["genotype"].isna()).to_numpy(bool)
                data = data.loc[mask, :]

                # Correct the expression.
                X = np.ones((data.shape[0], 1))
                if pic_corr_m is not None:
                    X = np.hstack((X, np.copy(pic_corr_m[mask, :])))
                if pic_corr_inter_m is not None:
                    X = np.hstack(
                        (
                            X,
                            np.copy(pic_corr_inter_m[mask, :])
                            * geno_m[row_index, :][mask, np.newaxis],
                        )
                    )
                data["expression"] = OLS(data["expression"], X).fit().resid

                # a = data[["intercept", "genotype", "covariate1"]].to_numpy()
                # b = data["expression"].to_numpy()
                # data["expression1"] = b - np.dot(a, np.linalg.inv(a.T.dot(a)).dot(a.T).dot(b))
                # print(data["expression1"])

                data["expression1"] = (
                    OLS(
                        data["expression"],
                        data[["intercept", "genotype", "covariate1"]],
                    )
                    .fit()
                    .resid
                )
                data["expression2"] = (
                    OLS(
                        data["expression"],
                        data[["intercept", "genotype", "covariate2"]],
                    )
                    .fit()
                    .resid
                )

                # Force normalise.
                for dataset in data["dataset"].unique():
                    sample_mask = (data["dataset"] == dataset).to_numpy(
                        dtype=bool
                    )
                    data.loc[sample_mask, "expression1"] = ndtri(
                        (
                            data.loc[sample_mask, "expression1"].rank(
                                ascending=True
                            )
                            - 0.5
                        )
                        / np.sum(sample_mask)
                    )
                    data.loc[sample_mask, "covariate1"] = ndtri(
                        (
                            data.loc[sample_mask, "covariate1"].rank(
                                ascending=True
                            )
                            - 0.5
                        )
                        / np.sum(sample_mask)
                    )

                    data.loc[sample_mask, "expression2"] = ndtri(
                        (
                            data.loc[sample_mask, "expression2"].rank(
                                ascending=True
                            )
                            - 0.5
                        )
                        / np.sum(sample_mask)
                    )
                    data.loc[sample_mask, "covariate2"] = ndtri(
                        (
                            data.loc[sample_mask, "covariate2"].rank(
                                ascending=True
                            )
                            - 0.5
                        )
                        / np.sum(sample_mask)
                    )

                # Get the allele data.
                alleles = alleles_df.iloc[row_index, :]
                major_allele = alleles["Alleles"].split("/")[0]
                minor_allele = alleles["Alleles"].split("/")[1]

                # Add the interaction terms.
                data["interaction1"] = data["genotype"] * data["covariate1"]
                data["interaction2"] = data["genotype"] * data["covariate2"]

                # Calculate the annotations.
                counts = data["group"].value_counts()
                for x in [0.0, 1.0, 2.0]:
                    if x not in counts:
                        counts.loc[x] = 0
                zero_geno_count = (counts[0.0] * 2) + counts[1.0]
                two_geno_count = (counts[2.0] * 2) + counts[1.0]
                minor_allele_frequency = min(
                    zero_geno_count, two_geno_count
                ) / (zero_geno_count + two_geno_count)
                (
                    eqtl_pvalue1,
                    eqtl_pearsonr1,
                    interaction_pvalue1,
                    context_genotype_r1,
                ) = self.calculate_annot(data=data, suffix="1")
                (
                    eqtl_pvalue2,
                    eqtl_pearsonr2,
                    interaction_pvalue2,
                    context_genotype_r2,
                ) = self.calculate_annot(data=data, suffix="2")

                # Fill the interaction plot annotation.
                annot1 = [
                    "eQTL p-value: {}".format(eqtl_pvalue1),
                    "eQTL r: {:.2f}".format(eqtl_pearsonr1),
                    "interaction p-value: {}".format(interaction_pvalue1),
                    "context - genotype r: {:.2f}".format(context_genotype_r1),
                ]
                annot2 = [
                    "eQTL p-value: {}".format(eqtl_pvalue2),
                    "eQTL r: {:.2f}".format(eqtl_pearsonr2),
                    "interaction p-value: {}".format(interaction_pvalue2),
                    "context - genotype r: {:.2f}".format(context_genotype_r2),
                ]

                allele_map = {
                    0.0: "{}/{}".format(major_allele, major_allele),
                    1.0: "{}/{}".format(major_allele, minor_allele),
                    2.0: "{}/{}".format(minor_allele, minor_allele),
                }

                print_probe_name = probe_name
                if "." in print_probe_name:
                    print_probe_name = print_probe_name.split(".")[0]

                print_snp_name = snp_name
                if ":" in print_snp_name:
                    print_snp_name = print_snp_name.split(":")[2]

                # Plot the double interaction eQTL.
                self.double_inter_plot(
                    df=data,
                    x1="covariate1",
                    x2="covariate2",
                    y1="expression1",
                    y2="expression2",
                    group="group",
                    palette=self.palette,
                    allele_map=allele_map,
                    xlabel1=cov1,
                    xlabel2=cov2,
                    title="{} [{}] - {}\n MAF={:.2f}  n={:,}".format(
                        print_snp_name,
                        minor_allele,
                        print_probe_name,
                        minor_allele_frequency,
                        data.shape[0],
                    ),
                    annot1=annot1,
                    annot2=annot2,
                    ylabel="{} expression".format(print_probe_name),
                    filename="{}_{}_{}_{}_{}".format(
                        row_index, print_probe_name, print_snp_name, cov1, cov2
                    ),
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
    def construct_dataset_df(std_df):
        dataset_sample_counts = list(
            zip(*np.unique(std_df.iloc[:, 1], return_counts=True))
        )
        dataset_sample_counts.sort(key=lambda x: -x[1])
        datasets = [csc[0] for csc in dataset_sample_counts]

        dataset_df = pd.DataFrame(0, index=std_df.iloc[:, 0], columns=datasets)
        for dataset in datasets:
            dataset_df.loc[(std_df.iloc[:, 1] == dataset).values, dataset] = 1
        dataset_df.index.name = "-"

        return dataset_df

    @staticmethod
    def load_tech_cov(df, name, std_df):
        if df is None:
            return None, []

        n_samples = std_df.shape[0]

        print(
            "\tWorking on technical covariates matrix matrix '{}'".format(name)
        )

        # Check for nan values.
        if df.isna().values.sum() > 0:
            print("\t  Matrix contains nan values")
            exit()

        # Put the samples on the rows.
        if df.shape[1] == n_samples:
            print("\t  Transposing matrix")
            df = df.T

        # Check for variables with zero std.
        variance_mask = df.std(axis=0) != 0
        n_zero_variance = variance_mask.shape[0] - variance_mask.sum()
        if n_zero_variance > 0:
            print(
                "\t  Dropping {} rows with 0 variance".format(n_zero_variance)
            )
            df = df.loc[:, variance_mask]

        # Convert to numpy.
        m = df.to_numpy(np.float64)
        columns = df.columns.tolist()
        del df

        covariates = columns
        print(
            "\t  Technical covariates [{}]: {}".format(
                len(covariates), ", ".join(covariates)
            )
        )

        return m, covariates

    @staticmethod
    def construct_correct_matrices(
        dataset_m,
        dataset_labels,
        tcov_m,
        tcov_labels,
        tcov_inter_m,
        tcov_inter_labels,
    ):
        # Create the correction matrices.
        corr_m = None
        corr_m_columns = ["Intercept"]
        corr_inter_m = None
        corr_inter_m_columns = []
        if dataset_m.shape[1] > 1:
            # Note that for the interaction term we need to include all
            # datasets.
            corr_m = np.copy(dataset_m[:, 1:])
            corr_m_columns.extend(dataset_labels[1:])

            corr_inter_m = np.copy(dataset_m)
            corr_inter_m_columns.extend(
                ["{} x Genotype".format(label) for label in dataset_labels]
            )

        if tcov_m is not None:
            corr_m_columns.extend(tcov_labels)
            if corr_m is not None:
                corr_m = np.hstack((corr_m, tcov_m))
            else:
                corr_m = tcov_m

        if tcov_inter_m is not None:
            corr_m_columns.extend(tcov_inter_labels)
            if corr_m is not None:
                corr_m = np.hstack((corr_m, tcov_inter_m))
            else:
                corr_m = tcov_inter_m

            corr_inter_m_columns.extend(
                ["{} x Genotype".format(label) for label in tcov_inter_labels]
            )
            if corr_inter_m is not None:
                corr_inter_m = np.hstack((corr_inter_m, tcov_inter_m))
            else:
                corr_inter_m = tcov_inter_m

        return corr_m, corr_inter_m, corr_m_columns + corr_inter_m_columns

    @staticmethod
    def calculate_annot(data, suffix=""):
        eqtl_pvalue = (
            OLS(
                data["expression{}".format(suffix)],
                data[["intercept", "genotype"]],
            )
            .fit()
            .pvalues[1]
        )
        eqtl_pvalue_str = "{:.2e}".format(eqtl_pvalue)
        if eqtl_pvalue == 0:
            eqtl_pvalue_str = "<{:.1e}".format(1e-308)
        eqtl_pearsonr, _ = stats.pearsonr(
            data["expression{}".format(suffix)], data["genotype"]
        )

        interaction_pvalue = (
            OLS(
                data["expression{}".format(suffix)],
                data[
                    [
                        "intercept",
                        "genotype",
                        "covariate{}".format(suffix),
                        "interaction{}".format(suffix),
                    ]
                ],
            )
            .fit()
            .pvalues[3]
        )
        interaction_pvalue_str = "{:.2e}".format(interaction_pvalue)
        if interaction_pvalue == 0:
            interaction_pvalue_str = "<{:.1e}".format(1e-308)

        context_genotype_r, _ = stats.pearsonr(
            data["genotype"], data["covariate{}".format(suffix)]
        )

        return (
            eqtl_pvalue_str,
            eqtl_pearsonr,
            interaction_pvalue_str,
            context_genotype_r,
        )

    def double_inter_plot(
        self,
        df,
        x1="x1",
        x2="x2",
        y1="y1",
        y2="y2",
        group="group",
        palette=None,
        allele_map=None,
        xlabel1="",
        xlabel2="",
        annot1=None,
        annot2=None,
        ylabel="",
        title="",
        filename="ieqtl_plot",
    ):
        if len(set(df[group].unique()).symmetric_difference({0, 1, 2})) > 0:
            return

        fig, axes = plt.subplots(
            nrows=1, ncols=2, sharex="none", sharey="all", figsize=(24, 12)
        )
        sns.set(color_codes=True)
        sns.set_style("ticks")
        sns.despine(fig=fig, ax=axes[0])
        sns.despine(fig=fig, ax=axes[1])

        self.inter_plot(
            ax=axes[0],
            df=df,
            x=x1,
            y=y1,
            group=group,
            palette=palette,
            allele_map=allele_map,
            annot=annot1,
            xlabel=xlabel1,
            ylabel=ylabel,
        )

        self.inter_plot(
            ax=axes[1],
            df=df,
            x=x2,
            y=y2,
            group=group,
            palette=palette,
            allele_map=allele_map,
            annot=annot2,
            xlabel=xlabel2,
            ylabel=ylabel,
        )

        fig.suptitle(title, fontsize=25, fontweight="bold")

        for extension in self.extensions:
            outpath = os.path.join(
                self.outdir, "{}.{}".format(filename, extension)
            )
            print("\t\tSaving plot: {}".format(os.path.basename(outpath)))
            fig.savefig(outpath)
        plt.close()

    @staticmethod
    def inter_plot(
        ax,
        df,
        x="x",
        y="y",
        group="group",
        palette=None,
        allele_map=None,
        annot=None,
        xlabel="",
        ylabel="",
        title="",
    ):
        for i, group_id in enumerate([0, 1, 2]):
            subset = df.loc[df[group] == group_id, :].copy()
            allele = group_id
            if allele_map is not None:
                allele = allele_map[group_id]

            coef_str = "NA"
            r_annot_pos = (-1, -1)
            if len(subset.index) > 1:
                coef, p = stats.pearsonr(subset[y], subset[x])
                coef_str = "{:.2f}".format(coef)

                subset["intercept"] = 1
                betas = (
                    np.linalg.inv(
                        subset[["intercept", x]].T.dot(subset[["intercept", x]])
                    )
                    .dot(subset[["intercept", x]].T)
                    .dot(subset[y])
                )
                subset["y_hat"] = np.dot(subset[["intercept", x]], betas)
                subset.sort_values(x, inplace=True)

                r_annot_pos = (
                    subset.iloc[-1, :][x] + (subset[x].max() * 0.05),
                    subset.iloc[-1, :]["y_hat"],
                )

                sns.regplot(
                    x=x,
                    y=y,
                    data=subset,
                    ci=None,
                    scatter_kws={
                        "facecolors": palette[group_id],
                        "linewidth": 0,
                        "alpha": 0.60,
                    },
                    line_kws={
                        "color": palette[group_id],
                        "linewidth": 5,
                        "alpha": 1,
                    },
                    ax=ax,
                )

            ax.annotate(
                "{}\n{}".format(allele, coef_str),
                xy=r_annot_pos,
                color=palette[group_id],
                alpha=0.75,
                fontsize=22,
                fontweight="bold",
            )

        if annot is not None:
            for i, annot_label in enumerate(annot):
                ax.annotate(
                    annot_label,
                    xy=(0.03, 0.94 - (i * 0.04)),
                    xycoords=ax.transAxes,
                    color="#000000",
                    alpha=0.75,
                    fontsize=20,
                    fontweight="bold",
                )

        (xmin, xmax) = (df[x].min(), df[x].max())
        (ymin, ymax) = (df[y].min(), df[y].max())
        xmargin = (xmax - xmin) * 0.05
        ymargin = (ymax - ymin) * 0.05

        ax.set_xlim(xmin - xmargin, xmax + xmargin)
        ax.set_ylim(ymin - ymargin, ymax + ymargin)

        ax.set_title(title, fontsize=22, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=20, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=20, fontweight="bold")

    def print_arguments(self):
        print("Arguments:")
        print("  > PICALO base path: {}".format(self.picalo_path))
        print("  > Genotype input path: {}".format(self.geno_path))
        print("  > Alleles path: {}".format(self.alleles_path))
        print("  > Expression input path: {}".format(self.expr_path))
        print("  > Technical covariates input path: {}".format(self.tcov_path))
        print(
            "  > Technical covariates with interaction input path: {}".format(
                self.tcov_inter_path
            )
        )
        print("  > Sample-dataset path: {}".format(self.std_path))
        print("  > Min. dataset size: {}".format(self.min_dataset_size))
        print("  > Genotype NA value: {}".format(self.genotype_na))
        print("  > SNP call rate: >{}".format(self.call_rate))
        print("  > Interest: {}".format(self.interest))
        print("  > Nrows: {}".format(self.nrows))
        print("  > Extension: {}".format(self.extensions))
        print("  > Output directory: {}".format(self.outdir))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
