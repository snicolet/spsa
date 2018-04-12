#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: chess-game.py SEED [PARAM_NAME PARAM_VALUE]...

Play one game of chess with SPSA3_PARAM(s), using cutechess-cli :

  SEED          Random seed for the game to be played
  PARAM_NAME    Name of a parameter that's being optimized
  PARAM_VALUE   Integer value for parameter PARAM_NAME

SPSA3 is a black-box parameter tuning tool designed and written by S. Nicolet.
It is an implementation of the SPSA3 algorithm, with a focus on optimizing
parameters for game playing engines like Go, Chess, etc.

This script works between SPSA3 and cutechess-cli, a chess utility to organize
matches between chess engines. This Python script plays ONE GAME between two
chess engines. One of the engines receives the list of arguments values given 
on the command line, and the other one being chosen by the script among a fixed
pool of oppenent(s) specified in the script.

The path to this script, without any parameters, should be on the "Script" line
of the .spsa3 file. 'Replications' in the .spsa3 file should be set to 2 so that
this script can alternate the engine's playing side correctly. The interface of
this script is meant to be very similar to the interface used by the tool CLOP
by Remi Coulomb.

In this script the following variables must be modified to fit the test
environment and conditions. The default values are just examples.
   'directory'
   'cutechess_cli_path'
   'engine'
   'engine_param_cmd'
   'opponents'
   'options'

When the game is completed the script writes the game outcome to its
standard output:
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
engine  = ' cmd=' + directory + 'stockfish '
engine += ' proto=uci '
engine += ' option.Threads=1 '
engine += ' name=stockfish '

# Format for the commands that are sent to the engine to
# set the parameter values. When the command is sent,
# {name} will be replaced with the parameter name and {value}
# with the parameter value.
engine_param_cmd = ' setoption name {name} value {value} '

# A pool of opponents for the engine. The opponent will be chosen
# based on the seed sent by SPSA3. In Stockfish development we
# usually use only one opponent in the pool (the old master branch).
opponents = [ ' cmd=' + directory + 'base proto=uci option.Threads=1 name=base ' ]

# Additional cutechess-cli options, eg. time control and opening book.
# They will be used by both players.
options  = ' -resign movecount=3 score=400 '
options += ' -draw movenumber=34 movecount=8 score=20 '
options += ' -each tc=10.0+0.05 '
options += ' -openings file=2moves_v1.pgn format=pgn order=random plies=4 '


def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0 or argv[0] == '--help':
        print(__doc__)
        return 0

    if len(argv) < 3 or len(argv) % 2 == 0:
        print('Too few arguments, or even number of arguments')
        return 2

    seed = 0
    try:
        seed = int(argv[0])
    except exceptions.ValueError:
        print('Invalid seed value: %s' % argv[0])
        return 2

    fcp = engine
    scp = opponents[(seed >> 1) % len(opponents)]

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

    # Choose the engine's playing side (color) based on SPSA's seed
    if seed % 2 != 0:
        fcp, scp = scp, fcp

    cutechess_args = ' -srand %d -engine %s -engine %s %s ' % (seed >> 1, fcp, scp, options)
    command  = ' cd ' + directory + ' && '
    command += ' %s %s ' % (cutechess_cli_path, cutechess_args)
    
    # Debug the command
    # print(command)

    # Run cutechess-cli and wait for it to finish
    process = Popen(command, shell = True, stdout = PIPE)
    output = process.communicate()[0]
    if process.returncode != 0:
        print('Could not execute command: %s' % command)
        return 2

    # Convert cutechess-cli's result into W/L/D
    # Note that only one game should be played
    result = -1
    for line in output.splitlines():
        if line.startswith('Finished game'):
            if line.find(": 1-0") != -1:
                result = seed % 2
            elif line.find(": 0-1") != -1:
                result = (seed % 2) ^ 1
            elif line.find(": 1/2-1/2") != -1:
                result = 2
            else:
                print('The game did not terminate properly')
                return 2
            break

    if result == 0:
        print('1')      # Win
    elif result == 1:
        print('0')      # Loss
    elif result == 2:
        print('0.5')    # Draw

if __name__ == "__main__":
    sys.exit(main())