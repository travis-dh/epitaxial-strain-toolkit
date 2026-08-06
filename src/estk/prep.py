"""prep.py: High-level orchestration of the complete project preparation workflow."""

from pymatgen.core import Structure

from .orientation_generator import generate_orientations, symmetry_scan
from .strain_generator import generate_strains_for_all_orientations


def prepare_project(
    input_file: str,
    project_dir: str = "oriented_structures",
    min_strain: float = -4.0,
    max_strain: float = 4.0,
    step: float = 0.5,
    include_zero: bool = True,
    orientations: list[str] | None = None,
) -> None:
    """Run the complete ESTK preparation workflow."""

    print(f"--- Symmetry Scan for {input_file} ---")

    structure = Structure.from_file(input_file)
    symmetry_scan(structure)

    print("\n--- Generating Orientations ---")
    generated_orientations = generate_orientations(
        input_file,
        output_dir=project_dir,
        requested_orientations=orientations,
    )

    print("\n--- Generating Strained Structures ---")
    generate_strains_for_all_orientations(
        project_dir=project_dir,
        min_strain=min_strain,
        max_strain=max_strain,
        step=step,
        include_zero=include_zero,
        orientation_labels=generated_orientations,
    )

    print(f"\nSetup complete in directory: {project_dir}")