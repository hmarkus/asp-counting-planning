#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import uuid

from subprocess import Popen, PIPE

from tarski.reachability import create_reachability_lp, run_clingo
from tarski.theories import Theory
from tarski.utils.command import silentremove, execute
from tarski.syntax.transform.universal_effect_elimination import expand_universal_effect, compile_universal_effects_away

from utils import *

if __name__ == '__main__':
    args = parse_arguments()

    domain_file = args.domain
    instance_file = args.instance
    if not os.path.isfile(domain_file):
        sys.stderr.write("Error: Domain file does not exist.\n")
        sys.exit()
    if not os.path.isfile(instance_file):
        sys.stderr.write("Error: Instance file does not exist.\n")
        sys.exit()

    theory_output = args.theory_output
    theory_output_with_actions = args.theory_output.replace(".theory", "-with-actions.theory")
    print("Saving extra copy of theory with actions to %s" % theory_output_with_actions)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if args.fd_split or args.htd_split:
        command = [dir_path+'/src/translate/pddl_to_prolog.py', domain_file, instance_file]
        if args.relevance_analysis:
            command.extend(['--relevance-analysis'])
        if args.htd_split:
            command.extend(['--htd', '--only-output-htd-program'])
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)
    else:
        command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
                 instance_file, '--only-output-direct-program']
        if args.relevance_analysis:
            command.extend(['--relevance-analysis'])
        if not args.ground_actions:
            command.extend(['--remove-action-predicates'])
        execute(command, stdout=theory_output)
        print("ASP model being copied to %s" % theory_output)

    # Produces extra theory file with actions
    command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
                 instance_file, '--only-output-direct-program']
    if args.inequality_rules:
        command.extend(['--inequality-rules'])
    execute(command, stdout=theory_output_with_actions)
    print("ASP model *with actions* being copied to %s" % theory_output_with_actions)


    if args.lpopt_preprocessor:
        lpopt = find_lpopt()
        temporary_filename = str(uuid.uuid4())
        command = [lpopt, "-f", theory_output]
        temp_file = open(temporary_filename, "w+t")
        execute(command, stdout=temporary_filename)
        os.rename(temporary_filename, theory_output)

    grounder = select_grounder(args.grounder)

    extra_options = []

    # It is unclear whether we can still support clingo, but I left this here
    # just in case we revert the change.
    if args.grounder == 'clingo':
        extra_options = ['-V2', '--quiet']
    elif args.grounder == 'gringo':
        extra_options=['--output', 'text']
    elif args.grounder == 'newground':
        extra_options=['--no-show', '--ground']
    elif args.grounder == 'idlv':
        print("Output below refers to Gringo for legacy reasons. The selected grounder is I-DLV.")
        extra_options=['--t']

    use_clingo = args.grounder == 'clingo'

    model_output = args.model_output
    with open(model_output, 'w+t') as output:
        start_time = time.time()
        command = [grounder, theory_output] + extra_options
        process = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True)
        grounder_output = process.communicate()[0]
        atoms = -2 # starts with -2 because gringo outputs an empty line + goal reachable
        if not args.suppress_output:
            for i in grounder_output.split('\n'):
                if not i.startswith("temp_decomp_") and not i.startswith("equals"):
                    atoms += 1
                    print(i, file=output)
        if atoms <= 0:
            print("Relaxed unsolvable task.")
            print ("Gringo finished correctly: 0")
            sys.exit(-1)
        if process.returncode == 0 or (use_clingo and process.returncode == 30):
            # For some reason, clingo returns 30 for correct exit
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % compute_time(start_time, use_clingo, args.model_output))
            print("Number of atoms (not actions):", len(grounder_output.split('\n')) - 1)
            print("Number of atoms discarding temporary ones:", atoms)
            if args.grounder == 'newground':
                with open(args.model_output, 'r') as model_file:
                    print(model_file.read())
        else:
            print ("Gringo finished correctly: 0")

    if args.remove_files:
        silentremove(args.model_output)
        silentremove(theory_output)
