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

WORKDIR=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$ROOT/joblist.txt")

if [[ -z "$WORKDIR" ]]; then
    echo "No entry for array index $SLURM_ARRAY_TASK_ID" >&2
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
    output_filename: str = "runjob_array.slurm",
) -> Path:
    """Generate a Slurm array script for unfinished calculations in a project."""
    if scheduler != "slurm":
        raise NotImplementedError(
            f"scheduler={scheduler!r} not supported yet -- only 'slurm' is implemented"
        )

    project_dir = Path(project_dir)
    if project_dir.is_absolute():
        raise ValueError(
            "project_dir must be relative to the directory where the Slurm script "
            "will be submitted."
        )

    project_dir_text = project_dir.as_posix().rstrip("/")
    (project_dir / "logs").mkdir(parents=True, exist_ok=True)

    update_job_statuses(project_dir)
    joblist_path = write_job_manifest(project_dir)
    n_jobs = sum(1 for _ in joblist_path.open())
    if n_jobs == 0:
        raise ValueError("Nothing left to submit -- every strain is already converged.")

    placeholders = []
    if partition == "<PARTITION>":
        placeholders.append("<PARTITION>")
    if account == "<ACCOUNT>":
        placeholders.append("<ACCOUNT>")

    if placeholders:
        print(
            "WARNING: The generated Slurm script contains placeholder value(s): "
            f"{', '.join(placeholders)}.\n"
            "Replace them in the generated script before submitting with `sbatch`, "
            "or regenerate the script with, for example:\n\n"
            f"    estk slurm {project_dir} --partition normal --account TG-XXXXXXX\n"
        )

    script = TEMPLATE.format(
        project_dir=project_dir_text,
        job_name=job_name,
        partition=partition,
        nodes=nodes,
        ntasks=ntasks,
        account=account,
        walltime=walltime,
        max_index=n_jobs - 1,
        throttle=f"%{max_concurrent}" if max_concurrent else "",
        module_loads="\n".join(
            f"module load {module}" for module in (modules or DEFAULT_MODULES)
        ),
        executable=executable,
    )
    output_path = Path(output_filename)
    output_path.write_text(script)
    output_path.chmod(0o755)
    print(f"Wrote {output_path} (array 0-{n_jobs - 1}, {n_jobs} job(s))")
    return output_path
