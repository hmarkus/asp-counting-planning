# ASP encoding to ground planning tasks

Encodes the relaxed-reachability of a PDDL planning task as a logic program. The
canonical model of this program is equivalent to all reachable atoms (and
actions). This can be used to find all possible ground atoms that are
relaxed-reachable in the planning task. In fact, this is how Fast Downward
grounds the input tasks. Similarly, this is how Powerlifted extracts
delete-relaxation heurisitics without grounding the problem.

So far, our logic program is a simple Datalog, although it could be expanded
with more sophisticated features. We are also focusing exclusively on the
grounding and not on the production of a more compact FDR representation (at
least for now).

*Note:* This is an ongoing work.

## Installation

We recommend using a Python virtual environment. Once inside the virtual
environment, you can run

```bash
$ python setup.py install
```

or

```bash
$ pip install -e .
```

while in the root directory of the repository.

## Usage

To run the program, execute

```bash
$ ./generate-asp-model.py -i /path/to/instance.pddl [-m MODEL-OUTPUT] [-t THEORY-OUTPUT]
```

where `/path/to/instance.pddl` is the path to a *PDDL instance* (not the domain
file!). It is necessary that there is a PDDL domain file in the same directory
as `instance.pddl`, though. The script will infer the domain file automatically.

The program will generate the Datalog encoding corresponding to the PDDL task
and ground it using gringo. The Datalog file will be saved in `MODEL-OUTPUT`
(default: `output.theory`); the canonical model (together with any other output
from the grounder) will be saved in `THEORY-OUTPUT` (default: `output.model`).

There are some extra options one can use:

- `--ground-actions`: Use the encoding from Helmert (AIJ 2009) where action
  predicates are listed explcitly.
- `--grounder`: Select grounder to be used to ground the Datalog
  program. Current options are `gringo` and `newground`. You must have either
  `gringo` or/and `newground` on the `PATH`. (Default: `gringo`)
- `--lpopt-preprocessor`: Uses the `lpopt` preprocessor to rewrite the Datalog
  program. This option expects an environment variable called `LPOPT_BIN_PATH`
  to point to the binary file of `lpopt`.
- `--fd-split`: Uses Fast Downward preprocessor to split rules of the Datalog
  program. This uses the method by Helmert (AIJ 2009).
- `--htd-split`: (This option is not fully functional yet.) Splits the rules
  based on the hypertree decompositions of the rule bodies. It expects
  `BalancedGo` to be on the `PATH`.

to install the necessary packages.


### Requirements

- Python3.7 or newer (if you do not want to use `newground` then Python 3.6
  should also work)
- You must have `gringo` and/or `newground` on the `PATH`.
- To use `lpopt`, you must also have an environment variable called
  `LPOPT_BIN_PATH` to point to the binary file of `lpopt`
