"""
File:         visualiser.py
Created:      2021/04/14
Last Changed: 2021/12/03
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
import os

# Third party imports.
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Local application imports.
from src.statistics import (
    calc_vertex_xpos,
    calc_pearsonr_vector,
    fit_and_predict,
    calc_rss,
    inverse,
    fit,
    predict,
    calc_std,
    calc_p_value,
)


class Visualiser:
    def __init__(self):
        self.palette = {0.0: "#E69F00", 1.0: "#0072B2", 2.0: "#D55E00"}

    def plot_overview(self, ieqtl, out_path, label):
        # Initialize the output directory.
        outdir = os.path.join(out_path, "plot")
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if not ieqtl.is_computed:
            ieqtl.compute()

        # Get the data we need.
        X = np.copy(ieqtl.X)
        y = np.copy(ieqtl.y)
        n = ieqtl.n

        # Calculate the eqtl stats.
        rss_model1 = calc_rss(y=y, y_hat=np.mean(y))
        eqtl_inv_m = inverse(X=X[:, :2])
        eqtl_betas = fit(X=X[:, :2], y=y, inv_m=eqtl_inv_m)
        y_hat = predict(X=X[:, :2], betas=eqtl_betas)
        eqtl_pearsonr = calc_pearsonr_vector(x=y, y=y_hat)
        rss_model2 = calc_rss(y=y, y_hat=y_hat)
        eqtl_std = calc_std(rss=rss_model2, n=n, df=2, inv_m=eqtl_inv_m)
        eqtl_p_value = calc_p_value(rss1=rss_model1, rss2=rss_model2, df1=1, df2=2, n=n)

        # Construct plot data frames.
        df = pd.DataFrame(
            X, columns=["intercept", "genotype", "covariate", "interaction"]
        )
        df["expression"] = y
        df["group"] = df["genotype"].round(0)

        annot1 = [
            "N = {:,}".format(ieqtl.n),
            "r = {:.2f}".format(eqtl_pearsonr),
            "Betas = {}".format(", ".join(["{:.2f}".format(x) for x in eqtl_betas])),
            "SD = {}".format(", ".join(["{:.2f}".format(x) for x in eqtl_std])),
            "t-values = {}".format(
                ", ".join(["{:.2f}".format(x) for x in eqtl_betas / eqtl_std])
            ),
            "p-value = {:.2e}".format(eqtl_p_value),
        ]
        annot2 = [
            "N = {:,}".format(ieqtl.n),
            "Betas = {}".format(", ".join(["{:.2f}".format(x) for x in ieqtl.betas])),
            "SD = {}".format(", ".join(["{:.2f}".format(x) for x in ieqtl.std])),
            "t-values = {}".format(
                ", ".join(["{:.2f}".format(x) for x in ieqtl.betas / ieqtl.std])
            ),
            "p-value = {:.2e}".format(ieqtl.p_value),
        ]

        # Plot.
        self.create_overview_figure(
            df=df,
            annot1=annot1,
            annot2=annot2,
            snp=ieqtl.get_snp(),
            gene=ieqtl.get_gene(),
            cov=ieqtl.get_cov(),
            title="{}:{}".format(ieqtl.get_ieqtl_id(), label),
            outdir=outdir,
        )

    def create_overview_figure(self, df, annot1, annot2, snp, gene, cov, title, outdir):
        sns.set_style("ticks")
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(24, 9))

        self.eqtl_plot(
            fig=fig,
            ax=ax1,
            df=df,
            x="group",
            y="expression",
            palette=self.palette,
            xlabel=snp,
            ylabel=gene,
            annot=annot1,
            title="eQTL",
        )

        self.inter_plot(
            fig=fig,
            ax=ax2,
            df=df,
            x="covariate",
            y="expression",
            group="group",
            palette=self.palette,
            xlabel=cov,
            ylabel="",
            annot=annot2,
            title="interaction",
        )

        plt.suptitle(title, fontsize=18)

        fig.savefig(
            os.path.join(outdir, "{}_overview_plot.png".format(title.replace(":", "-")))
        )
        plt.close()

    def plot_interaction_optimization(self, ieqtl, out_path, label, ocf=None):
        # Initialize the output directory.
        outdir = os.path.join(out_path, "plot")
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # Get the data we need.
        X_start = np.copy(ieqtl.X)
        y = np.copy(ieqtl.y)

        # Calculate the pearson R.
        pearsonr_start = calc_pearsonr_vector(x=y, y=fit_and_predict(X=X_start, y=y))
        r_squared_start = pearsonr_start * pearsonr_start

        # Calc the OCF if not given.
        if ocf is None:
            solo_optimized = True
            coef_a, coef_b = ieqtl.get_mll_coef_representation()
            ocf = calc_vertex_xpos(a=coef_a, b=coef_b)
        else:
            solo_optimized = False
            ocf = ocf[ieqtl.mask]

        # Construct the OCF ieQTL matrix.
        X_opt = np.copy(X_start)
        X_opt[:, 2] = ocf
        X_opt[:, 3] = X_opt[:, 1] * X_opt[:, 2]

        # Calculate the pearson R.
        r_squared_opt = None
        if not solo_optimized:
            pearsonr_opt = calc_pearsonr_vector(x=y, y=fit_and_predict(X=X_opt, y=y))
            r_squared_opt = pearsonr_opt * pearsonr_opt

        # Construct plot data frames.
        df1 = pd.DataFrame(
            X_start, columns=["intercept", "genotype", "covariate", "interaction"]
        )
        df2 = pd.DataFrame(
            X_opt, columns=["intercept", "genotype", "covariate", "interaction"]
        )
        for df in [df1, df2]:
            df["expression"] = y
            df["group"] = df["genotype"].round(0)

        annot1 = [
            "N = {:,}".format(ieqtl.n),
            "R^2 = {:.2f}".format(r_squared_start),
            "Betas = {}".format(", ".join(["{:.2f}".format(x) for x in ieqtl.betas])),
            "SD = {}".format(", ".join(["{:.2f}".format(x) for x in ieqtl.std])),
            "t-values = {}".format(
                ", ".join(["{:.2f}".format(x) for x in ieqtl.betas / ieqtl.std])
            ),
            "p-value = {:.2e}".format(ieqtl.p_value),
        ]
        annot2 = ["N = {:,}".format(ieqtl.n)]
        if r_squared_opt is not None:
            annot2.append("R^2 = {:.2f}".format(r_squared_start))

        # Plot.
        self.create_optimization_figure(
            df1=df1,
            df2=df2,
            annot1=annot1,
            annot2=annot2,
            gene=ieqtl.get_gene(),
            cov=ieqtl.get_cov(),
            title="{}:{}".format(ieqtl.get_ieqtl_id(), label),
            outdir=outdir,
            solo_optimized=solo_optimized,
        )

    def create_optimization_figure(
        self, df1, df2, annot1, annot2, gene, cov, title, outdir, solo_optimized
    ):
        sns.set_style("ticks")
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(24, 9))

        self.inter_plot(
            fig=fig,
            ax=ax1,
            df=df1,
            x="covariate",
            y="expression",
            group="group",
            palette=self.palette,
            xlabel=cov,
            ylabel=gene,
            annot=annot1,
            title="start",
        )

        p2_title = "optimized"
        file_appendix = ""
        if solo_optimized:
            p2_title = "optimized [solo]"
            file_appendix = "_soloOptimized"

        self.inter_plot(
            fig=fig,
            ax=ax2,
            df=df2,
            x="covariate",
            y="expression",
            group="group",
            palette=self.palette,
            xlabel="{} [optimized]".format(cov),
            ylabel=gene,
            annot=annot2,
            title=p2_title,
        )

        plt.suptitle(title, fontsize=18)

        fig.savefig(
            os.path.join(
                outdir,
                "{}{}_inter_optimization_plot.png".format(
                    title.replace(":", "-"), file_appendix
                ),
            )
        )
        plt.close()

    @staticmethod
    def eqtl_plot(
        fig,
        ax,
        df,
        x="x",
        y="y",
        palette=None,
        annot=None,
        xlabel="",
        ylabel="",
        title="",
    ):
        sns.despine(fig=fig, ax=ax)

        sns.regplot(
            x=x,
            y=y,
            data=df,
            scatter=False,
            ci=None,
            line_kws={"color": "#000000"},
            ax=ax,
        )
        sns.violinplot(x=x, y=y, data=df, palette=palette, cut=0, zorder=-1, ax=ax)
        plt.setp(ax.collections, alpha=0.75)
        sns.boxplot(x=x, y=y, data=df, whis=np.inf, color="white", zorder=-1, ax=ax)

        if annot is not None:
            for i, annot_label in enumerate(annot):
                ax.annotate(
                    annot_label,
                    xy=(0.03, 0.94 - (i * 0.04)),
                    xycoords=ax.transAxes,
                    color="#000000",
                    alpha=0.75,
                    fontsize=12,
                    fontweight="bold",
                )

        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=14, fontweight="bold")

    @staticmethod
    def inter_plot(
        fig,
        ax,
        df,
        x="x",
        y="y",
        group="group",
        palette=None,
        annot=None,
        xlabel="",
        ylabel="",
        title="",
    ):
        if len(set(df[group].unique()).symmetric_difference({0, 1, 2})) > 0:
            return

        sns.despine(fig=fig, ax=ax)

        for i, group_id in enumerate([0, 1, 2]):
            subset = df.loc[df[group] == group_id, :]
            n = subset.shape[0]

            coef_str = "NA"
            if len(subset.index) > 1:
                # Regression.
                coef, p = stats.spearmanr(subset[y], subset[x])
                coef_str = "{:.2f}".format(coef)

                # Plot.
                sns.regplot(
                    x=x,
                    y=y,
                    data=subset,
                    ci=None,
                    scatter_kws={
                        "facecolors": palette[group_id],
                        "linewidth": 0,
                        "alpha": 0.3,
                    },
                    line_kws={"color": palette[group_id], "alpha": 0.75},
                    ax=ax,
                )

            # Add the text.
            ax.annotate(
                "{}: r = {} [n={}]".format(group_id, coef_str, n),
                xy=(0.03, 0.94 - (i * 0.04)),
                xycoords=ax.transAxes,
                color=palette[group_id],
                alpha=0.75,
                fontsize=12,
                fontweight="bold",
            )

        if annot is not None:
            for i, annot_label in enumerate(annot):
                ax.annotate(
                    annot_label,
                    xy=(0.03, 0.82 - (i * 0.04)),
                    xycoords=ax.transAxes,
                    color="#000000",
                    alpha=0.75,
                    fontsize=12,
                    fontweight="bold",
                )

        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=14, fontweight="bold")
