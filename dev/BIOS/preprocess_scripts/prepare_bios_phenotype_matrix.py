#!/usr/bin/env python3

"""
File:         prepare_bios_phenotype_matrix.py
Created:      2021/11/10
Last Changed: 2022/03/18
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function
import os

# Third party imports.
import pandas as pd
import numpy as np

# Local application imports.

# Metadata
__program__ = "Prepare BIOS Phenotype Matrix"
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
./prepare_bios_phenotype_matrix.py -h
"""


class main:
    def __init__(self):
        self.pheno_path = (
            "/groups/umcg-bios/tmp01/projects/PICALO/data/BIOS_RNA_pheno.txt.gz"
        )

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))),
            "prepare_bios_phenotype_matrix",
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    def start(self):
        df = self.load_file(self.pheno_path, index_col=3, header=0)
        df.index.name = None

        rna_alignment_columns = []
        cf_perc_columns = []
        cc_columns = []
        blood_stats_columns = []
        other_columns = []
        encoded_dfs = []
        for column in df.columns:
            if column in [
                "uuid",
                "gonl_id",
                "star.start_mapping_time",
                "RNA_Extraction_Method",
                "LDLcholMethod",
                "Sampling_Time",
                "Sampling_Date",
                "imputation_id",
                "GWAS_DataGeneration_Date",
                "RNA_Extraction_Date",
                "DNA_Extraction_Date",
                "star.end_time",
                "star.start_job_time",
                "star.pct_unmapped_mismatch",
                "bam.exon_duplicates",
            ]:
                continue

            if (
                column.startswith("star")
                or column.startswith("bam")
                or column.startswith("fastqc")
                or column.startswith("prime_bias")
            ):
                rna_alignment_columns.append(column)
            elif column.endswith("_Perc"):
                cf_perc_columns.append(column)
            elif column in [
                "Mono",
                "Lymph",
                "Granulocyte",
                "Baso",
                "Eos",
                "Neut",
                "LUC",
                "WBC",
                "RBC",
                "PLT",
            ]:
                cc_columns.append(column)
            elif column in ["RDW", "HCT", "HGB", "MCHC", "MPV", "MCH", "MCV"]:
                blood_stats_columns.append(column)
            else:
                if column in [
                    "biobank_id",
                    "LipidMed",
                    "DNA_Extraction_Method",
                    "RNA_Source",
                    "DNA_QuantificationMethod",
                    "DNA_Source",
                    "Smoking",
                    "GWAS_Chip",
                    "Ascertainment_criterion",
                ]:
                    encoded_dfs.append(self.to_dummies(column=column, row=df[column]))
                elif column in ["Sex", "Lipids_BloodSampling_Fasting"]:
                    codes, _ = pd.factorize(df[column])
                    encoded_df = pd.Series(codes, index=df.index).to_frame()
                    encoded_df.columns = [column]
                    encoded_df[encoded_df == -1] = np.nan
                    encoded_dfs.append(encoded_df)
                else:
                    other_columns.append(column)

        rna_alignment_df = df.loc[:, rna_alignment_columns]
        self.save_file(
            df=rna_alignment_df,
            outpath=os.path.join(self.outdir, "BIOS_RNA_AlignmentMetrics.txt.gz"),
        )
        del rna_alignment_df

        incl_rna_alignmnt_df = df.loc[
            :,
            [
                "fastqc_clean.R1_clean_GC_mean",
                "fastqc_raw.R1_raw_GC_mean",
                "fastqc_clean.R2_clean_GC_mean",
                "fastqc_clean.R1_clean_GC_std",
                "fastqc_clean.R2_clean_GC_std",
                "fastqc_raw.R2_raw_GC_mean",
                "fastqc_raw.R1_raw_GC_std",
                "prime_bias.MEDIAN_5PRIME_BIAS",
                "fastqc_raw.R2_raw_GC_std",
                "prime_bias.MEDIAN_5PRIME_TO_3PRIME_BIAS",
                "star.pct_mapped_many",
                "star.pct_mapped_multiple",
                "bam.genome_total",
                "star.num_input",
                "bam.genome_mapped",
                "star.num_unique_mapped",
                "star.rate_insertion_per_base",
                "star.avg_insertion_length",
                "star.num_mapped_many",
                "bam.genome_insert_std",
            ],
        ]
        self.save_file(
            df=incl_rna_alignmnt_df,
            outpath=os.path.join(
                self.outdir, "BIOS_CorrectionIncluded_RNA_AlignmentMetrics.txt.gz"
            ),
        )
        del incl_rna_alignmnt_df

        cf_perc_df = df.loc[:, cf_perc_columns].copy()
        cf_perc_df.dropna(axis=0, how="all", inplace=True)
        cf_perc_df = cf_perc_df.reindex(sorted(cf_perc_df.columns), axis=1)
        self.save_file(
            df=cf_perc_df,
            outpath=os.path.join(self.outdir, "BIOS_CellFractionPercentages.txt.gz"),
        )
        del cf_perc_df

        cc_df = df.loc[:, cc_columns].copy()
        cc_df.dropna(axis=0, how="all", inplace=True)
        cc_df = cc_df.reindex(sorted(cc_df.columns), axis=1)
        cc_df["sum"] = cc_df.sum(axis=1)
        self.save_file(
            df=cc_df, outpath=os.path.join(self.outdir, "BIOS_CellCounts.txt.gz")
        )
        del cc_df

        bs_df = df.loc[:, blood_stats_columns].copy()
        bs_df.dropna(axis=0, how="all", inplace=True)
        bs_df = bs_df.reindex(sorted(bs_df.columns), axis=1)
        self.save_file(
            df=bs_df, outpath=os.path.join(self.outdir, "BIOS_BloodStats.txt.gz")
        )
        del bs_df

        other_df = df.loc[:, other_columns].copy()
        encoded_df = pd.concat(encoded_dfs, axis=1)
        other_df = other_df.merge(encoded_df, left_index=True, right_index=True)
        self.save_file(
            df=other_df, outpath=os.path.join(self.outdir, "BIOS_phenotypes.txt.gz")
        )
        del other_df

        sex_df = encoded_df.loc[:, ["Sex"]].copy()
        sex_df.dropna(inplace=True)
        self.save_file(df=sex_df, outpath=os.path.join(self.outdir, "BIOS_sex.txt.gz"))
        del sex_df, encoded_df

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
    def to_dummies(column, row):
        dummies = pd.get_dummies(row)
        dummies.columns = [
            "{}-{}".format(column, colname) for colname in dummies.columns
        ]

        return dummies

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


if __name__ == "__main__":
    m = main()
    m.start()
