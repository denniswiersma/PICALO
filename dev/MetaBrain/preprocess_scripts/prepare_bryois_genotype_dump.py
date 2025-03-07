#!/usr/bin/env python3

"""
File:         prepare_bryois_genotype_dump.py
Created:      2022/01/26
Last Changed: 2022/02/10
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

# Local application imports.

# Metadata
__program__ = "Prepare Bryois Genotype Dump"
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
./prepare_bryois_genotype_dump.py -h 
"""


class main:
    def __init__(self):
        self.bryois_path = "/groups/umcg-biogen/tmp01/output/2019-11-06-FreezeTwoDotOne/2020-10-12-deconvolution/deconvolution/data/julienbryois2021/media-3.xlsx"
        self.snps_indir = "/groups/umcg-biogen/tmp01/input/GENOTYPES/MAFFilteredSorted/"
        self.datasets = [
            "NABEC-Human550",
            "GVEX-V2",
            "LIBD-h650",
            "UCLA-ASD",
            "NABEC-Human610",
            "BrainGVEX-V2",
            "CMC",
            "LIBD-1M",
            "CMC-set2",
            "TargetALS",
            "AMPAD-ROSMAP",
            "GTEX-WGS",
            "AMPAD-MAYO",
            "AMPAD-MSBB",
            "2020-01-08-ENA-genotypes",
            "LIBD-h650",
        ]

        # Set variables.
        self.outdir = os.path.join(
            str(os.path.dirname(os.path.abspath(__file__))),
            "prepare_bryois_genotype_dump",
        )
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        self.bryois_ct_trans = {
            "Astrocytes": "Astrocytes",
            "Endothelial cells": "EndothelialCells",
            "Excitatory neurons": "ExcitatoryNeurons",
            "Inhibitory neurons": "InhibitoryNeurons",
            "Microglia": "Microglia",
            "OPCs / COPs": "Oligodendrocytes",
            "Oligodendrocytes": "OPCsCOPs",
            "Pericytes": "Pericytes",
        }

    def start(self):
        # print("Loading Bryois data.")
        # bryois_df = pd.read_excel(self.bryois_path)
        # bryois_df.columns = bryois_df.iloc[0, :]
        # bryois_df = bryois_df.iloc[1:, :]
        # bryois_df.reset_index(drop=True, inplace=True)
        # bryois_df.index.name = None
        # bryois_df.columns.name = None
        # print(bryois_df)
        #
        # print("Loading MetaBrain data")
        # metabrain_snp_df_list = []
        # for dataset in self.datasets:
        #     print("\t{}".format(dataset))
        #     inpath = os.path.join(self.snps_indir, dataset, "SNPs.txt.gz")
        #     df = pd.read_csv(inpath, sep="\t", header=None, index_col=None)
        #     metabrain_snp_df_list.append(df)
        #
        # metabrain_snp_df = pd.concat(metabrain_snp_df_list, axis=0)
        # metabrain_snp_df.columns = ["SNPName"]
        # print(metabrain_snp_df)
        #
        # metabrain_snp_df.drop_duplicates(inplace=True)
        # metabrain_snp_df["SNP"] = [x.split(":")[2] for x in metabrain_snp_df["SNPName"]]
        # print(metabrain_snp_df)
        #
        # print("Merge.")
        # bryois_df = bryois_df.merge(metabrain_snp_df, on="SNP", how="left")
        # print("Filter significnat.")
        # bryois_df = bryois_df.loc[bryois_df["adj_p"] <= 0.05, :]

        print("Save.")
        # bryois_df.to_csv(os.path.join(self.outdir, "bryois_cis_eqtl.txt.gz"), sep="\t", header=True, index=False, compression="gzip")
        bryois_df = pd.read_csv(
            os.path.join(self.outdir, "bryois_cis_eqtl.txt.gz"),
            sep="\t",
            header=0,
            index_col=None,
        )
        print(bryois_df)

        print("Save SNPs for genotype dump")
        snp_df = bryois_df[["SNPName"]].copy()
        snp_df.dropna(inplace=True)
        snp_df.drop_duplicates(inplace=True)
        snp_df.to_csv(
            os.path.join(self.outdir, "bryois_cis_eqtl_snps.txt"),
            sep="\t",
            header=False,
            index=False,
        )
        del snp_df


if __name__ == "__main__":
    m = main()
    m.start()
