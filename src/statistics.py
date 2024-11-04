"""
File:         statistics.py
Created:      2021/04/14
Last Changed: 2022/07/25
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
import math
import time

# Third party imports.
import numpy as np
from scipy.special import betainc
from statsmodels.regression.linear_model import OLS


def remove_covariates(y_m, X_m=None, X_inter_m=None, inter_m=None, log=None):
    if X_m is None and X_inter_m is None:
        log.warning("No covariates to be removed, skipping step.")
        return y_m
    if X_inter_m is not None and inter_m is None:
        log.error("Error in remove_covariates")
        exit()
    if inter_m is not None and (y_m.shape != inter_m.shape):
        log.error("Error in remove_covariates")
        exit()

    # Initialize the base matrix with an intercept.
    correction_matrix = np.ones((y_m.shape[1], 1))

    # Add the technical covariates.
    if X_m is not None:
        X_m_tmp = np.copy(X_m)

        # Force 2D matrix.
        if np.ndim(X_m_tmp) == 1:
            X_m_tmp = X_m_tmp[:, np.newaxis]

        # Merge.
        correction_matrix = np.hstack((correction_matrix, X_m_tmp))

    # Prepare the technical covariates * genotype matrix.
    X_inter_m_tmp = None
    if X_inter_m is not None and inter_m is not None:
        X_inter_m_tmp = np.copy(X_inter_m)

        # Force 2D matrix.
        if np.ndim(X_inter_m_tmp) == 1:
            X_inter_m_tmp = X_inter_m_tmp[:, np.newaxis]

    # Loop over expression rows.
    last_print_time = None
    n_rows = y_m.shape[0]
    y_corrected_m = np.empty(y_m.shape, dtype=np.float64)
    for i in range(n_rows):
        # Update user on progress.
        now_time = int(time.time())
        if log is not None and (
            last_print_time is None
            or (now_time - last_print_time) >= 30
            or i == (n_rows - 1)
        ):
            log.debug(
                "\t\t{:,}/{:,} rows processed [{:.2f}%]".format(
                    i, (n_rows - 1), (100 / (n_rows - 1)) * i
                )
            )
            last_print_time = now_time

        # Mask the Nan values.
        sample_mask = ~np.isnan(y_m[i, :])

        # Initialize the correction matrix.
        X = np.copy(correction_matrix[sample_mask, :])

        # Add the covariates with interaction termn.
        if X_inter_m_tmp is not None:
            X_inter_times_inter_m = (
                X_inter_m_tmp[sample_mask, :] * inter_m[i, sample_mask][:, np.newaxis]
            )
            X = np.hstack((X, X_inter_times_inter_m))

        # Mask the features with 0 std except for the first one.
        feature_mask = np.std(X, axis=0) != 0
        feature_mask[0] = True

        # Calculate residuals using OLS.
        y_corrected_m[i, ~sample_mask] = np.nan
        y_corrected_m[i, sample_mask] = calculate_residuals_ols(
            X=X[:, feature_mask], y=y_m[i, sample_mask]
        )

    del X_m_tmp, X_inter_m_tmp

    return y_corrected_m


def remove_covariates_elementwise(y_m, X_m, a):
    y_corrected_m = np.empty(y_m.shape, dtype=np.float64)

    # Construct the feature matrix. Only fill in the intercept and
    # the static covariate.
    X = np.empty((X_m.shape[1], 3), dtype=np.float64)
    X[:, 0] = 1
    X[:, 2] = a

    for i in range(y_m.shape[0]):
        # Fill in the variable covariate (i.e. genotype).
        X[:, 1] = X_m[i, :]

        # Mask the Nan values.
        sample_mask = ~np.isnan(y_m[i, :])

        # Mask the features with 0 std except for the first one.
        feature_mask = np.std(X[sample_mask, :], axis=0) != 0
        feature_mask[0] = True

        # Calculate residuals using OLS.
        y_corrected_m[i, ~sample_mask] = np.nan
        y_corrected_m[i, sample_mask] = calc_residuals(
            y=y_m[i, sample_mask],
            y_hat=fit_and_predict(
                X=X[sample_mask, :][:, feature_mask], y=y_m[i, sample_mask]
            ),
        )

    return y_corrected_m


def inverse(X):
    X_square = X.T.dot(X)
    try:
        return np.linalg.inv(X_square)
    except np.linalg.LinAlgError:
        print("Warning: using pseudo-inverse")
        return np.linalg.pinv(X_square)


def fit(X, y, inv_m=None):
    if inv_m is None:
        inv_m = inverse(X)
    return inv_m.dot(X.T).dot(y)


def predict(X, betas):
    return np.dot(X, betas)


def fit_and_predict(X, y):
    return predict(X=X, betas=fit(X=X, y=y))


def calc_residuals(y, y_hat):
    return y - y_hat


def calc_rss(y, y_hat):
    res = calc_residuals(y=y, y_hat=y_hat)
    res_squared = res * res
    return np.sum(res_squared)


def calc_std(rss, n, df, inv_m):
    return np.sqrt(rss / (n - df) * np.diag(inv_m))


def calculate_residuals_ols(X, y):
    return OLS(y, X).fit().resid


def calc_p_value(rss1, rss2, df1, df2, n):
    """
    last row == stats.f.sf(f_value, dfn=(df2 - df1), dfd=(n - df2)) but this
    is faster somehow.

    https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.betainc.html

    1 - I(a,b,x) = I(b, a, 1-x)
    """
    if rss2 >= rss1:
        return 1
    dfn = df2 - df1
    dfd = n - df2
    f_value = ((rss1 - rss2) / dfn) / (rss2 / dfd)
    p_value = betainc(dfd / 2, dfn / 2, 1 - ((dfn * f_value) / ((dfn * f_value) + dfd)))
    if p_value == 0:
        p_value = 2.2250738585072014e-308
    return p_value


def calc_vertex_xpos(a, b):
    a[a == 0] = np.nan
    vertex_xpos = -b / (2 * a)
    return vertex_xpos.astype(np.float64)


def calc_pearsonr_vector(x, y):
    x_dev = x - np.mean(x)
    y_dev = y - np.mean(y)
    dev_sum = np.sum(x_dev * y_dev)
    x_rss = np.sum(x_dev * x_dev)
    y_rss = np.sum(y_dev * y_dev)
    return dev_sum / np.sqrt(x_rss * y_rss)


def calc_regression_log_likelihood(residuals):
    """
    https://www.stat.cmu.edu/~cshalizi/mreg/15/lectures/06/lecture-06.pdf

    this boils down to np.sum(stats.norm.logpdf(residuals, 0.0, np.std(residuals)))
    """
    n = np.size(residuals)
    s = np.std(residuals)
    return (
        -(n / 2) * math.log(2 * math.pi)
        - n * math.log(s)
        - (1 / (2 * s**2)) * np.sum(residuals**2)
    )
