"""
File:         data.py
Created:      2020/11/16
Last Changed: 2021/11/19
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.

# Third party imports.
import pandas as pd
import numpy as np

# Local application imports.
from src.utilities import load_dataframe


class Data:
    def __init__(
        self,
        eqtl_path,
        genotype_path,
        expression_path,
        tech_covariate_path,
        tech_covariate_with_inter_path,
        covariate_path,
        sample_dataset_path,
        log,
    ):
        # Safe arguments.
        self.eqtl_path = eqtl_path
        self.geno_path = genotype_path
        self.expr_path = expression_path
        self.tcov_path = tech_covariate_path
        self.tcov_inter_path = tech_covariate_with_inter_path
        self.covs_path = covariate_path
        self.std_path = sample_dataset_path
        self.log = log

        # Set empty variables.
        self.eqtl_df = None
        self.geno_df = None
        self.expr_df = None
        self.tcov_df = None
        self.tcov_inter_df = None
        self.covs_df = None
        self.std_df = None

    def get_eqtl_df(self, skiprows=None, nrows=None):
        if self.eqtl_df is None:
            self.eqtl_df = load_dataframe(
                self.eqtl_path,
                header=0,
                index_col=None,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.eqtl_df

    def get_geno_df(self, skiprows=None, nrows=None):
        if self.geno_df is None:
            self.geno_df = load_dataframe(
                self.geno_path,
                header=0,
                index_col=0,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.geno_df

    def get_expr_df(self, skiprows=None, nrows=None):
        if self.expr_df is None:
            self.expr_df = load_dataframe(
                self.expr_path,
                header=0,
                index_col=0,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.expr_df

    def get_tcov_df(self, skiprows=None, nrows=None):
        if self.tcov_path is None:
            return None

        if self.tcov_df is None:
            self.tcov_df = load_dataframe(
                self.tcov_path,
                header=0,
                index_col=0,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.tcov_df

    def get_tcov_inter_df(self, skiprows=None, nrows=None):
        if self.tcov_inter_path is None:
            return None

        if self.tcov_inter_df is None:
            self.tcov_inter_df = load_dataframe(
                self.tcov_inter_path,
                header=0,
                index_col=0,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.tcov_inter_df

    def get_covs_df(self, skiprows=None, nrows=None):
        if self.covs_df is None:
            self.covs_df = load_dataframe(
                self.covs_path,
                header=0,
                index_col=0,
                skiprows=skiprows,
                nrows=nrows,
                log=self.log,
            )

        return self.covs_df

    def get_std_df(self):
        if self.std_df is None and self.std_path is not None:
            self.std_df = load_dataframe(
                self.std_path, header=0, index_col=None, log=self.log
            )

        return self.std_df

    @staticmethod
    def reverse_merge_dict(dict):
        out_dict = {}
        seen_keys = set()
        for key, value in dict.items():
            if key in seen_keys:
                print("Key {} has multiple values.".format(key))
            seen_keys.add(key)

            if value in out_dict.keys():
                keys = out_dict[value]
                keys.append(key)
                out_dict[value] = keys
            else:
                out_dict[value] = [key]

        return out_dict

    def print_arguments(self):
        self.log.info("Data Arguments:")
        self.log.info("  > eQTL input path: {}".format(self.eqtl_path))
        self.log.info("  > Genotype input path: {}".format(self.geno_path))
        self.log.info("  > Expression input path: {}".format(self.expr_path))
        self.log.info("  > Technical covariates input path: {}".format(self.tcov_path))
        self.log.info(
            "  > Technical covariates with interaction input path: {}".format(
                self.tcov_inter_path
            )
        )
        self.log.info("  > Covariates input path: {}".format(self.covs_path))
        self.log.info("  > Sample-dataset path: {}".format(self.std_path))
        self.log.info("")
