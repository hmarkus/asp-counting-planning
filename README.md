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

To run the program generate-asp-model, execute

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


To run the count-ground-actions program for upper-bounding the number of action atoms
in the grounding and for computing alternative groundings, execute

```bash
$ ./ count-ground-actions.py -m MODEL-OUTPUT -t THEORY-OUTPUT-with-ground-actions
```

where `MODEL-OUTPUT` is the path to the MODEL-OUTPUT obtained with a call to the 
program above and `THEORY-OUTPUT-with-ground-actions` is the path to the THEORY-OUTPUT 
obtained by the same call, but additionally containing the argument `--ground-actions`. 

The program will count the number of expected action instantiations in a grounding
for each action individually. Also, the program is capable of outputting alternative
encodings for grounding (see options `--output` and `--extendedOutput`).

There are some extra options that one can optionally turn on:

- `--choices`: Use ASP choice rules, which is an alternative encoding that
  directly uses ASP choices, instead of SAT-like rules for guessing / deciding 
  whether an action is contained in the grounding.   
- `--output`: Compute the alternative grounding encoding and write it to stdout.
- `--extendedOutput`: Compute an alternative (extended) grounding encoding and 
  write it to stdout.
- `--counter-path`: Set the used counting solver environment variable,
  giving the execution path within the path specified by the environment variable `LPCNT_AUX_PATH`.
   This option expects an environment variable called `LPCNT_AUX_PATH` and
  that the path `LPCNT_AUX_PATH` contains the file given by the value of the passed environment variable. (default: `LPCNT_BIN_PATH`)


### Requirements for Counting

- Python3.7 or newer
- You must have `gringo` on the `PATH`.
- Add environment variable `LPCNT_AUX_PATH` pointing to
  `/path/to/repo/build/bdist.linux-x86_64`
- Add environment variable `GRINGO_BIN_PATH` pointing to the desired gringo
  installation
- Add environment variable `LPCNT_BIN_PATH` pointing to the desired counting 
  solving script. 
