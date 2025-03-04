#!/usr/bin/env python3

"""
File:         visualise_results_metabrain.py
Created:      2021/05/06
Last Changed: 2022/03/25
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function

import argparse
import glob
import os
import subprocess
import sys

# Third party imports.
import pandas as pd

# Local application imports.

# Metadata
__program__ = "Visualise Results MetaBrain"
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
./visualise_results_metabrain.py -h
"""


class main:
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.input_data_path = getattr(arguments, "input_data")
        self.pf_path = getattr(arguments, "picalo_files")
        self.expression_preprocessing_path = getattr(
            arguments, "expression_preprocessing_dir"
        )
        self.palette_path = getattr(arguments, "palette")
        self.outname = getattr(arguments, "outname")
        self.extensions = getattr(arguments, "extensions")

        # Set variables.
        # self.outdir = os.path.join(
        #     str(os.path.dirname(os.path.abspath(__file__))), "plot"
        # )
        print(os.getcwd())
        self.outdir = "my_little_plots"
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

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
            "-id",
            "--input_data",
            type=str,
            required=True,
            help="The path to PICALO results.",
        )
        parser.add_argument(
            "-pf",
            "--picalo_files",
            type=str,
            required=True,
            help="The path to the picalo files.",
        )
        parser.add_argument(
            "-ep",
            "--expression_preprocessing_dir",
            type=str,
            required=True,
            help="The path to the expression preprocessing data.",
        )
        parser.add_argument(
            "-p",
            "--palette",
            type=str,
            required=True,
            help="The path to a json file with the"
            "dataset to color combinations.",
        )
        parser.add_argument(
            "-o",
            "--outname",
            type=str,
            required=True,
            help="The name of the output files.",
        )
        parser.add_argument(
            "-e",
            "--extensions",
            type=str,
            nargs="+",
            default=["png"],
            choices=[
                "eps",
                "pdf",
                "pgf",
                "png",
                "ps",
                "raw",
                "rgba",
                "svg",
                "svgz",
            ],
            help="The output file format(s), default: ['png']",
        )

        return parser.parse_args()

    def start(self):
        print("Visualise metabrain results arguments:")
        self.print_arguments()
        plot_scripts_dir = "PICALO/dev/general/plot_scripts/"

        # lineplot_log10_sum_abs_normalized_delta_log_likelihood
        # lineplot_min_n_per_sample
        # lineplot_n_overlap
        # lineplot_n
        # lineplot_overlap_%
        # lineplot_pearson_r
        # lineplot_sum_abs_normalized_delta_log_likelihood

        # Plot overview lineplot.
        command = [
            "python3",
            f"{plot_scripts_dir}overview_lineplot_bar2.py",
            "-i",
            self.input_data_path,
            # "-p",
            # self.palette_path,
            "-o",
            self.outname,
        ]
        print("\n\n1\n\n")
        # self.run_command(command)
        # sys.exit(0)

        # covariate_selection_lineplot

        # Plot covariate selection overview lineplot.
        command = [
            "python3",
            f"{plot_scripts_dir}covariate_selection_lineplot.py",
            "-i",
            self.input_data_path,
            "-p",
            self.palette_path,
            "-o",
            self.outname,
        ]
        print("\n\n2\n\n")
        # self.run_command(command)

        # GenotypeStats_histplot_0.png
        # GenotypeStats_histplot_1.png
        # GenotypeStats_histplot_2.png
        # GenotypeStats_histplot_allele1.png
        # GenotypeStats_histplot_allele2.png
        # GenotypeStats_histplot_hw pval.png
        # GenotypeStats_histplot_ma.png
        # GenotypeStats_histplot_maf.png
        # GenotypeStats_histplot_min gs.png
        # GenotypeStats_histplot_n.png
        # GenotypeStats_histplot_nan.png

        # Plot genotype stats.
        command = [
            "python3",
            f"{plot_scripts_dir}create_histplot.py",
            "-d",
            os.path.join(self.input_data_path, "genotype_stats.txt.gz"),
            "-o",
            self.outname + "_GenotypeStats",
        ]
        print("\n\n3\n\n")
        # self.run_command(command)

        # PIC10_lineplot.png
        # PIC1_lineplot.png
        # PIC2_lineplot.png
        # PIC3_lineplot.png
        # PIC4_lineplot.png
        # PIC5_lineplot.png
        # PIC6_lineplot.png
        # PIC7_lineplot.png
        # PIC8_lineplot.png
        # PIC9_lineplot.png
        # PICS_upsetplot.png
        # included_ieQTLs_PIC10_upsetplot.png
        # included_ieQTLs_PIC1_upsetplot.png
        # included_ieQTLs_PIC2_upsetplot.png
        # included_ieQTLs_PIC3_upsetplot.png
        # included_ieQTLs_PIC4_upsetplot.png
        # included_ieQTLs_PIC5_upsetplot.png
        # included_ieQTLs_PIC6_upsetplot.png
        # included_ieQTLs_PIC7_upsetplot.png
        # included_ieQTLs_PIC8_upsetplot.png
        # included_ieQTLs_PIC9_upsetplot.png

        # Plot eQTL upsetplot.
        command = [
            "python3",
            f"{plot_scripts_dir}create_upsetplot.py",
            "-i",
            self.input_data_path,
            "-e",
            os.path.join(
                self.pf_path, "eQTLProbesFDR0.05-ProbeLevel-Available.txt.gz"
            ),
            "-p",
            self.palette_path,
            "-o",
            self.outname,
        ]
        print("\n\n4\n\n")
        # self.run_command(command)

        # interaction_barplot.png
        # interaction_pieplot.png

        # Plot interaction overview plot.
        command = [
            "python3",
            f"{plot_scripts_dir}interaction_overview_plot.py",
            "-i",
            self.input_data_path,
            "-p",
            self.palette_path,
            "-o",
            self.outname,
        ]
        # print("\n\n5\n\n")
        # self.run_command(command)

        # Plot #ieQTLs per sample boxplot.
        command = [
            "python3",
            f"{plot_scripts_dir}no_ieqtls_per_sample_plot.py",
            "-i",
            self.input_data_path,
            "-p",
            self.palette_path,
            "-o",
            self.outname,
        ]
        print("\n\n6\n\n")
        # self.run_command(command)

        pics = []
        last_iter_fpaths = []
        for i in range(1, 23):
            pic = "PIC{}".format(i)
            comp_iterations_path = os.path.join(
                self.input_data_path, pic, "iteration.txt.gz"
            )

            if os.path.exists(comp_iterations_path):
                pics.append(pic)
                fpaths = glob.glob(
                    os.path.join(
                        self.input_data_path, pic, "results_iteration*"
                    )
                )
                fpaths.sort()
                print("fpaths")
                print(fpaths)
                last_iter_fpaths.append(fpaths[-1])

                # Plot scatterplot.
                command = [
                    "python3",
                    f"{plot_scripts_dir}create_scatterplot.py",
                    "-d",
                    comp_iterations_path,
                    "-hr",
                    "0",
                    "-ic",
                    "0",
                    "-a",
                    "1",
                    "-std",
                    os.path.join(self.pf_path, "sample_to_dataset.txt.gz"),
                    "-p",
                    self.palette_path,
                    "-o",
                    self.outname + "_PIC{}".format(i),
                ]
                # self.run_command(command)

                # Plot correlation_heatmap of iterations.
                command = [
                    "python3",
                    f"{plot_scripts_dir}create_correlation_heatmap.py",
                    "-rd",
                    comp_iterations_path,
                    "-rn",
                    self.outname,
                    "-o",
                    self.outname + "_{}".format(pic),
                ]
                # self.run_command(command)

        # Compare iterative t-values .
        command = (
            ["python3", f"{plot_scripts_dir}compare_tvalues.py", "-d"]
            + last_iter_fpaths[:5]
            + ["-n"]
            + pics[:5]
            + ["-o", self.outname + "_IterativeTValuesOverview"]
        )
        # self.run_command(command)

        # Create components_df if not exists.
        components_path = os.path.join(
            self.input_data_path, "components.txt.gz"
        )
        if not os.path.exists(components_path):
            print("Components file does not exists, loading iteration files")
            data = []
            columns = []
            for i in range(1, 50):
                pic = "PIC{}".format(i)
                comp_iterations_path = os.path.join(
                    self.input_data_path, pic, "iteration.txt.gz"
                )
                if os.path.exists(comp_iterations_path):
                    df = self.load_file(
                        comp_iterations_path, header=0, index_col=0
                    )
                    last_iter = df.iloc[[df.shape[0] - 1], :].T
                    data.append(last_iter)
                    columns.append(pic)

            if len(data) > 0:
                components_df = pd.concat(data, axis=1)
                components_df.columns = columns
                self.save_file(
                    components_df.T,
                    outpath=components_path,
                    header=True,
                    index=True,
                )

        # Plot comparison to expression mean correlation.
        for pic in pics:
            command = [
                "python3",
                f"{plot_scripts_dir}create_regplot.py",
                "-xd",
                components_path,
                "-xi",
                pic,
                "-yd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/tmp01/output/2020-11-10-PICALO/preprocess_scripts/correlate_samples_with_avg_gene_expression/MetaBrain_CorrelationsWithAverageExpression.txt.gz",
                "/groups/umcg-biogen/tmp04/output/2024-MetaBrainV2dot1-PICALO/2024-10-16-BulkSingleCellIntegration/PICALO/dev/general/preprocess_scripts/correlate_samples_with_avg_gene_expression/MetaBrain_CorrelationsWithAverageExpression.txt.gz",
                "-y_transpose",
                "-yi",
                "AvgExprCorrelation",
                "-std",
                os.path.join(self.pf_path, "sample_to_dataset.txt.gz"),
                "-p",
                self.palette_path,
                "-o",
                self.outname + "_{}_vs_AvgExprCorrelation".format(pic),
            ]
            # self.run_command(command)

        # Check for which PICs we have the interaction stats.
        pics = []
        pic_interactions_fpaths = []
        for i in range(1, 6):
            pic = "PIC{}".format(i)
            fpath = os.path.join(
                self.input_data_path,
                "PIC_interactions",
                "{}.txt.gz".format(pic),
            )
            if os.path.exists(fpath):
                pics.append(pic)
                pic_interactions_fpaths.append(fpath)

        if len(pic_interactions_fpaths) > 0:
            # Compare t-values.
            command = (
                ["python3", f"{plot_scripts_dir}compare_tvalues.py", "-d"]
                + pic_interactions_fpaths
                + ["-n"]
                + pics
                + ["-o", "{}_TValuesOverview".format(self.outname)]
            )
            # self.run_command(command)

        # Plot comparison scatterplot.
        command = [
            "python3",
            f"{plot_scripts_dir}create_comparison_scatterplot.py",
            "-d",
            components_path,
            "-transpose",
            "-std",
            os.path.join(self.pf_path, "sample_to_dataset.txt.gz"),
            "-n",
            "5",
            "-p",
            self.palette_path,
            "-o",
            self.outname + "_ColoredByDataset",
        ]
        # self.run_command(command)

        # Plot comparison scatterplot.
        command = [
            "python3",
            f"{plot_scripts_dir}create_comparison_scatterplot.py",
            "-d",
            components_path,
            "-transpose",
            "-std",
            # WARN: hardcoded path, replace with my sex file
            "data/sex.txt.gz",
            "-n",
            "5",
            "-p",
            self.palette_path,
            "-o",
            self.outname + "_ColoredBySex",
        ]
        # self.run_command(command)

        if os.path.exists(components_path):
            # Plot correlation_heatmap of components.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-o",
                self.outname,
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs expression correlations.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/tmp01/output/2020-11-10-PICALO/preprocess_scripts/correlate_samples_with_avg_gene_expression/MetaBrain_CorrelationsWithAverageExpression.txt.gz",
                "/groups/umcg-biogen/tmp04/output/2024-MetaBrainV2dot1-PICALO/2024-10-16-BulkSingleCellIntegration/PICALO/dev/general/preprocess_scripts/correlate_samples_with_avg_gene_expression/MetaBrain_CorrelationsWithAverageExpression.txt.gz",
                "-cn",
                "AvgExprCorrelation",
                "-o",
                self.outname + "_vs_AvgExprCorrelation",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs datasets.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                os.path.join(self.pf_path, "datasets_table.txt.gz"),
                "-cn",
                "datasets",
                "-o",
                self.outname + "_vs_Datasets",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs RNA alignment metrics.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/tmp01/output/2020-11-10-PICALO/data/2020-02-05-freeze2dot1.TMM.Covariates.withBrainRegion-noncategorical-variable.txt.gz",
                # this one for me:
                "/groups/umcg-biogen/tmp04/output/2024-MetaBrainV2dot1-PICALO/2024-10-16-BulkSingleCellIntegration/data/2020-02-05-freeze2dot1.TMM.Covariates.withBrainRegion-noncategorical-variable.txt.gz",
                "-cn",
                "RNAseq alignment metrics",
                "-o",
                self.outname + "_vs_RNASeqAlignmentMetrics",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs Sex.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path, replace with my sex file
                "data/sex.txt.gz",
                "-cn",
                "Sex",
                "-o",
                self.outname + "_vs_Sex",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs MDS.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                os.path.join(self.pf_path, "mds_table.txt.gz"),
                "-cn",
                "MDS",
                "-o",
                self.outname + "_vs_MDS",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs PCA without cov correction.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path, werkt maybe gewoon
                os.path.join(
                    self.expression_preprocessing_path,
                    "data",
                    # "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1.SampleSelection.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.PCAOverSamplesEigenvectors.txt.gz",
                    "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1-filtered.ProbesWithZeroVarianceRemoved.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.PCAOverSamplesEigenvectors.txt.gz",
                ),
                "-cn",
                "PCA before cov. corr.",
                "-o",
                self.outname + "_vs_PCABeforeCorrection",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs PCA with cov correction.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path, werkt maybe gewoon
                os.path.join(
                    self.expression_preprocessing_path,
                    "data",
                    # "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1.SampleSelection.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.CovariatesRemovedOLS.ScaleAndLocReturned.PCAOverSamplesEigenvectors.txt.gz",
                    "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1-filtered.ProbesWithZeroVarianceRemoved.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.CovariatesRemovedOLS.ScaleAndLocReturned.PCAOverSamplesEigenvectors.txt.gz",
                ),
                "-cn",
                "PCA after cov. corr.",
                "-o",
                self.outname + "_vs_PCAAfterCorrection",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs PCA with centering and cov correction.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path, werkt maybe gewoon
                os.path.join(
                    self.expression_preprocessing_path,
                    "data",
                    # "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1.SampleSelection.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.ProbesCentered.SamplesZTransformed.PCAOverSamplesEigenvectors.txt.gz",
                    "MetaBrain.allCohorts.2020-02-16.TMM.freeze2dot1-filtered.ProbesWithZeroVarianceRemoved.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.ProbesCentered.SamplesZTransformed.PCAOverSamplesEigenvectors.txt.gz",
                ),
                "-cn",
                "PCA centered after cov. corr.",
                "-o",
                self.outname + "_vs_PCACenteredAfterCorrection",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs cell fraction summarized.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/prm03/projects/2022-DeKleinEtAl/output/2020-10-12-deconvolution/deconvolution/matrix_preparation/2022-01-21-CortexEUR-cis-NegativeToZero-DatasetAndRAMCorrected/perform_deconvolution/deconvolution_table.txt.gz",
                "data/deconvolution_table.txt.gz",
                "-cn",
                "cell fractions",
                "-o",
                self.outname + "_vs_CellFractionSummarized",
                "-e",
                "png",
                "pdf",
            ]
            # self.run_command(command)

            # Plot correlation_heatmap of components vs cell fraction complete.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/prm03/projects/2022-DeKleinEtAl/output/2020-10-12-deconvolution/deconvolution/matrix_preparation/2022-01-21-CortexEUR-cis-NegativeToZero-DatasetAndRAMCorrected/perform_deconvolution/deconvolution_table_complete.txt.gz",
                "data/deconvolution_table.txt.gz",
                "-cn",
                "cell fractions",
                "-o",
                self.outname + "_vs_CellFractionComplete",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs IHC counts.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/prm03/projects/2022-DeKleinEtAl/output/2020-10-12-deconvolution/deconvolution/data/AMP-AD/IHC_counts.txt.gz",
                "data/IHC_counts.txt.gz",
                "-cn",
                "IHC counts",
                "-o",
                self.outname + "_vs_IHC",
                "-e",
            ] + self.extensions
            # self.run_command(command)

            # Plot correlation_heatmap of components vs single cell counts.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/prm03/projects/2022-DeKleinEtAl/output/2020-10-12-deconvolution/deconvolution/data/AMP-AD/single_cell_counts.txt.gz",
                "data/single_cell_counts.txt.gz",
                "-cn",
                "SCC",
                "-o",
                self.outname + "_vs_SCC",
                "-e",
            ] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs phenotypes.
            command = [
                "python3",
                f"{plot_scripts_dir}create_correlation_heatmap.py",
                "-rd",
                components_path,
                "-rn",
                self.outname,
                "-cd",
                # WARN: hardcoded path
                # "/groups/umcg-biogen/tmp01/output/2020-11-10-PICALO/preprocess_scripts/prepare_metabrain_phenotype_matrix/MetaBrain_phenotypes.txt.gz",
                # this one for me:
                "/groups/umcg-biogen/tmp04/output/2024-MetaBrainV2dot1-PICALO/2024-10-16-BulkSingleCellIntegration/data/MetaBrain_phenotypes.txt.gz",
                "-cn",
                "phenotypes",
                "-o",
                self.outname + "_vs_Phenotypes",
                "-e",
            ] + self.extensions
            # self.run_command(command)

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
    def save_file(df, outpath, header=True, index=False, sep="\t"):
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

    @staticmethod
    def run_command(command):
        print(" ".join(command))
        subprocess.call(command)

    def print_arguments(self):
        print("Arguments:")
        print("  > Input data path: {}".format(self.input_data_path))
        print("  > Picalo files path: {}".format(self.pf_path))
        print(
            "  > Expression pre-processing data path: {}".format(
                self.expression_preprocessing_path
            )
        )
        print("  > Palette path: {}".format(self.palette_path))
        print("  > Outname {}".format(self.outname))
        print("  > Output directory {}".format(self.outdir))
        print("  > Extensions: {}".format(self.extensions))
        print("")


if __name__ == "__main__":
    m = main()
    m.start()
