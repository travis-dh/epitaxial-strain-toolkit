"""
strain_generator.py: Biaxial strain application and calculation tree generation.

This module applies biaxial strain to the in-plane lattice vectors of oriented 
structures and generates fully-populated VASP input sets. It is designed to 
maintain a 'Uniform Depth' directory architecture, enabling Slurm Job Arrays 
to execute calculations directly within the leaf subdirectories.
"""
import numpy as np
from pathlib import Path
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

from .utils import strain_label
from .metadata import MetadataManager

DEFAULT_INCAR_PARAMS = dict(
    ENCUT=520, 
    ISIF=3, 
    LCHARG=False, 
    ALGO='Normal', 
    ISPIN=2,
    NELMIN=2, 
    NELM=100, 
    NCORE=8, 
    ISMEAR=0, 
    EDIFF=1E-5, 
    EDIFFG=-0.01, 
    LASPH=True, 
    LREAL=False, 
    IBRION=2, 
    NSW=300, 
    PREC='A', 
    ADDGRID=True
)

DEFAULT_KPOINTS_PARAMS = dict(reciprocal_density=100)

def apply_biaxial_strain(structure: Structure, strain_value: float) -> Structure:
    """
    Applies biaxial strain to the in-plane (a and b) lattice vectors [1, 5].
    The strain value is a percentage (e.g., -4.0 for 4% compression).
    """
    strained_struct = structure.copy()
    lattice_matrix = strained_struct.lattice.matrix.copy()
    
    scale_factor = 1.0 + (strain_value / 100.0)

    lattice_matrix[0] *= scale_factor
    lattice_matrix[1] *= scale_factor
    
    strained_struct.lattice = lattice_matrix
    return strained_struct

def generate_strains_for_all_orientations(
    project_dir: str | Path = "oriented_structures",
    min_strain: float = -4.0,
    max_strain: float = 4.0,
    step: float = 0.5,
    include_zero: bool = True,
    write_vasp: bool = True,
    orientation_labels: list[str] | None = None,
):
    """
    Walks through orientations and generates fully-populated VASP directories [2].
    Ensures 'Uniform Depth' so Slurm Job Arrays can run calculations 
    directly in the leaf subdirectories [5].
    """
    project_path = Path(project_dir)
    mm = MetadataManager(project_path)
    
    strains = np.arange(min_strain, max_strain + step, step)
    if include_zero and 0.0 not in strains:
        strains = np.sort(np.append(strains, 0.0))

    allowed_orientations = set(orientation_labels) if orientation_labels is not None else None
    for orient_dir in [d for d in project_path.iterdir() if d.is_dir()]:
        if allowed_orientations is not None and orient_dir.name not in allowed_orientations:
            continue
        ref_poscar_path = orient_dir / "POSCAR_reference"
        
        if not ref_poscar_path.exists():
            continue
            
        print(f"Applying strain to orientation: {orient_dir.name}")
        ref_structure = Structure.from_file(ref_poscar_path)
        
        for strain_val in strains:
            label = strain_label(strain_val)
            target_path = orient_dir / label
            target_path.mkdir(parents=True, exist_ok=True)
            
            strained_struct = apply_biaxial_strain(ref_structure, strain_val)
            
            if write_vasp:
                v_set = MPRelaxSet(
                    strained_struct,
                    user_incar_settings=DEFAULT_INCAR_PARAMS,
                    user_kpoints_settings=DEFAULT_KPOINTS_PARAMS,
                    user_potcar_functional="PBE_64",
                )
                v_set.write_input(str(target_path))
            else:
                strained_struct.to(fmt="poscar", filename=str(target_path / "POSCAR"))
            
            mm.upsert_strain(
                miller_label=orient_dir.name,
                strain_name=label,
                strain_value=float(strain_val),
            )

if __name__ == "__main__":
    generate_strains_for_all_orientations()