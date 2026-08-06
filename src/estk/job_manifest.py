"""job_manifest.py: Convergence status synchronization and job execution list generation."""
from pathlib import Path

from .metadata import MetadataManager


def _converged(outcar_path: Path) -> bool:
    """Return whether an OUTCAR reports successful ionic convergence."""
    try:
        return "reached required accuracy" in outcar_path.read_text()
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return False


def update_job_statuses(
    project_dir: str | Path = "oriented_structures",
) -> None:
    """Synchronize each calculation's status with its OUTCAR."""
    project_path = Path(project_dir)
    metadata_manager = MetadataManager(project_path)

    for orientation_label, orientation in metadata_manager.data["orientations"].items():
        for strain_label, strain in orientation["strains"].items():
            outcar_path = (
                project_path
                / orientation_label
                / strain_label
                / "OUTCAR"
            )

            if not outcar_path.exists():
                status = "Initialized"
            elif _converged(outcar_path):
                status = "Converged"
            else:
                status = "Incomplete"

            if strain.get("status") != status:
                metadata_manager.upsert_strain(
                    orientation_label,
                    strain_label,
                    strain["value"],
                    status=status,
                )


def write_job_manifest(
    project_dir: str | Path = "oriented_structures",
    skip_status: tuple[str, ...] = ("Converged",),
    filename: str = "joblist.txt",
    max_jobs: int | None = None,
) -> Path:
    """
    Write a deterministic list of calculations requiring execution.

    Incomplete calculations are listed before calculations that have never run.
    When ``max_jobs`` is supplied, only that many calculations are written.
    """
    if max_jobs is not None and max_jobs < 1:
        raise ValueError("max_jobs must be at least 1.")

    project_path = Path(project_dir)
    metadata_manager = MetadataManager(project_path)

    jobs: list[tuple[int, str]] = []
    skipped_missing: list[str] = []

    for orientation_label in sorted(metadata_manager.data["orientations"]):
        orientation = metadata_manager.data["orientations"][orientation_label]

        for strain_label in sorted(orientation["strains"]):
            strain = orientation["strains"][strain_label]
            status = strain.get("status", "Initialized")

            if status in skip_status:
                continue

            relative_path = f"{orientation_label}/{strain_label}"
            if not (project_path / relative_path / "INCAR").exists():
                skipped_missing.append(relative_path)
                continue

            priority = 0 if status == "Incomplete" else 1
            jobs.append((priority, relative_path))

    jobs.sort(key=lambda item: (item[0], item[1]))
    selected_jobs = jobs[:max_jobs] if max_jobs is not None else jobs
    lines = [relative_path for _, relative_path in selected_jobs]

    manifest_path = project_path / filename
    manifest_path.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )

    print(
        f"Wrote {len(lines)} of {len(jobs)} unfinished job(s) "
        f"to {manifest_path}"
    )

    if skipped_missing:
        print(
            "WARNING: "
            f"{len(skipped_missing)} metadata entries have no INCAR and were skipped: "
            f"{skipped_missing[:5]}"
        )

    return manifest_path