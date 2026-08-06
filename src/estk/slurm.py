"""
slurm.py: HPC integration and Slurm workload manager orchestration.

Provides utilities to synchronize project job manifests and generate Slurm 
array scripts. The generated scripts are designed to execute calculations 
within the toolkit's 'Uniform Depth' directory architecture.
"""
from datetime import datetime
from pathlib import Path

from .job_manifest import update_job_statuses, write_job_manifest


DEFAULT_MODULES = ["intel/23.1", "impi/21.9"]

TEMPLATE = """#!/bin/bash
#SBATCH -J {job_name}
#SBATCH -o {project_dir}/logs/slurm_%A_%a.out
#SBATCH -e {project_dir}/logs/slurm_%A_%a.err
#SBATCH -p {partition}
#SBATCH -N {nodes}
#SBATCH -n {ntasks}
#SBATCH -A {account}
#SBATCH -t {walltime}
#SBATCH --array=0-{max_index}{throttle}

source deactivate
module --force purge
{module_loads}

ROOT="${{SLURM_SUBMIT_DIR}}/{project_dir}"
JOBLIST="$ROOT/{joblist_filename}"

WORKDIR=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$JOBLIST")

if [[ -z "$WORKDIR" ]]; then
    echo "No entry for array index $SLURM_ARRAY_TASK_ID in $JOBLIST" >&2
    exit 1
fi

cd "$ROOT/$WORKDIR" || exit 1

ibrun {executable} > stdout
"""


def generate_slurm_array(
    project_dir: str | Path = "oriented_structures",
    scheduler: str = "slurm",
    executable: str = "$VASPXY",
    partition: str = "<PARTITION>",
    nodes: int = 1,
    ntasks: int = 48,
    walltime: str = "02:00:00",
    account: str = "<ACCOUNT>",
    job_name: str = "epi",
    modules: list[str] | None = None,
    max_concurrent: int | None = None,
    max_submit: int | None = None,
    orientation_labels: list[str] | None = None,
    output_filename: str = "runjob_array.slurm",
) -> Path:
    """Generate a bounded Slurm array for unfinished calculations."""
    if scheduler != "slurm":
        raise NotImplementedError(
            f"scheduler={scheduler!r} is unsupported; only 'slurm' is implemented."
        )

    if max_concurrent is not None and max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1.")

    if max_submit is not None and max_submit < 1:
        raise ValueError("max_submit must be at least 1.")

    project_path = Path(project_dir)
    if project_path.is_absolute():
        raise ValueError(
            "project_dir must be relative to the directory where sbatch is run."
        )

    project_dir_text = project_path.as_posix().rstrip("/")
    (project_path / "logs").mkdir(parents=True, exist_ok=True)

    update_job_statuses(project_path)

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    joblist_filename = f"joblist_{batch_id}.txt"
    joblist_path = write_job_manifest(
        project_path,
        filename=joblist_filename,
        max_jobs=max_submit,
        orientation_labels=orientation_labels,
    )

    n_jobs = sum(1 for _ in joblist_path.open(encoding="utf-8"))
    if n_jobs == 0:
        joblist_path.unlink(missing_ok=True)
        orientation_text = (
            f" for orientation(s) {', '.join(orientation_labels)}"
            if orientation_labels
            else ""
        )
        raise ValueError(
            f"Nothing left to submit{orientation_text}; "
            "all selected calculations are converged."
        )

    placeholders = []
    if partition in (None, "<PARTITION>"):
        placeholders.append("<PARTITION>")
    if account in (None, "<ACCOUNT>"):
        placeholders.append("<ACCOUNT>")

    if placeholders:
        print(
            "WARNING: The generated Slurm script contains placeholder value(s): "
            f"{', '.join(placeholders)}. Configure them before submission."
        )

    effective_concurrent = max_concurrent
    if effective_concurrent is not None:
        effective_concurrent = min(effective_concurrent, n_jobs)

    script = TEMPLATE.format(
        project_dir=project_dir_text,
        joblist_filename=joblist_filename,
        job_name=job_name,
        partition=partition or "<PARTITION>",
        nodes=nodes,
        ntasks=ntasks,
        account=account or "<ACCOUNT>",
        walltime=walltime,
        max_index=n_jobs - 1,
        throttle=(
            f"%{effective_concurrent}"
            if effective_concurrent is not None
            else ""
        ),
        module_loads="\n".join(
            f"module load {module}"
            for module in (modules or DEFAULT_MODULES)
        ),
        executable=executable,
    )

    output_path = Path(output_filename)
    output_path.write_text(script, encoding="utf-8")
    output_path.chmod(0o755)

    orientation_text = (
        f", orientations {', '.join(orientation_labels)}"
        if orientation_labels
        else ""
    )
    print(
        f"Wrote {output_path} using {joblist_path} "
        f"(array 0-{n_jobs - 1}, {n_jobs} job(s){orientation_text})"
    )
    return output_path