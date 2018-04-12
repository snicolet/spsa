#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: match.py LENGTH SEED [PARAM_NAME PARAM_VALUE]...

Organize a small match betwwen two engines

  LENGTH        Length of the match to be played
  SEED          Random seed for the match to be played
  PARAM_NAME    Name of a parameter that's being optimized
  PARAM_VALUE   Value for parameter PARAM_NAME

This script organize a match of the given length between a reference
engine and the engine which parameters we want to optimize. It works
as a bridge between SPSA3 and another external script which must be able
to play ONE GAME between the two engines.

Note: SPSA3 is used as black-box parameter tuning tool, in an implementation  
written by S. Nicolet. This is the SPSA algorithm, with a focus on optimizing
parameters for game playing engines like Go, Chess, etc.

In this script the following variables must be modified to fit the test
environment and conditions. The default values are just examples.
   'directory'
   'engine'
   'engine_param_cmd'

When the match is completed the script writes the average score of the match
outcome to its standard output, which is a real number between 0.0 (the engine
lost all the games of the match, and 1.0 (the engine won all the games of the
match). For example in a match of six games, 2 wins, 1 draw and 3 losses gives
a match result of (2 + 0.5 + 0) / 6 = 0.417
"""

from subprocess import Popen, PIPE
import sys
import random


# The directory where the one-game script will be found
directory = './'

# Name of the one-game script to run
engine = 'python chess-game.py '

# Format for the commands that are sent to the engine to
# set the parameter values list. When the engine is run,
# {name} will be replaced with the parameter name and {value}
# with the parameter value.
engine_param_cmd = ' {name} {value} '


def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0 or argv[0] == '--help':
        print(__doc__)
        return 0

    if len(argv) < 4 or len(argv) % 2 == 1:
        print('Too few arguments, or odd number of aguments')
        return 2

    rounds = 0
    try:
        rounds = int(argv[0])
    except exceptions.ValueError:
        print('Invalid length of match: %s' % argv[0])
        return 2

    argv = argv[1:]
    seed = 0
    try:
        seed = int(argv[0])
        random.seed(seed)
    except exceptions.ValueError:
        print('Invalid seed value: %s' % argv[0])
        return 2

    # Parse the parameters that should be optimized
    params = ""
    for i in range(1, len(argv), 2):
        # Make sure the parameter value is numeric
        try:
            float(argv[i + 1])
        except exceptions.ValueError:
            print('Invalid value for parameter %s: %s' % (argv[i], argv[i + 1]))
            return 2
        params += engine_param_cmd.format(name = argv[i], value = argv[i + 1])
        

    # Run the engine in a sequential loop, wait for each game to finish
    # and accumulate the match score. Not that we change the random seed
    # for each separate game.
    count = 0.0
    score = 0.0
    for k in range(0, rounds):
        game_seed = random.randint(1, 100000000)
        
        command  = ' cd ' + directory + ' && '
        command += ' %s %s %s ' % (engine, game_seed, params)
        
        # Debug the command for the one-game script
        # print(command)
     
        # Run one game and wait for it to finish
        process = Popen(command, shell = True, stdout = PIPE)
        output = process.communicate()[0]
        if process.returncode != 0:
            print('Could not execute command: %s' % command)
            return 2
    
        # Debug the one-game script output
        # print(output)

        # Convert the one-game script output into a game score: 
        # we search for the last line containing a score of the game
        result = ""
        for line in output.splitlines():
            if len(line.strip()) != 0:
                result = line

        if result == "":
            print('The match did not terminate properly')
            return 2
        else:
            score += float(result)
            count += 1.0
        
    # Print the average match score on the standard output
    if (count >= 1):
        print(score / count)

if __name__ == "__main__":
    sys.exit(main())
    
    
    