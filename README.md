[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d46ac6670e8a4016a382434445668d70)](https://www.codacy.com/app/herculesl/isle?utm_source=github.com&utm_medium=referral&utm_content=EconomicSL/isle&utm_campaign=badger)

# isle

# Installation of dependencies

If the dependencies haven't been installed, run this command in a terminal

```
$ pip install -r requirements.txt
```

# Usage

## Simulation 

Execute the simulation with this command

```
$ python3 start.py
```

## Simulation with additional options

The ```start.py``` script accepts a number of options. 

```
usage: start.py [-h] [--abce] [--oneriskmodel] [--riskmodels {1,2,3,4}]
                [--replicid REPLICID] [--replicating]
                [--randomseed RANDOMSEED] [--foreground] [-p] [-v]
```

See the help for more details

```
python3 start.py --help
```

## Graphical simulation runs

abce can be used to run simulations with a graphical interface:

```
python3 start.py --abce
```

## Ensemble simulations

The bash scripts ```starter_*.sh``` can be used to run ensembles of a large number of simulations for settings with 1-4 different riskmodels. ```starter_two.sh``` is set up to generate random seeds and risk event schedules that are - for consistency and comparability - also used by the other scripts (i.e. ```starter_two.sh``` needs to be run first).

```
bash starter_two.sh
bash starter_one.sh
bash starter_four.sh
bash starter_three.sh
```

## Plotting

Use the scripts ```plotter_pl_timescale.py``` and  ```visualize.py``` for plotting/visualizing single simulation runs. Use  ```.py```,  ```metaplotter_pl_timescale.py```, or  ```metaplotter_pl_timescale_additional_measures.py``` to visualize ensemble runs.

