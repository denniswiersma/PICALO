"""
File:         cmd_line_arguments.py
Created:      2020/11/16
Last Changed: 2023/08/21
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
import argparse

# Third party imports.

# Local application imports.


class CommandLineArguments:
    def __init__(self, program, version, description):
        # Safe variables.
        self.program = program
        self.version = version
        self.description = description

        # Get the arguments.
        parser = self.create_argument_parser()
        self.arguments = parser.parse_args()
        self.print_arguments()

    def create_argument_parser(self):
        parser = argparse.ArgumentParser(
            prog=self.program, description=self.description
        )

        # Add optional arguments.
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="{} {}".format(self.program, self.version),
            help="show program's version number and exit",
        )
        parser.add_argument(
            "-eq",
            "--eqtl",
            type=str,
            required=True,
            help="The path to the eqtl matrix.",
        )
        parser.add_argument(
            "-ge",
            "--genotype",
            type=str,
            required=True,
            help="The path to the genotype matrix.",
        )
        parser.add_argument(
            "-na",
            "--genotype_na",
            type=int,
            required=False,
            default=-1,
            help="The genotype value that equals a missing " "value. Default: -1.",
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
            "-co",
            "--covariate",
            type=str,
            required=True,
            help="The path to the covariate matrix (i.e. the "
            "matrix used as initial guess for the "
            "optimization)",
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
            "-hw",
            "--hardy_weinberg_pvalue",
            type=float,
            required=False,
            default=1e-4,
            help="The Hardy-Weinberg p-value threshold." "Default: >= 1e-4.",
        )
        parser.add_argument(
            "-maf",
            "--minor_allele_frequency",
            type=float,
            required=False,
            default=0.01,
            help="The MAF threshold. Default: >0.01.",
        )
        parser.add_argument(
            "-mgs",
            "--min_group_size",
            type=int,
            required=False,
            default=2,
            help="The minimal number of samples per genotype " "group. Default: >= 2.",
        )
        parser.add_argument(
            "-iea",
            "--ieqtl_alpha",
            type=float,
            required=False,
            default=0.05,
            help="The interaction eQTL significance cut-off. " "Default: <=0.05.",
        )
        parser.add_argument(
            "-n_components",
            type=int,
            required=False,
            default=10,
            help="The number of components to extract. " "Default: 10.",
        )
        parser.add_argument(
            "-min_iter",
            type=int,
            required=False,
            default=5,
            help="The minimum number of optimization "
            "iterations to perform per component. "
            "Default: 5.",
        )
        parser.add_argument(
            "-max_iter",
            type=int,
            required=False,
            default=100,
            help="The maximum number of optimization "
            "iterations to perform per component. "
            "Default: 100.",
        )
        parser.add_argument(
            "-tol",
            type=float,
            required=False,
            default=1e-3,
            help="The convergence threshold. The optimization "
            "will stop when the 1 - pearson correlation"
            "coefficient is below this threshold. "
            "Default: 1e-3.",
        )
        parser.add_argument(
            "-force_continue",
            action="store_true",
            help="Force to identify more components even if "
            "the previous one did not converge."
            " Default: False.",
        )
        parser.add_argument(
            "-o",
            "--outdir",
            type=str,
            required=False,
            default="output",
            help="The name of the output folder.",
        )
        parser.add_argument(
            "-verbose",
            action="store_true",
            help="Enable verbose output. Default: False.",
        )

        return parser

    def print_arguments(self):
        for arg in vars(self.arguments):
            print(
                "Input argument '{}' "
                "has value '{}'.".format(arg, getattr(self.arguments, arg))
            )

    def get_argument(self, arg_key):
        if self.arguments is not None and arg_key in self.arguments:
            value = getattr(self.arguments, arg_key)
        else:
            value = None

        return value

    def get_all_arguments(self):
        return self.arguments
