# Optimizer for games

Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

Usage : *python game-optimizer.py [PARAM_NAME PARAM_VALUE]...*

The parameter list can also we provided as a string in the Python code,
see the function set_parameters_from_string() in the example section.

### List of files in the directory ###

- *game_optimizer.py* : the main file of the package
- *spsa.py* : a general-purpose minimization algorithm (an improved version of the SPSA algorithm)
- *utils.py* : small utility functions
- *match.py* : a script to organize a match between two playing engines in any game (Go, Chess, etc..)
- *chess-game.py* : organize one game of Chess between two engines. Can be plugged into *match.py*
- *chess-match.py* : a specialized Chess version of *match.py*, more efficient because it uses parallelism for the match
