"""job_manifest.py: Convergence status synchronization and job execution list generation."""
from pathlib import Path
from collections import deque
from .metadata import MetadataManager


def _converged(outcar_path: Path) -> bool:
    """Efficiently checks the end of OUTCAR for the convergence string."""
    try:
        with open(outcar_path, 'r') as f:
            last_lines = "".join(deque(f, 20))
        return "reached required accuracy" in last_lines
    except (FileNotFoundError, UnicodeDecodeError, IOError):
        return False


def update_job_statuses(project_dir: str | Path = "oriented_structures") -> None:
    """Scan every strain leaf directory's OUTCAR and sync metadata status to match."""
    project_dir = Path(project_dir)
    mm = MetadataManager(project_dir)

    for orient_label, entry in mm.data["orientations"].items():
        for strain_label, strain_entry in entry["strains"].items():
            outcar = project_dir / orient_label / strain_label / "OUTCAR"
            if not outcar.exists():
                status = "Initialized"
            elif _converged(outcar):
                status = "Converged"
            else:
                status = "Incomplete"

            if strain_entry.get("status") != status:
                mm.upsert_strain(orient_label, strain_label, strain_entry["value"], status=status)


def write_job_manifest(
    project_dir: str | Path = "oriented_structures",
    skip_status=("Converged",),
    filename: str = "joblist.txt",
) -> Path:
    """Build joblist.txt from current metadata, cross-checked against disk."""
    project_dir = Path(project_dir)
    mm = MetadataManager(project_dir)

    lines, skipped_missing = [], []
    for orient_label in sorted(mm.data["orientations"]):
        entry = mm.data["orientations"][orient_label]
        for strain_label in sorted(entry["strains"]):
            strain_entry = entry["strains"][strain_label]
            if strain_entry.get("status") in skip_status:
                continue

            rel_path = f"{orient_label}/{strain_label}"
            if not (project_dir / rel_path / "INCAR").exists():
                skipped_missing.append(rel_path)
                continue

            lines.append(rel_path)

    manifest_path = project_dir / filename
    manifest_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"Wrote {len(lines)} job(s) to {manifest_path}")
    if skipped_missing:
        print(f"WARNING: {len(skipped_missing)} metadata entries have no INCAR on disk (skipped): {skipped_missing[:5]}")
    return manifest_path