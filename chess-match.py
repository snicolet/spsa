#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: chess-match.py LENGTH SEED [PARAM_NAME PARAM_VALUE]...

Organize a small chess match with SPSA3_PARAM(s), using cutechess-cli:

  LENGTH        Length of the match to be played
  SEED          Running number for the match to be played
  PARAM_NAME    Name of a parameter that's being optimized
  PARAM_VALUE   Integer value for parameter PARAM_NAME

SPSA3 is a black-box parameter tuning tool designed and written by S. Nicolet.
It is an implementation of the SPSA3 algorithm, with a focus on optimizing
parameters for game playing engines like Go, Chess, etc.

This script works between SPSA3 and cutechess-cli, a chess utility to organize
matches between chess engines. This Python script plays one MATCH between two
chess engines. One of the engines receives the list of arguments values given 
on the command line, and the other one being chosen by the script among a fixed
pool of oppenent(s) specified in the script.

In this script the following variables must be modified to fit the test
environment and conditions. The default values are just examples.
   'directory'
   'cutechess_cli_path'
   'engine'
   'engine_param_cmd'
   'opponents'
   'options'

When the match is completed the script writes the average score of the match
outcome to its standard output:
  0   = loss
  0.5 = draw
  1   = win
"""

from subprocess import Popen, PIPE
import sys
#import exceptions


# The directory where the two engine executables will be found
directory = '/Users/stephane/Programmation/fishtest-for-local-tests/worker/testing/'

# Path to the cutechess-cli executable.
# On Windows this should point to cutechess-cli.exe
cutechess_cli_path = directory + 'cutechess-cli'

# The engine whose parameters will be optimized
engine  = 'cmd=stockfish '
engine += 'proto=uci '
engine += 'option.Threads=1 '
engine += 'name=stockfish '

# Format for the commands that are sent to the engine to
# set the parameter values. When the command is sent,
# {name} will be replaced with the parameter name and {value}
# with the parameter value.
engine_param_cmd = 'setoption name {name} value {value}'

# A pool of opponents for the engine. The opponent will be chosen
# based on the seed sent by SPSA3. In Stockfish development we
# usually use only one opponent in the pool (the old master branch).
opponents = [ 'cmd=base proto=uci option.Threads=1 name=base' ]

# Additional cutechess-cli options, eg. time control and opening book.
# This is also were we set options used by both players.
options  = ' -tournament gauntlet -pgnout results.pgn '
options += ' -concurrency 3 '
options += ' -resign movecount=3 score=400 '
options += ' -draw movenumber=34 movecount=8 score=20 '
options += ' -each tc=10.0+0.05 option.Hash=128 '
options += ' -openings file=2moves_v1.pgn format=pgn order=random plies=4 '


def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0 or argv[0] == '--help':
        print(__doc__)
        return 0

    if len(argv) < 4 or len(argv) % 2 == 1:
        print('Too few arguments')
        return 2

    rounds = 0
    try:
        rounds = int(argv[0])
    except exceptions.ValueError:
        print('Invalid length of match: %s' % argv[0])
        return 2

    argv = argv[1:]
    spsa3_seed = 0
    try:
        spsa3_seed = int(argv[0])
    except exceptions.ValueError:
        print('Invalid seed value: %s' % argv[0])
        return 2

    fcp = engine
    scp = opponents[spsa3_seed % len(opponents)]

    # Parse the parameters that should be optimized
    for i in range(1, len(argv), 2):
        # Make sure the parameter value is numeric
        try:
            float(argv[i + 1])
        except exceptions.ValueError:
            print('Invalid value for parameter %s: %s' % (argv[i], argv[i + 1]))
            return 2
        # Pass SPSA3's parameters to the engine by using
        # cutechess-cli's initialization string feature
        initstr = engine_param_cmd.format(name = argv[i], value = argv[i + 1])
        fcp += ' initstr="%s" ' % initstr

    cutechess_args  = ' -repeat -rounds %s ' % rounds
    cutechess_args += ' -srand %d -engine %s -engine %s %s ' % (spsa3_seed, fcp, scp, options)
    command  = ' cd ' + directory + ' && '
    command += ' %s %s ' % (cutechess_cli_path, cutechess_args)
    
    # Debug the command
    print(command)

    # Run cutechess-cli and wait for it to finish
    process = Popen(command, shell = True, stdout = PIPE)
    output = process.communicate()[0]
    if process.returncode != 0:
        print('Could not execute command: %s' % command)
        return 2
    
    # Debug the cutechess-cli output
    print(output)

    # Convert cutechess-cli's output into a match score: 
    # we search for the last line containing a score of the match
    result = ""
    for line in output.splitlines():
        if line.startswith('Score of stockfish vs base'):
            result = line[line.find("[")+1 : line.find("]")]

    if result == "":
        print('The match did not terminate properly')
        return 2
    else:
        print(result)

if __name__ == "__main__":
    sys.exit(main())