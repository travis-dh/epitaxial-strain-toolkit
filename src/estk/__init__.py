"""
Epitaxial Strain Toolkit
A reusable Python package for preprocessing VASP structures with 
symmetry-aware orientation and biaxial strain generation.
"""

# Expose the core orientation logic
from .orientation_generator import (
    generate_orientations,
    symmetry_scan,
    check_symmetry
)

# Expose the core strain logic
from .strain_generator import (
    generate_strains_for_all_orientations,
    apply_biaxial_strain
)

# Expose the metadata manager for manual manifest inspection if needed
from .metadata import MetadataManager

from .slurm import generate_slurm_array
from .job_manifest import write_job_manifest, update_job_statuses

# Expose naming utilities
from .utils import (
    miller_label,
    strain_label
)

# Define the public API of the package
__all__ = [
    "generate_orientations",
    "symmetry_scan",
    "check_symmetry",
    "generate_strains_for_all_orientations",
    "apply_biaxial_strain",
    "MetadataManager",
    "miller_label",
    "strain_label",
    "generate_slurm_array",       
    "write_job_manifest",         
    "update_job_statuses",        
]