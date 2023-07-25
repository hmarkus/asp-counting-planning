#!/usr/bin/env python


import argparse
import os
import shutil
import sys
import subprocess
import tempfile
import time
import uuid

from tarski.utils.command import silentremove, execute

from subprocess import Popen, PIPE

from utils import *

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate models.')
    parser.add_argument('-i', '--instance', required=True, help="The path to the problem instance file.")
    parser.add_argument('--domain', default=None, help="(Optional) The path to the problem domain file. If none is "
                                                       "provided, the system will try to automatically deduce "
                                                       "it from the instance filename.")
    parser.add_argument('--lpopt-preprocessor', action='store_true', help="Use lpopt to preprocess rules.")

    args = parser.parse_args()
    if args.domain is None:
        args.domain = find_domain_filename(args.instance)
        if args.domain is None:
            raise RuntimeError(f'Could not find domain filename that matches instance file "{args.domain}"')

    return args


if __name__ == '__main__':

    args = parse_arguments()

    domain_file = args.domain
    instance_file = args.instance

    dir_path = os.path.dirname(os.path.realpath(__file__))
    theory_output = "relevance-analysis.theory"
    original_model = "output.model"
    model_output = "output-relevant.model"
    command=[dir_path+'/src/translate/pddl_to_prolog.py', domain_file,
             instance_file,
             '--relevance-analysis', '--remove-action-predicates']
    execute(command, stdout=theory_output)
    print("ASP model being copied to %s" % theory_output)


    if args.lpopt_preprocessor:
        lpopt = find_lpopt()
        temporary_filename = str(uuid.uuid4())
        command = [lpopt, "-f", theory_output]
        temp_file = open(temporary_filename, "w+t")
        execute(command, stdout=temporary_filename)
        os.rename(temporary_filename, theory_output)


    # Fix gringo for now. IDLV might be better if tuned properly.
    grounder = select_grounder('gringo')
    extra_options=['--output', 'text']



    with open(model_output, 'w+t') as output:
        start_time = time.time()
        command = [grounder, original_model, theory_output] + extra_options
        process = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True)
        grounder_output = process.communicate()[0]
        relevant_model = 0
        for i in grounder_output.split('\n'):
            if 'relevant_' in i:
                relevant_model += 1
                proper_name = i.replace("relevant_", "")
                print(proper_name, file=output)
        if process.returncode == 0:
            # For some reason, clingo returns 30 for correct exit
            print ("Gringo finished correctly: 1")
            print("Total time (in seconds): %0.5fs" % compute_time(start_time, False, model_output))
            print("Number of relevant atoms:", relevant_model)
        else:
            print ("Gringo finished correctly: 0")
