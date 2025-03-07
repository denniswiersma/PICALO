"""
File:         main.py
Created:      2020/11/16
Last Changed: 2023/08/21
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
from src.logger import Logger
from src.force_normaliser import ForceNormaliser
from src.objects.data import Data
from src.inter_optimizer import InteractionOptimizer
from src.statistics import remove_covariates, remove_covariates_elementwise
from src.utilities import load_dataframe, save_dataframe, get_ieqtls


class Main:
    def __init__(
        self,
        current_dir,
        eqtl_path,
        genotype_path,
        genotype_na,
        expression_path,
        tech_covariate_path,
        tech_covariate_with_inter_path,
        covariate_path,
        sample_dataset_path,
        min_dataset_size,
        ieqtl_alpha,
        call_rate,
        hw_pval,
        maf,
        mgs,
        n_components,
        min_iter,
        max_iter,
        tol,
        force_continue,
        outdir,
        verbose,
    ):
        # Safe arguments.
        self.genotype_na = genotype_na
        self.min_dataset_sample_size = min_dataset_size
        self.call_rate = call_rate
        self.hw_pval = hw_pval
        self.maf = maf
        self.mgs = mgs
        self.ieqtl_alpha = ieqtl_alpha
        self.n_components = n_components
        self.min_iter = min_iter
        self.max_iter = max_iter
        self.tol = tol
        self.force_continue = force_continue

        # Prepare an output directory.
        self.outdir = os.path.join(current_dir, "output", outdir)
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        # Initialize logger.
        logger = Logger(outdir=self.outdir, verbose=verbose, clear_log=True)
        logger.print_arguments()
        self.log = logger.get_logger()

        # Initialize data object.
        self.data = Data(
            eqtl_path=eqtl_path,
            genotype_path=genotype_path,
            expression_path=expression_path,
            tech_covariate_path=tech_covariate_path,
            tech_covariate_with_inter_path=tech_covariate_with_inter_path,
            covariate_path=covariate_path,
            sample_dataset_path=sample_dataset_path,
            log=self.log,
        )
        self.data.print_arguments()

    def start(self):
        self.log.info("Starting program")
        self.print_arguments()

        ########################################################################

        self.log.info("Loading eQTL data, genotype data, and dataset info")
        eqtl_df = self.data.get_eqtl_df()
        geno_df = self.data.get_geno_df()
        std_df = self.data.get_std_df()

        if std_df is not None:
            # Validate that the input data matches.
            self.validate_data(std_df=std_df, geno_df=geno_df)
        else:
            # Create sample-to-dataset file with all the samples having the
            # same dataset.
            std_df = pd.DataFrame({"sample": geno_df.columns, "dataset": "None"})

        self.log.info("\tChecking dataset sample sizes")
        # Check if each dataset has the minimal number of samples.
        dataset_sample_counts = list(
            zip(*np.unique(std_df.iloc[:, 1], return_counts=True))
        )
        dataset_sample_counts.sort(key=lambda x: -x[1])
        max_dataset_length = np.max(
            [len(str(dataset[0])) for dataset in dataset_sample_counts]
        )
        for dataset, sample_size in dataset_sample_counts:
            self.log.info(
                "\t  {:{}s}  {:,} samples".format(
                    dataset, max_dataset_length, sample_size
                )
            )
        if dataset_sample_counts[-1][1] < self.min_dataset_sample_size:
            self.log.warning(
                "\t\tOne or more datasets have a smaller sample "
                "size than recommended. Consider excluded these"
            )
        self.log.info("")

        # Construct dataset df.
        dataset_df = self.construct_dataset_df(std_df=std_df)
        datasets = dataset_df.columns.tolist()

        self.log.info("\tCalculating genotype call rate per dataset")
        geno_df, call_rate_df = self.calculate_call_rate(
            geno_df=geno_df, dataset_df=dataset_df
        )
        call_rate_n_skipped = (call_rate_df.min(axis=1) < self.call_rate).sum()
        if call_rate_n_skipped > 0:
            self.log.warning(
                "\t  {:,} eQTLs have had dataset(s) filled with "
                "NaN values due to call rate "
                "threshold ".format(call_rate_n_skipped)
            )

        save_dataframe(
            df=call_rate_df,
            outpath=os.path.join(self.outdir, "call_rate.txt.gz"),
            header=True,
            index=True,
            log=self.log,
        )
        self.log.info("")

        self.log.info("\tCalculating genotype stats for inclusing criteria")
        cr_keep_mask = ~(geno_df == self.genotype_na).all(axis=1).to_numpy(dtype=bool)
        geno_stats_df = pd.DataFrame(
            np.nan,
            index=geno_df.index,
            columns=[
                "N",
                "NaN",
                "0",
                "1",
                "2",
                "min GS",
                "HW pval",
                "allele1",
                "allele2",
                "MA",
                "MAF",
            ],
        )
        geno_stats_df["N"] = 0
        geno_stats_df["NaN"] = geno_df.shape[1]
        geno_stats_df.loc[cr_keep_mask, :] = self.calculate_genotype_stats(
            df=geno_df.loc[cr_keep_mask, :]
        )

        # Checking which eQTLs pass the requirements
        n_keep_mask = (geno_stats_df.loc[:, "N"] >= 6).to_numpy(dtype=bool)
        mgs_keep_mask = (geno_stats_df.loc[:, "min GS"] >= self.mgs).to_numpy(
            dtype=bool
        )
        hwpval_keep_mask = (geno_stats_df.loc[:, "HW pval"] >= self.hw_pval).to_numpy(
            dtype=bool
        )
        maf_keep_mask = (geno_stats_df.loc[:, "MAF"] > self.maf).to_numpy(dtype=bool)
        combined_keep_mask = (
            cr_keep_mask
            & n_keep_mask
            & mgs_keep_mask
            & hwpval_keep_mask
            & maf_keep_mask
        )
        geno_n_skipped = np.size(combined_keep_mask) - np.sum(combined_keep_mask)
        if geno_n_skipped > 0:
            self.log.warning(
                "\t  {:,} eQTL(s) failed the call rate threshold".format(
                    np.size(cr_keep_mask) - np.sum(cr_keep_mask)
                )
            )
            self.log.warning(
                "\t  {:,} eQTL(s) failed the sample size threshold".format(
                    np.size(n_keep_mask) - np.sum(n_keep_mask)
                )
            )
            self.log.warning(
                "\t  {:,} eQTL(s) failed the min. genotype group size threshold".format(
                    np.size(mgs_keep_mask) - np.sum(mgs_keep_mask)
                )
            )
            self.log.warning(
                "\t  {:,} eQTL(s) failed the Hardy-Weinberg p-value threshold".format(
                    np.size(hwpval_keep_mask) - np.sum(hwpval_keep_mask)
                )
            )
            self.log.warning(
                "\t  {:,} eQTL(s) failed the MAF threshold".format(
                    np.size(maf_keep_mask) - np.sum(maf_keep_mask)
                )
            )
            self.log.warning("\t  ----------------------------------------")
            self.log.warning(
                "\t  {:,} eQTL(s) are discarded in total".format(geno_n_skipped)
            )

        # Select rows that meet requirements.
        eqtl_df = eqtl_df.loc[combined_keep_mask, :]
        geno_df = geno_df.loc[combined_keep_mask, :]

        # Add mask to genotype stats data frame.
        geno_stats_df["mask"] = 0
        geno_stats_df.loc[combined_keep_mask, "mask"] = 1

        save_dataframe(
            df=geno_stats_df,
            outpath=os.path.join(self.outdir, "genotype_stats.txt.gz"),
            header=True,
            index=True,
            log=self.log,
        )
        self.log.info("")

        del (
            call_rate_df,
            geno_stats_df,
            n_keep_mask,
            mgs_keep_mask,
            hwpval_keep_mask,
            maf_keep_mask,
        )

        ########################################################################

        self.log.info("Loading other data")
        self.log.info("\tIncluded {:,} eQTLs".format(np.sum(combined_keep_mask)))
        skiprows = None
        if geno_n_skipped > 0:
            skiprows = [
                i + 1
                for i in range(0, max(eqtl_df.index) + 1)
                if i not in eqtl_df.index
            ]
        expr_df = self.data.get_expr_df(skiprows=skiprows, nrows=max(eqtl_df.index) + 1)
        covs_df = self.data.get_covs_df()

        # Check for nan values.
        if geno_df.isna().values.sum() > 0:
            self.log.error("\t  Genotype file contains NaN values")
            exit()
        if expr_df.isna().values.sum() > 0:
            self.log.error("\t  Expression file contains NaN values")
            exit()
        if covs_df.isna().values.sum() > 0:
            self.log.error("\t  Covariate file contains NaN values")
            exit()

        # Transpose if need be.
        if covs_df.shape[0] == geno_df.shape[1]:
            self.log.warning("\t  Transposing covariate matrix")
            covs_df = covs_df.T

        covariates = covs_df.index.tolist()
        self.log.info("\t  Covariates: {}".format(", ".join(covariates)))

        # Validate that the input data (still) matches.
        self.validate_data(
            std_df=std_df,
            eqtl_df=eqtl_df,
            geno_df=geno_df,
            expr_df=expr_df,
            covs_df=covs_df,
        )
        samples = std_df.iloc[:, 0].to_numpy(object)
        self.log.info("")

        ########################################################################

        self.log.info("Transform to numpy matrices for speed")
        eqtl_m = eqtl_df[["SNPName", "ProbeName"]].to_numpy(object)
        geno_m = geno_df.to_numpy(np.float64)
        expr_m = expr_df.to_numpy(np.float64)
        dataset_m = dataset_df.to_numpy(np.uint8)
        covs_m = covs_df.to_numpy(np.float64)
        self.log.info("")
        del eqtl_df, geno_df, expr_df, dataset_df, covs_df

        # Fill the missing values with NaN.
        expr_m[geno_m == self.genotype_na] = np.nan
        geno_m[geno_m == self.genotype_na] = np.nan

        ########################################################################

        self.log.info("Loading technical covariates")
        tcov_df = self.data.get_tcov_df()
        tcov_inter_df = self.data.get_tcov_inter_df()

        tcov_m, tcov_labels = self.load_tech_cov(
            df=tcov_df, name="tech. cov. without interaction", std_df=std_df
        )
        tcov_inter_m, tcov_inter_labels = self.load_tech_cov(
            df=tcov_inter_df, name="tech. cov. with interaction", std_df=std_df
        )

        corr_m, corr_inter_m, correction_m_labels = self.construct_correct_matrices(
            dataset_m=dataset_m,
            dataset_labels=datasets,
            tcov_m=tcov_m,
            tcov_labels=tcov_labels,
            tcov_inter_m=tcov_inter_m,
            tcov_inter_labels=tcov_inter_labels,
        )

        self.log.info(
            "\tCorrection matrix includes the following columns "
            "[N={}]: {}".format(
                len(correction_m_labels), ", ".join(correction_m_labels)
            )
        )
        self.log.info("")
        del tcov_m, tcov_labels, tcov_inter_m, tcov_inter_labels, correction_m_labels

        ########################################################################

        self.log.info("Starting PIC identification")

        io = InteractionOptimizer(
            covariates=covariates,
            dataset_m=dataset_m,
            samples=samples,
            ieqtl_alpha=self.ieqtl_alpha,
            min_iter=self.min_iter,
            max_iter=self.max_iter,
            tol=self.tol,
            log=self.log,
        )

        pic_m = np.empty((self.n_components, np.size(samples)), dtype=np.float64)
        summary_stats_m = np.empty((self.n_components, 2), dtype=np.float64)
        summary_stats_m[:] = np.nan
        n_components_performed = 0
        pic_a = None
        stop = False
        pic_corr_m = np.copy(corr_m) if corr_m is not None else None
        pic_corr_inter_m = np.copy(corr_inter_m) if corr_inter_m is not None else None
        components_df = None
        for comp_count in range(self.n_components):
            if stop:
                self.log.warning("Last component did not converge")
                if not self.force_continue:
                    self.log.warning("Stop further identification of " "components")
                    break

            self.log.info("\tIdentifying PIC {}".format(comp_count + 1))

            # Prepare component output directory.
            comp_outdir = os.path.join(self.outdir, "PIC{}".format(comp_count + 1))
            if not os.path.exists(comp_outdir):
                os.makedirs(comp_outdir)

            # Add component to the base matrix.
            if pic_a is not None:
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

            component_path = os.path.join(comp_outdir, "component.npy")
            if os.path.exists(component_path):
                self.log.info("\t  PIC has already been identified")

                # Loading previous run PIC.
                with open(component_path, "rb") as f:
                    pic_a = np.load(f)
                f.close()
                self.log.info(
                    "\t  Loaded dataframe: {} with shape: {}".format(
                        os.path.basename(component_path), pic_a.shape
                    )
                )
                pic_m[comp_count, :] = pic_a

                # Loading #ieQTLs this PIC had.
                info_df_path = os.path.join(comp_outdir, "info.txt.gz")
                if os.path.exists(info_df_path):
                    info_df = load_dataframe(
                        info_df_path, header=0, index_col=0, log=self.log
                    )
                    summary_stats_m[comp_count, 0] = info_df.loc[info_df.index[-1], "N"]
            else:
                # Remove tech. covs. + components from expression matrix.
                self.log.info("\t  Correcting expression matrix")
                comp_expr_m = remove_covariates(
                    y_m=expr_m,
                    X_m=pic_corr_m,
                    X_inter_m=pic_corr_inter_m,
                    inter_m=geno_m,
                    log=self.log,
                )

                # Optimize the cell fractions in X iterations.
                self.log.info("\t  Optimizing interaction component")
                pic_a, n_ieqtls, stop = io.process(
                    eqtl_m=eqtl_m,
                    geno_m=geno_m,
                    expr_m=comp_expr_m,
                    covs_m=covs_m,
                    outdir=comp_outdir,
                )

                # Save #ieQTLs to summary stats.
                summary_stats_m[comp_count, 0] = n_ieqtls

                # Stop if the returned component is None.
                if pic_a is None:
                    break

                # Save.
                pic_m[comp_count, :] = pic_a
                with open(component_path, "wb") as f:
                    np.save(f, pic_a)
                f.close()

            # Increment counter.
            n_components_performed += 1

            # Saving component output file.
            if n_components_performed > 0:
                components_df = pd.DataFrame(
                    pic_m[:n_components_performed, :],
                    index=[
                        "PIC{}".format(i + 1) for i in range(n_components_performed)
                    ],
                    columns=samples,
                )

                save_dataframe(
                    df=components_df,
                    outpath=os.path.join(self.outdir, "components.txt.gz"),
                    header=True,
                    index=True,
                    log=self.log,
                )

            self.log.info("")

        if n_components_performed == 0:
            self.log.error("No PICs identified. Stopping PICALO.")

            # Save summary stats.
            save_dataframe(
                df=pd.DataFrame(
                    summary_stats_m,
                    index=["PIC{}".format(i + 1) for i in range(self.n_components)],
                    columns=["Iterative #ieQTLs", "Raw #ieQTLs"],
                ),
                outpath=os.path.join(self.outdir, "SummaryStats.txt.gz"),
                header=True,
                index=True,
                log=self.log,
            )
            exit()

        pics_df = components_df
        if stop and not self.force_continue:
            pics_df = components_df.iloc[:-1, :]
        save_dataframe(
            df=pics_df,
            outpath=os.path.join(self.outdir, "PICs.txt.gz"),
            header=True,
            index=True,
            log=self.log,
        )
        del components_df

        ########################################################################

        if pics_df.shape[0] > 0:
            self.log.info(
                "Map interactions with PICs without correcting " "previous PICs."
            )
            self.log.info("\t  Correcting expression matrix")

            # Prepare output directory.
            pic_ieqtl_outdir = os.path.join(self.outdir, "PIC_interactions")
            if not os.path.exists(pic_ieqtl_outdir):
                os.makedirs(pic_ieqtl_outdir)

            # Correct the gene expression matrix.
            corrected_expr_m = remove_covariates(
                y_m=expr_m,
                X_m=corr_m,
                X_inter_m=corr_inter_m,
                inter_m=geno_m,
                log=self.log,
            )

            fn = ForceNormaliser(dataset_m=dataset_m, samples=samples, log=self.log)

            self.log.info("\t  Mapping ieQTLs")
            for pic_index, pic in enumerate(pics_df.index):
                # Extract the PIC we are working on.
                pic_a = pics_df.iloc[pic_index, :].to_numpy()

                # Clean the expression matrix.
                pic_expr_m = remove_covariates_elementwise(
                    y_m=corrected_expr_m, X_m=geno_m, a=pic_a
                )

                # Force normalise the expression matrix.
                pic_expr_m = fn.process(data=pic_expr_m)
                fn_pic_a = fn.process(data=pic_a)

                # Find the significant ieQTLs.
                n_hits, _, _, results_df = get_ieqtls(
                    eqtl_m=eqtl_m,
                    geno_m=geno_m,
                    expr_m=pic_expr_m,
                    context_a=fn_pic_a,
                    cov=pics_df.index[pic_index],
                    alpha=self.ieqtl_alpha,
                )
                self.log.info("\t\t{} has {:,} significant ieQTLs".format(pic, n_hits))

                # Save results.
                save_dataframe(
                    df=results_df,
                    outpath=os.path.join(pic_ieqtl_outdir, "{}.txt.gz".format(pic)),
                    header=True,
                    index=False,
                    log=self.log,
                )
                summary_stats_m[pic_index, 1] = n_hits

                del pic_expr_m, pic_a, results_df

            del corrected_expr_m

        ########################################################################

        # Save summary stats.
        save_dataframe(
            df=pd.DataFrame(
                summary_stats_m,
                index=["PIC{}".format(i + 1) for i in range(self.n_components)],
                columns=["Iterative #ieQTLs", "Raw #ieQTLs"],
            ),
            outpath=os.path.join(self.outdir, "SummaryStats.txt.gz"),
            header=True,
            index=True,
            log=self.log,
        )

        self.log.info("Finished")
        self.log.info("")

    def validate_data(
        self,
        std_df,
        eqtl_df=None,
        geno_df=None,
        expr_df=None,
        covs_df=None,
        tcovs_df=None,
    ):
        # Check the samples.
        samples = std_df.iloc[:, 0].values.tolist()
        if geno_df is not None and geno_df.columns.tolist() != samples:
            self.log.error(
                "\tThe genotype file header does not match "
                "the sample-to-dataset link file"
            )
            exit()

        if expr_df is not None and expr_df.columns.tolist() != samples:
            self.log.error(
                "\tThe expression file header does not match "
                "the sample-to-dataset link file"
            )
            exit()

        if covs_df is not None and covs_df.columns.tolist() != samples:
            self.log.error(
                "\tThe covariates file header does not match "
                "the sample-to-dataset link file"
            )
            exit()

        if tcovs_df is not None and tcovs_df.index.tolist() != samples:
            self.log.error(
                "\tThe technical covariates file indices does "
                "not match the sample-to-dataset link file"
            )
            exit()

        # Check the eQTLs.
        if eqtl_df is not None:
            snp_reference = eqtl_df["SNPName"].values.tolist()
            probe_reference = eqtl_df["ProbeName"].values.tolist()

            if geno_df is not None and geno_df.index.tolist() != snp_reference:
                self.log.error(
                    "The genotype file indices do not match the " "eQTL file"
                )
                exit()

            if expr_df is not None and expr_df.index.tolist() != probe_reference:
                self.log.error(
                    "The expression file indices do not match the " "eQTL file"
                )
                exit()

    def calculate_call_rate(self, geno_df, dataset_df):
        # Calculate the fraction of NaNs per dataset.
        call_rate_df = pd.DataFrame(
            np.nan,
            index=geno_df.index,
            columns=["{} CR".format(dataset) for dataset in dataset_df.columns],
        )
        for dataset, sample_mask in dataset_df.T.iterrows():
            call_rate_s = (
                geno_df.loc[:, sample_mask.to_numpy(dtype=bool)] != self.genotype_na
            ).astype(int).sum(axis=1) / np.sum(sample_mask)
            call_rate_df.loc[:, "{} CR".format(dataset)] = call_rate_s

            # If the call rate is too high, replace all genotypes of that
            # dataset with missing.
            row_mask = call_rate_s < self.call_rate
            geno_df.loc[row_mask, sample_mask.astype(bool)] = self.genotype_na

        return geno_df, call_rate_df

    def calculate_genotype_stats(self, df):
        rounded_m = df.to_numpy(dtype=np.float64)
        rounded_m = np.rint(rounded_m)

        # Calculate the total samples that are not NaN.
        nan = np.sum(rounded_m == self.genotype_na, axis=1)
        n = rounded_m.shape[1] - nan

        # Count the genotypes.
        zero_a = np.sum(rounded_m == 0, axis=1)
        one_a = np.sum(rounded_m == 1, axis=1)
        two_a = np.sum(rounded_m == 2, axis=1)

        # Calculate the smallest genotype group size.
        sgz = np.minimum.reduce([zero_a, one_a, two_a])

        # Calculate the Hardy-Weinberg p-value.
        hwe_pvalues_a = self.calc_hwe_pvalue(
            obs_hets=one_a, obs_hom1=zero_a, obs_hom2=two_a
        )

        # Count the alleles.
        allele1_a = (zero_a * 2) + one_a
        allele2_a = (two_a * 2) + one_a

        # Calculate the MAF.
        maf = np.minimum(allele1_a, allele2_a) / (allele1_a + allele2_a)

        # Determine which allele is the minor allele.
        allele_m = np.column_stack((allele1_a, allele2_a))
        ma = np.argmin(allele_m, axis=1) * 2

        # Construct output data frame.
        output_df = pd.DataFrame(
            {
                "N": n,
                "NaN": nan,
                "0": zero_a,
                "1": one_a,
                "2": two_a,
                "min GS": sgz,
                "HW pval": hwe_pvalues_a,
                "allele1": allele1_a,
                "allele2": allele2_a,
                "MA": ma,
                "MAF": maf,
            },
            index=df.index,
        )
        del rounded_m, allele_m

        return output_df

    @staticmethod
    def calc_hwe_pvalue(obs_hets, obs_hom1, obs_hom2):
        """
        exact SNP test of Hardy-Weinberg Equilibrium as described in Wigginton,
        JE, Cutler, DJ, and Abecasis, GR (2005) A Note on Exact Tests of
        Hardy-Weinberg Equilibrium. AJHG 76: 887-893

        Adapted by M.Vochteloo to work on matrices.
        """
        if (
            not "int" in str(obs_hets.dtype)
            or not "int" in str(obs_hets.dtype)
            or not "int" in str(obs_hets.dtype)
        ):
            obs_hets = np.rint(obs_hets)
            obs_hom1 = np.rint(obs_hom1)
            obs_hom2 = np.rint(obs_hom2)

        # Force homc to be the max and homr to be the min observed genotype.
        obs_homc = np.maximum(obs_hom1, obs_hom2)
        obs_homr = np.minimum(obs_hom1, obs_hom2)

        # Calculate some other stats we need.
        rare_copies = 2 * obs_homr + obs_hets
        l_genotypes = obs_hets + obs_homc + obs_homr
        n = np.size(obs_hets)

        # Get the distribution midpoint.
        mid = np.rint(
            rare_copies * (2 * l_genotypes - rare_copies) / (2 * l_genotypes)
        ).astype(np.int)
        mid[mid % 2 != rare_copies % 2] += 1

        # Calculate the start points for the evaluation.
        curr_homr = (rare_copies - mid) / 2
        curr_homc = l_genotypes - mid - curr_homr

        # Calculate the left side.
        left_steps = np.floor(mid / 2).astype(int)
        max_left_steps = np.max(left_steps)
        left_het_probs = np.zeros((n, max_left_steps + 1), dtype=np.float64)
        left_het_probs[:, 0] = 1
        for i in np.arange(0, max_left_steps, 1, dtype=np.float64):
            prob = (
                left_het_probs[:, int(i)]
                * (mid - (i * 2))
                * ((mid - (i * 2)) - 1.0)
                / (4.0 * (curr_homr + i + 1.0) * (curr_homc + i + 1.0))
            )
            prob[mid - (i * 2) <= 0] = 0
            left_het_probs[:, int(i) + 1] = prob

        # Calculate the right side.
        right_steps = np.floor((rare_copies - mid) / 2).astype(int)
        max_right_steps = np.max(right_steps)
        right_het_probs = np.zeros((n, max_right_steps + 1), dtype=np.float64)
        right_het_probs[:, 0] = 1
        for i in np.arange(0, max_right_steps, 1, dtype=np.float64):
            prob = (
                right_het_probs[:, int(i)]
                * 4.0
                * (curr_homr - i)
                * (curr_homc - i)
                / (((i * 2) + mid + 2.0) * ((i * 2) + mid + 1.0))
            )
            prob[(i * 2) + mid >= rare_copies] = 0
            right_het_probs[:, int(i) + 1] = prob

        # Combine the sides.
        het_probs = np.hstack((np.flip(left_het_probs, axis=1), right_het_probs[:, 1:]))

        # Normalize.
        sum = np.sum(het_probs, axis=1)
        het_probs = het_probs / sum[:, np.newaxis]

        # Replace values higher then probability of obs_hets with 0.
        threshold_col_a = (max_left_steps - left_steps) + np.floor(obs_hets / 2).astype(
            int
        )
        threshold = np.array(
            [
                het_probs[i, threshold_col]
                for i, threshold_col in enumerate(threshold_col_a)
            ]
        )
        het_probs[het_probs > threshold[:, np.newaxis]] = 0

        # Calculate the p-values.
        p_hwe = np.sum(het_probs, axis=1)
        p_hwe[p_hwe > 1] = 1

        return p_hwe

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

    def load_tech_cov(self, df, name, std_df):
        if df is None:
            return None, []

        n_samples = std_df.shape[0]

        self.log.info(
            "\tWorking on technical covariates matrix matrix '{}'".format(name)
        )

        # Check for nan values.
        if df.isna().values.sum() > 0:
            self.log.error("\t  Matrix contains nan values")
            exit()

        # Put the samples on the rows.
        if df.shape[1] == n_samples:
            self.log.warning("\t  Transposing matrix")
            df = df.T

        # Check if valid.
        self.validate_data(std_df=std_df, tcovs_df=df)

        # Check for variables with zero std.
        variance_mask = df.std(axis=0) != 0
        n_zero_variance = variance_mask.shape[0] - variance_mask.sum()
        if n_zero_variance > 0:
            self.log.warning(
                "\t  Dropping {} rows with 0 variance".format(n_zero_variance)
            )
            df = df.loc[:, variance_mask]

        # Convert to numpy.
        m = df.to_numpy(np.float64)
        columns = df.columns.tolist()
        del df

        covariates = columns
        self.log.info(
            "\t  Technical covariates [{}]: {}".format(
                len(covariates), ", ".join(covariates)
            )
        )

        return m, covariates

    @staticmethod
    def construct_correct_matrices(
        dataset_m, dataset_labels, tcov_m, tcov_labels, tcov_inter_m, tcov_inter_labels
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

    def print_arguments(self):
        self.log.info("Arguments:")
        self.log.info("  > Genotype NA value: {}".format(self.genotype_na))
        self.log.info(
            "  > Minimal dataset size: >={}".format(self.min_dataset_sample_size)
        )
        self.log.info("  > SNP call rate: >{}".format(self.call_rate))
        self.log.info("  > Hardy-Weinberg p-value: >={}".format(self.hw_pval))
        self.log.info("  > MAF: >{}".format(self.maf))
        self.log.info("  > Minimal group size: >={}".format(self.mgs))
        self.log.info("  > ieQTL alpha: <={}".format(self.ieqtl_alpha))
        self.log.info("  > N components: {}".format(self.n_components))
        self.log.info("  > Minimal iterations: {}".format(self.min_iter))
        self.log.info("  > Maximum iterations: {}".format(self.max_iter))
        self.log.info("  > Tolerance: {}".format(self.tol))
        self.log.info("  > Force continue: {}".format(self.force_continue))
        self.log.info("  > Output directory: {}".format(self.outdir))
        self.log.info("")
