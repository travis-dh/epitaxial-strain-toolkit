# Epitaxial Strain Toolkit (ESTK)

ESTK is a Python package for preparing and managing epitaxial strain calculations.

It provides tools for generating strained structures, organizing calculation workflows, and creating helper files for running calculations on HPC systems.

## Installation

ESTK is currently available as a source distribution.

```bash
git clone https://github.com/travis-dh/epitaxial-strain-toolkit.git
cd epitaxial-strain-toolkit
pip install -e .
```
Alternatively, it can be installed by running:
```bash
pip install git+https://github.com/travis-dh/epitaxial-strain-toolkit.git
```
## Typical workflow and basic usage

A typical ESTK workflow looks like:

```bash
# Generate only the (001) and (111) orientations from -5% to +5% strain
estk prepare BaTiO3.cif --strain 5 --orientations 001 111

# Configure your cluster once
estk config set partition skx-dev
estk config set account AB-CDE123456

# Generate the Slurm array script
estk slurm --max-concurrent 10

# Submit the calculations
sbatch runjob_array.slurm

# Later, after some jobs have completed...
estk slurm
sbatch runjob_array.slurm
```

When `estk slurm` is run again, ESTK automatically updates the job manifest and regenerates the Slurm array so that completed calculations are skipped and only unfinished jobs are resubmitted.

## License

ESTK is released under the GNU General Public License v3.0. See the LICENSE file for details.
