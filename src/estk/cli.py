"""
cli.py
Command-line entry point for ESTK. Wires argparse sub-commands
(`prepare`, `slurm`, `config`) to the corresponding package functions.
"""

import argparse

from .config import get_config_value, load_config, set_config_value
from .prep import prepare_project
from .slurm import generate_slurm_array


def handle_prepare(args) -> None:
    if args.strain is not None:
        strain_limit = abs(args.strain)
        min_strain = -strain_limit
        max_strain = strain_limit
    else:
        min_strain = args.min_strain
        max_strain = args.max_strain

    prepare_project(
        input_file=args.input_file,
        project_dir=args.project_dir,
        min_strain=min_strain,
        max_strain=max_strain,
        step=args.step,
        include_zero=not args.no_zero,
        orientations=args.orientations,
    )


def handle_slurm(args) -> None:
    """Generate a Slurm array script."""
    print("--- Generating Slurm Array Script ---")

    generate_slurm_array(
        project_dir=args.project_dir,
        partition=args.partition or get_config_value("partition"),
        nodes=args.nodes,
        ntasks=args.ntasks,
        walltime=args.walltime,
        account=args.account or get_config_value("account"),
        max_concurrent=args.max_concurrent,
        max_submit=args.max_submit,
    )

    print(f"Slurm script generated for project: {args.project_dir}")


def handle_config(args) -> None:
    """Get, set, or list persisted ESTK configuration values."""
    if args.config_command == "set":
        set_config_value(args.key, args.value)
        print(f"Set '{args.key}' = '{args.value}'")
    elif args.config_command == "get":
        value = get_config_value(args.key)
        if value is None:
            print(f"'{args.key}' is not set")
        else:
            print(value)
    elif args.config_command == "list":
        config = load_config()
        if not config:
            print("No configuration values set.")
        else:
            for key, value in config.items():
                print(f"{key} = {value}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="estk",
        description=(
            "Epitaxial Strain Toolkit (ESTK): "
            "symmetry-aware VASP preprocessing."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Subcommands",
    )

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Generate oriented structures and strained inputs",
    )
    prepare_parser.add_argument(
        "input_file",
        help="Path to the input POSCAR or CIF",
    )
    prepare_parser.add_argument(
        "--project-dir",
        default="oriented_structures",
        help="Output directory (default: oriented_structures)",
    )
    prepare_parser.add_argument(
        "--strain",
        type=float,
        default=None,
        help="Symmetric strain limit in percent, e.g. 4 gives -4 to +4",
    )
    prepare_parser.add_argument(
        "--min-strain",
        type=float,
        default=-4.0,
        help="Minimum biaxial strain in percent (default: -4.0)",
    )
    prepare_parser.add_argument(
        "--max-strain",
        type=float,
        default=4.0,
        help="Maximum biaxial strain in percent (default: 4.0)",
    )
    prepare_parser.add_argument(
        "--step",
        type=float,
        default=0.5,
        help="Strain step in percent (default: 0.5)",
    )
    prepare_parser.add_argument(
        "--no-zero",
        action="store_true",
        help="Do not force inclusion of the zero-strain case",
    )
    prepare_parser.add_argument(
        "--orientations",
        nargs="+",
        metavar="HKL",
        default=None,
        help=(
            "Generate only requested Miller orientations, e.g. "
            "--orientations 001 111"
        ),
    )
    prepare_parser.set_defaults(func=handle_prepare)

    slurm_parser = subparsers.add_parser(
        "slurm",
        help="Generate or refresh the Slurm array script",
    )
    slurm_parser.add_argument(
        "project_dir",
        nargs="?",
        default="oriented_structures",
        help="Project directory to scan",
    )
    slurm_parser.add_argument("--nodes", type=int, default=1)
    slurm_parser.add_argument("--ntasks", type=int, default=48)
    slurm_parser.add_argument("--walltime", default="02:00:00")
    slurm_parser.add_argument(
        "--max-submit",
        type=int,
        default=None,
        help=(
            "Maximum unfinished calculations included in this array submission"
        ),
    )
    slurm_parser.add_argument(
        "--max-concurrent",
        type=int,
        default=None,
        help="Maximum array tasks allowed to run simultaneously",
    )
    slurm_parser.add_argument(
        "--partition",
        default=None,
        help="Slurm partition (overrides ESTK config)",
    )
    slurm_parser.add_argument(
        "--account",
        default=None,
        help="Slurm account/allocation (overrides ESTK config)",
    )
    slurm_parser.set_defaults(func=handle_slurm)

    config_parser = subparsers.add_parser(
        "config",
        help="Get, set, or list ESTK configuration values",
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_command",
        required=True,
        help="Config actions",
    )

    config_set_parser = config_subparsers.add_parser(
        "set",
        help="Set a configuration value",
    )
    config_set_parser.add_argument("key")
    config_set_parser.add_argument("value")

    config_get_parser = config_subparsers.add_parser(
        "get",
        help="Print a configuration value",
    )
    config_get_parser.add_argument("key")

    config_subparsers.add_parser(
        "list",
        help="List all stored configuration values",
    )
    config_parser.set_defaults(func=handle_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()