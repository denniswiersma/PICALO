"""
File:         inter_optimizer.py
Created:      2021/03/25
Last Changed: 2022/12/15
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
import pandas as pd
import time
import os

# Third party imports.
import numpy as np

# Local application imports.
from src.force_normaliser import ForceNormaliser
from src.statistics import (
    calc_vertex_xpos,
    remove_covariates_elementwise,
    calc_pearsonr_vector,
)
from src.utilities import save_dataframe, get_ieqtls


class InteractionOptimizer:
    def __init__(
        self, covariates, dataset_m, samples, ieqtl_alpha, min_iter, max_iter, tol, log
    ):
        self.covariates = covariates
        self.samples = samples
        self.ieqtl_alpha = ieqtl_alpha
        self.min_iter = min_iter
        self.max_iter = max_iter
        self.tol = tol
        self.log = log
        self.fn = ForceNormaliser(dataset_m=dataset_m, samples=samples, log=log)

    def process(self, eqtl_m, geno_m, expr_m, covs_m, outdir):
        context_a = None
        n_hits = 0
        stop = True
        cov = None
        prev_included_ieqtls = (0, set())
        n_iterations_performed = 0
        info_m = np.empty((self.max_iter, 6), dtype=np.float64)
        n_hits_per_sample_m = np.empty(
            (self.max_iter, geno_m.shape[1]), dtype=np.float64
        )
        iterations_m = np.empty((self.max_iter + 1, geno_m.shape[1]), dtype=np.float64)
        for iteration in range(self.max_iter):
            self.log.info("\t\tIteration: {}".format(iteration))

            start_time = int(time.time())

            min_n_hits_per_sample = 0
            ieqtls = []
            n_hits_per_sample_a = np.zeros(geno_m.shape[1])
            results_df = None

            if iteration == 0 and np.shape(covs_m)[0] == 1:
                context_a = np.squeeze(covs_m)
                cov = self.covariates[0]

            # Find the significant ieQTLs.
            if context_a is None:
                self.log.info(
                    "\t\t  Finding the covariate that has the most "
                    "ieQTLs without optimization"
                )

                hits_per_cov_data = []

                # Find which covariate has the highest number of ieQTLs.
                for cov_index in range(covs_m.shape[0]):
                    # Extract the covariate we are working on.
                    cova_a = covs_m[cov_index, :]

                    # Clean the expression matrix.
                    iter_expr_m = remove_covariates_elementwise(
                        y_m=expr_m, X_m=geno_m, a=cova_a
                    )

                    # Force normalise the expression matrix and the interaction
                    # vector.
                    iter_expr_m = self.fn.process(data=iter_expr_m)
                    fn_cova_a = self.fn.process(data=cova_a)

                    # Find the significant ieQTLs.
                    (
                        cov_hits,
                        cov_hits_per_sample_a,
                        cov_ieqtls,
                        cov_results_df,
                    ) = get_ieqtls(
                        eqtl_m=eqtl_m,
                        geno_m=geno_m,
                        expr_m=iter_expr_m,
                        context_a=fn_cova_a,
                        cov=self.covariates[cov_index],
                        alpha=self.ieqtl_alpha,
                    )
                    cov_min_hits_per_sample = np.min(cov_hits_per_sample_a)

                    # Save hits.
                    self.log.info(
                        "\t\t\tCovariate: '{}' has {:,} significant ieQTLs [min {:,} per sample]".format(
                            self.covariates[cov_index],
                            cov_hits,
                            cov_min_hits_per_sample,
                        )
                    )
                    hits_per_cov_data.append([self.covariates[cov_index], cov_hits])

                    if (cov_min_hits_per_sample >= 2) and (
                        (cov_hits > n_hits)
                        or (
                            cov_hits == n_hits
                            and cov_min_hits_per_sample > min_n_hits_per_sample
                        )
                    ):
                        cov = self.covariates[cov_index]
                        context_a = np.copy(cova_a)
                        n_hits = cov_hits
                        min_n_hits_per_sample = cov_min_hits_per_sample
                        n_hits_per_sample_a = cov_hits_per_sample_a
                        ieqtls = cov_ieqtls
                        results_df = cov_results_df

                    del (
                        cova_a,
                        iter_expr_m,
                        fn_cova_a,
                        cov_hits,
                        cov_hits_per_sample_a,
                        cov_ieqtls,
                        cov_results_df,
                        cov_min_hits_per_sample,
                    )

                if cov is None:
                    self.log.warning("\t\t  No valid covariate found")
                    context_a = None
                    stop = False
                    break

                self.log.info(
                    "\t\t  Covariate '{}' will be used for this component.".format(cov)
                )

                hits_per_cov_df = pd.DataFrame(
                    hits_per_cov_data, columns=["Covariate", "N-ieQTLs"]
                )
                save_dataframe(
                    df=hits_per_cov_df,
                    outpath=os.path.join(outdir, "covariate_selection.txt.gz"),
                    header=True,
                    index=False,
                    log=self.log,
                )
                del hits_per_cov_df
            else:
                self.log.info("\t\t  Finding ieQTLs")

                # Clean the expression matrix.
                iter_expr_m = remove_covariates_elementwise(
                    y_m=expr_m, X_m=geno_m, a=context_a
                )

                # Force normalise the expression matrix and the interaction
                # vector.
                iter_expr_m = self.fn.process(data=iter_expr_m)
                fn_context_a = self.fn.process(data=context_a)

                n_hits, n_hits_per_sample_a, ieqtls, results_df = get_ieqtls(
                    eqtl_m=eqtl_m,
                    geno_m=geno_m,
                    expr_m=iter_expr_m,
                    context_a=fn_context_a,
                    cov=cov,
                    alpha=self.ieqtl_alpha,
                )
                min_n_hits_per_sample = np.min(n_hits_per_sample_a)

                self.log.info(
                    "\t\t\tCovariate: '{}' has {:,} significant ieQTLs [min {:,} per sample]".format(
                        cov, n_hits, min_n_hits_per_sample
                    )
                )

                del iter_expr_m, fn_context_a

            # Save results.
            save_dataframe(
                df=results_df,
                outpath=os.path.join(
                    outdir,
                    "results_iteration{}{}.txt.gz".format(
                        "0" * (len(str(self.max_iter)) - len(str(iteration)) - 1),
                        iteration,
                    ),
                ),
                header=True,
                index=False,
                log=self.log,
            )

            if n_hits <= 1:
                self.log.error("\t\t  None or not enough significant ieQTLs found")
                if iteration == 0:
                    context_a = None
                    stop = False
                break

            # Check if we have at least 2 ieQTLs per sample.
            if min_n_hits_per_sample <= 1:
                self.log.error(
                    "\t\t  Some samples have no or not enough ieQTLs for optimization"
                )
                if iteration == 0:
                    context_a = None
                    stop = False
                break

            self.log.info("\t\t  Optimizing ieQTLs")

            # Optimize the interaction vector.
            optimized_context_a = self.optimize_ieqtls(ieqtls)

            # Safe that interaction vector.
            if iteration == 0:
                iterations_m[iteration, :] = context_a
            iterations_m[iteration + 1, :] = optimized_context_a
            n_hits_per_sample_m[iteration, :] = n_hits_per_sample_a

            self.log.info(
                "\t\t  Calculating the total log likelihood before and after optimization"
            )
            pre_optimization_ll_a = self.calculate_log_likelihood(
                ieqtls=ieqtls, vector=context_a
            )
            post_optimization_ll_a = self.calculate_log_likelihood(
                ieqtls=ieqtls, vector=optimized_context_a
            )

            # Calculate the change in total log likelihood.
            sum_abs_norm_delta_ll = np.sum(
                np.abs(post_optimization_ll_a - pre_optimization_ll_a)
                / np.abs(pre_optimization_ll_a)
            )
            self.log.info(
                "\t\t\tSum absolute normalized \u0394 log likelihood: {:.2e}".format(
                    sum_abs_norm_delta_ll
                )
            )

            # Calculate the pearson correlation before and after optimalisation.
            pearsonr = calc_pearsonr_vector(x=context_a, y=optimized_context_a)
            self.log.info("\t\t\tPearson r: {:.6f}".format(pearsonr))

            # Compare the included ieQTLs with the previous iteration.
            included_ieqtl_ids = {ieqtl.get_ieqtl_id() for ieqtl in ieqtls}
            n_overlap = np.nan
            pct_overlap = np.nan
            if prev_included_ieqtls[1]:
                overlap = prev_included_ieqtls[1].intersection(included_ieqtl_ids)
                n_overlap = len(overlap)
                pct_overlap = (100 / prev_included_ieqtls[0]) * n_overlap
                self.log.info(
                    "\t\t\tOverlap in included ieQTL(s): {:,} [{:.2f}%]".format(
                        n_overlap, pct_overlap
                    )
                )

            # Store the stats.
            info_m[iteration, :] = np.array(
                [
                    n_hits,
                    min_n_hits_per_sample,
                    n_overlap,
                    pct_overlap,
                    sum_abs_norm_delta_ll,
                    pearsonr,
                ]
            )

            # Check if we are stuck in an oscillating loop. Start checking
            # this once we reached the minimum number of iterations + 1.
            if iteration >= 3 and iteration >= self.min_iter:
                # Check the correlation between this iteration and 2 iterations
                # back. Also check the correlation between the previous
                # iteration and 2 before that.
                pearsonr1 = calc_pearsonr_vector(
                    x=iterations_m[iteration - 1, :], y=iterations_m[iteration + 1, :]
                )

                pearsonr2 = calc_pearsonr_vector(
                    x=iterations_m[iteration - 2, :], y=iterations_m[iteration, :]
                )
                self.log.info(
                    "\t\t\titeration{} vs iteration{}:"
                    "\tr = {:.6f}".format(iteration, iteration - 2, pearsonr1)
                )
                self.log.info(
                    "\t\t\titeration{} vs iteration{}:"
                    "\tr = {:.6f}".format(iteration - 1, iteration - 3, pearsonr2)
                )

                # If one if these is highly correlated that means we are in an
                # oscillating loop.
                current_iter_passed_tol = (1 - pearsonr1) < self.tol
                previous_iter_passed_tol = (1 - pearsonr2) < self.tol
                if current_iter_passed_tol or previous_iter_passed_tol:
                    self.log.warning("")
                    self.log.warning("\t\tIterations are oscillating")

                    # Roll back to the previous iteration if that one converged
                    # but the current one did not. ALternatively, roll back
                    # if both converged but the previous iteration had more
                    # ieQTLs.
                    if (not current_iter_passed_tol and previous_iter_passed_tol) or (
                        current_iter_passed_tol
                        and previous_iter_passed_tol
                        and prev_included_ieqtls[0] > n_hits
                    ):
                        self.log.warning("\t\t  Rolling back to previous " "iteration.")
                        self.log.warning("")
                        context_a = iterations_m[iteration, :]
                        n_hits = prev_included_ieqtls[0]
                    else:
                        n_iterations_performed += 1

                    self.log.warning("\t\tModel converged")
                    self.log.info("")
                    stop = False
                    break

            # Print stats.
            rt_min, rt_sec = divmod(int(time.time()) - start_time, 60)
            self.log.debug(
                "\t\t  Finished in {} minute(s) and "
                "{} second(s)".format(int(rt_min), int(rt_sec))
            )
            self.log.info("")

            # Overwrite the variables for the next round. This has to be
            # before the break because we define context_a as the end result.
            context_a = optimized_context_a
            prev_included_ieqtls = (n_hits, included_ieqtl_ids)
            n_iterations_performed += 1

            # Check if we converged normally.
            if n_iterations_performed >= self.min_iter and (1 - pearsonr) < self.tol:
                self.log.warning("\t\tModel converged")
                self.log.info("")
                stop = False
                break

            del ieqtls, optimized_context_a, n_hits_per_sample_a

        # Save overview files.
        iteration_df = pd.DataFrame(
            iterations_m[: (n_iterations_performed + 1), :],
            index=["start"]
            + ["iteration{}".format(i) for i in range(n_iterations_performed)],
            columns=self.samples,
        )
        save_dataframe(
            df=iteration_df,
            outpath=os.path.join(outdir, "iteration.txt.gz"),
            header=True,
            index=True,
            log=self.log,
        )
        del iteration_df, iterations_m

        if n_iterations_performed > 0:
            n_hits_per_sample_df = pd.DataFrame(
                n_hits_per_sample_m[:n_iterations_performed, :],
                index=["iteration{}".format(i) for i in range(n_iterations_performed)],
                columns=self.samples,
            )
            save_dataframe(
                df=n_hits_per_sample_df,
                outpath=os.path.join(outdir, "n_hits_per_sample.txt.gz"),
                header=True,
                index=True,
                log=self.log,
            )

            info_df = pd.DataFrame(
                info_m[:n_iterations_performed, :],
                index=["iteration{}".format(i) for i in range(n_iterations_performed)],
                columns=[
                    "N",
                    "min N per sample",
                    "N Overlap",
                    "Overlap %",
                    "Sum Abs Normalized Delta Log Likelihood",
                    "Pearson r",
                ],
            )
            info_df.insert(0, "covariate", cov)
            save_dataframe(
                df=info_df,
                outpath=os.path.join(outdir, "info.txt.gz"),
                header=True,
                index=True,
                log=self.log,
            )

            del n_hits_per_sample_df, n_hits_per_sample_m, info_df, info_m

        return context_a, n_hits, stop

    @staticmethod
    def optimize_ieqtls(ieqtls):
        coef_a_collection = []
        coef_b_collection = []
        for i, ieqtl in enumerate(ieqtls):
            coef_a, coef_b = ieqtl.get_mll_coef_representation(full_array=True)
            coef_a_collection.append(coef_a)
            coef_b_collection.append(coef_b)

        coef_a_sum = np.sum(coef_a_collection, axis=0)
        coef_b_sum = np.sum(coef_b_collection, axis=0)
        optimized_a = calc_vertex_xpos(a=coef_a_sum, b=coef_b_sum)

        return optimized_a

    @staticmethod
    def calculate_log_likelihood(ieqtls, vector=None):
        log_likelihoods = np.empty(len(ieqtls), dtype=np.float64)
        for i, ieqtl in enumerate(ieqtls):
            log_likelihoods[i] = ieqtl.calc_log_likelihood(new_cov=vector)

        return log_likelihoods
