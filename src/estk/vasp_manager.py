from pathlib import Path
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

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
DEFAULT_POTCAR_FUNCTIONAL = "PBE_64"


def write_vasp_input_set(
    structure: Structure,
    output_dir: str | Path,
    incar_overrides: dict | None = None,
    kpoints_settings: dict | None = None,
    potcar_functional: str = DEFAULT_POTCAR_FUNCTIONAL,
) -> None:
    """Write a full VASP input set (INCAR, KPOINTS, POTCAR, POSCAR) for one structure."""
    incar_settings = {**DEFAULT_INCAR_PARAMS, **(incar_overrides or {})}
    kpoints = kpoints_settings or DEFAULT_KPOINTS_PARAMS

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vasp_set = MPRelaxSet(
        structure,
        user_incar_settings=incar_settings,
        user_kpoints_settings=kpoints,
        user_potcar_functional=potcar_functional,
    )
    vasp_set.write_input(str(output_dir))


def generate_vasp_inputs_for_project(
    project_dir: str | Path,
    structure_filename: str = "POSCAR",
    incar_overrides: dict | None = None,
    kpoints_settings: dict | None = None,
    potcar_functional: str = DEFAULT_POTCAR_FUNCTIONAL,
) -> list[Path]:
    """
    Recursively generate VASP input sets for all structures in a project.

    Each file matching ``structure_filename`` is loaded as a structure, and the
    corresponding INCAR, KPOINTS, POTCAR, and POSCAR files are written to the same
    directory using the specified settings. This is useful for regenerating VASP
    inputs across an existing project without modifying the underlying structures.
    """
    written = []
    for poscar_path in sorted(Path(project_dir).rglob(structure_filename)):
        structure = Structure.from_file(poscar_path)
        target_dir = poscar_path.parent
        write_vasp_input_set(
            structure, target_dir,
            incar_overrides=incar_overrides,
            kpoints_settings=kpoints_settings,
            potcar_functional=potcar_functional,
        )
        written.append(target_dir)
        print(f"Wrote VASP inputs -> {target_dir}")
    return written