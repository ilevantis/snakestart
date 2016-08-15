# Snakestart

A template + script to set up a basic conda env with snakemake and a sensible directory structure.

## Install

Projects based on this template require a working install of [miniconda](http://conda.pydata.org/docs/install/quick.html) and [conda-env](https://github.com/conda/conda-env).

1. Download this repo and`cd` into it
2. `cp snakestart.bash ~/bin/snakestart`
3. `cp snakestart $XDG_CONFIG_HOME/`

## Use

Snakestart takes 1 argument: the name of the project.
e.g. `snakestart my_project`

It will create a directory with the name of the project and the current date and create a conda environment with the project name. This conda environment includes snakemake, python3 and the bioconda and r channels.

The `Snakefile` contains some useful rules for updating defined dependencies when pushing to a remote git repo.

**Example:**
```bash
snakestart my_project
cd my_project_2016-08-15
git init && git add -A && git commit -m "first"
git remote add origin...
snakemake push
```