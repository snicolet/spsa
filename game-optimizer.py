# -*- coding: utf-8 -*-
"""
Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

Usage : python game-optimizer.py [PARAM_NAME PARAM_VALUE]...

The parameter list can also we provided as a string in the Python code,
see the function set_parameters_from_string() in the example section.

"""

from subprocess import Popen, PIPE
import random
import math
import array
import sys
import spsa
import utils


class game_optimizer:

    def __init__(self):
        """
        The constructor of a game_optimizer object.
        """

        # Store the arguments
        self.ENGINE_COMMAND  = ""   # name of the script used to make a match against the reference engine
        self.THETA_0         = {}   # the initial set of parameter
        self.MINI_MATCH      = 6    # size of the minimatches used to estimate the gradient


    def set_engine_command(self, command):
        """
        Set the name of the command used to run a minimatch against the
        reference engine. The command is a shell script which will receive
        the list of parameters on the standard output, and ruturn the score
        of the match, with the convention that higher scores will be a good
        thing for the optimized engine.
        """

        # Store the command name
        self.ENGINE_COMMAND = command


    def launch_engine(self, theta):
        """
        Launch the match of the engine with parameters theta
        """

        # Each match will be started with a different seed, passed as a command line parameter
        seed = random.randint(1, 100000000)  # a random seed

        # Debug the seed
        # print("seed = " + str(seed))

        # Create the command line and the list of parameters
        command = self.ENGINE_COMMAND + " "
        args = " " + str(self.MINI_MATCH) + " " + str(seed) + " "
        for (name, value) in theta.items():
            args +=  " " + name + " " + str(value) + " "

        # Debug the command
        # print("command + args = " + command + args)

        # We use a subprocess to launch the match
        process = Popen(command + args, shell = True, stdout = PIPE)
        output = process.communicate()[0]

        if process.returncode != 0:
            print('ERROR in launch_engine: could not execute command: %s' % (command + args))
            return -10000

        # the score of the match
        return float(output)


    def goal_function(self, **args):
        """
        This is the function that the class exports, and that can be plugged
        into the generic SPSA minimizer.

        Mainly we launch the engine match, take the opposite of the score (because
        we want to *maximize* the score but SPSA is a minimizer). Note that we add
        a regulization term, which helps the convexity of the problem.
        """

        # Create the parameter vector
        theta = {}
        for (name, value) in self.THETA_0.items():
            v = args[name]
            theta[name] = v

        # Calculate the regularization term
        regularization = utils.regulizer(utils.difference(theta, self.THETA_0), 0.01, 0.5)

        # Calculate the score of the minimatch
        score = self.launch_engine(theta)

        result = -score + regularization

        print("**args = " + utils.pretty(args))
        print("goal   = " + str(-result))

        return result


    def set_parameters_from_string(self, s):
        """
        This is the function to transform the list of parameters, given as a string,
        into a vector for internal usage by the class.

        Example: "QueenValue 10.0  RookValue 6.0 "
                       would be transformed into the following python vector:
                 {'QueenValue': 10.0, 'RookValue': 6.0}
                       this vector will be used as the starting point for the optimizer
        """

        # Parse the string
        s = ' '.join(s.split())
        list = s.split(' ')
        n = len(list)

        # Create the initial vector, and store it in THETA_0
        self.THETA_0 = {}
        for k in range(0 , n // 2):
            name  = list[ 2*k ]
            value = float(list[ 2*k + 1])
            self.THETA_0[name] = value

        # The function also prints and returns THETA_0
        print("read_parameters :  THETA_0 = " + utils.pretty(self.THETA_0))
        return self.THETA_0



###### Example

if __name__ == "__main__":

    # Create the optimization object
    optimizer  = game_optimizer()

    # Set the name of the script to run matches
    optimizer.set_engine_command("python chess-match.py")
    #optimizer.set_engine_command("python match.py")

    # Use this to get the initial parameters from a string
    parameters = "A 0.32  B 1.28"

    # Use this to get the initial parameters from the command line
    # parameters = ' '.join(sys.argv[1:])

    print("parameters = " + parameters)
    theta0 = optimizer.set_parameters_from_string(parameters)

    # Create the SPSA minimizer with 10000 iterations...
    minimizer  = spsa.SPSA_minimization(optimizer.goal_function, theta0, 10000)

    # Run it!
    minimum = minimizer.run()
    print("minimum = ", minimum)



