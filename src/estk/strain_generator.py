"""
strain_generator.py: Biaxial strain application and calculation tree generation.

This module applies biaxial strain to the in-plane lattice vectors of oriented 
structures and generates fully-populated VASP input sets. It is designed to 
maintain a 'Uniform Depth' directory architecture, enabling Slurm Job Arrays 
to execute calculations directly within the leaf subdirectories.
"""
from pathlib import Path

import numpy as np
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

from .metadata import MetadataManager
from .utils import strain_label


DEFAULT_INCAR_PARAMS = dict(
    ENCUT=520,
    ISIF=3,
    LCHARG=False,
    ALGO="Normal",
    ISPIN=2,
    NELMIN=2,
    NELM=100,
    NCORE=8,
    ISMEAR=0,
    EDIFF=1e-5,
    EDIFFG=-0.01,
    LASPH=True,
    LREAL=False,
    IBRION=2,
    NSW=300,
    PREC="A",
    ADDGRID=True,
)

DEFAULT_KPOINTS_PARAMS = dict(reciprocal_density=100)


def apply_biaxial_strain(
    structure: Structure,
    strain_value: float,
) -> Structure:
    """
    Apply biaxial strain to the in-plane lattice vectors.

    The strain value is expressed as a percentage. Fractional coordinates and
    the out-of-plane lattice vector are preserved.
    """
    strained_structure = structure.copy()
    lattice_matrix = strained_structure.lattice.matrix.copy()

    scale_factor = 1.0 + strain_value / 100.0
    lattice_matrix[0] *= scale_factor
    lattice_matrix[1] *= scale_factor

    strained_structure.lattice = lattice_matrix
    return strained_structure


def generate_strains_for_all_orientations(
    project_dir: str | Path = "oriented_structures",
    min_strain: float = -4.0,
    max_strain: float = 4.0,
    step: float = 0.5,
    include_zero: bool = True,
    write_vasp: bool = True,
    orientation_labels: list[str] | None = None,
) -> None:
    """
    Generate strained structures and VASP inputs for each selected orientation.
    """
    project_path = Path(project_dir)
    metadata_manager = MetadataManager(project_path)

    strains = np.arange(min_strain, max_strain + step, step)
    if include_zero and 0.0 not in strains:
        strains = np.sort(np.append(strains, 0.0))

    allowed_orientations = (
        set(orientation_labels) if orientation_labels is not None else None
    )

    for orientation_dir in (d for d in project_path.iterdir() if d.is_dir()):
        if (
            allowed_orientations is not None
            and orientation_dir.name not in allowed_orientations
        ):
            continue

        reference_path = orientation_dir / "POSCAR_reference"
        if not reference_path.exists():
            continue

        print(f"Applying strain to orientation: {orientation_dir.name}")
        reference_structure = Structure.from_file(reference_path)

        for strain_value in strains:
            label = strain_label(strain_value)
            target_path = orientation_dir / label
            target_path.mkdir(parents=True, exist_ok=True)

            strained_structure = apply_biaxial_strain(
                reference_structure,
                strain_value,
            )

            if write_vasp:
                input_set = MPRelaxSet(
                    strained_structure,
                    user_incar_settings=DEFAULT_INCAR_PARAMS,
                    user_kpoints_settings=DEFAULT_KPOINTS_PARAMS,
                )
                input_set.write_input(target_path)
            else:
                strained_structure.to(
                    fmt="poscar",
                    filename=target_path / "POSCAR",
                )

            metadata_manager.upsert_strain(
                miller_label=orientation_dir.name,
                strain_name=label,
                strain_value=float(strain_value),
            )


if __name__ == "__main__":
    generate_strains_for_all_orientations()