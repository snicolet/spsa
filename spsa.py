# -*- coding: utf-8 -*-
"""
Function minimization using the SPSA algorithm.
Author: Stéphane Nicolet
"""

import random
import math
import array


class SPSA_minimization:

    def __init__(self, f, theta0, max_iter, constraints = None, options = {}):
        """
        The constructor of a SPSA_minimization object.

        We use the notations and ideas of the following articles:

          • Spall JC (1998), Implementation of the Simultuaneous Perturbation
            Algorithm for Stochastic Optimization, IEEE Trans Aerosp Electron
            Syst 34(3):817–823
          • Kocsis & Szepesvari (2006), Universal Parameter Optimisation in
            Games based on SPSA, Mach Learn 63:249–286

        Args:
            f (function) :
                The function to minimize.
            theta0 (dict):
                The starting point of the minimization.
            max_iter (int) :
                The number of iterations of the algorithm.
            constraints (function, optional) :
                A function which maps the current point to the closest point
                of the search domain.
            options (dict, optional) :
                Optional settings of the SPSA algorithm parameters. Default
                values taken from the reference articles are used if not
                present in options.
        """

        # Store the arguments
        self.f = f
        self.theta0 = theta0
        self.max_iter = max_iter
        self.constraints = constraints
        self.options = options

        # some attributes to provide an history of evaluations
        self.previous_gradient = {}
        self.history = array.array('d', range(1000))
        self.history_count = 0

        # These constants are used throughout the SPSA algorithm

        self.a = options.get("a", 0.5)
        self.c = options.get("c", 0.1)

        self.alpha = options.get("alpha", 0.70) # theoretical alpha=0.601, must be <= 1
        self.gamma = options.get("gamma", 0.12) # theoretical gamma=0.101, must be <= 1/6

        self.A = options.get("A", max_iter / 10.0)


    def run(self):
        """
        Return a point which is (hopefully) a minimizer of the goal
        function f, starting from point theta0.

        Returns:
            The point (as a dict) which is (hopefully) a minimizer of "f".
        """

        k = 0
        theta = self.theta0

        while True:

            if self.constraints is not None:
               theta = self.constraints(theta)

            c_k = self.c / ((k + 1) ** self.gamma)
            a_k = self.a / ((k + 1 + self.A) ** self.alpha)

            gradient = self.approximate_gradient(theta, c_k)

            #print(k, " gradient =", gradient)
            # if k % 1000 == 0:
                # print(k, theta, "norm(g) =", norm(gradient))
                # print(k, " theta =", theta)

            theta = linear_combinaison(1.0, theta, -a_k, gradient)

            k = k + 1
            if k >= self.max_iter:
                break

            if (k % 100 == 0) or (k < 10) :
                print("iter =", k, " goal =", self.average_evaluations(30))

        return theta


    def evaluate_goal(self, theta):
        """
        Return the evaluation of the goal function f at point theta.

        We also store an history the 1000 last evaluations, so as to be able
        to quickly calculate an average of these last evaluations of the goal
        via the helper average_evaluations() : this is handy to monitor the
        progress of our minimization algorithm.
        """

        v = self.f(**theta)

        # store the value in history

        self.history[self.history_count % 1000] = v
        self.history_count += 1

        return v


    def approximate_gradient(self, theta, c):
        """
        Return an approximation of the gradient of f at point theta.

        On repeated calls, the esperance of the series of returned values
        converges almost surely to the true gradient of f at theta.
        """

        delta = self.create_delta(theta)

        count = 0
        while True:
            # Calculate two evaluations of f at points M + c * delta and
            # M - c * delta to estimate the gradient. We do not want to
            # use a null gradient, so we loop until the two functions
            # evaluations are different. Another trick is that we use
            # the same seed for the random generator for the two function
            # evaluations, to reduce the variance of the gradient if the
            # evaluations use simulations (like in games).
            state = random.getstate()
            f1 = self.evaluate_goal(linear_combinaison(1.0, theta, c, delta))

            random.setstate(state)
            f2 = self.evaluate_goal(linear_combinaison(1.0, theta, -c, delta))

            if f1 != f2:
                break

            count = count + 1
            if count >= 100:
                # print("too many evaluation to find a gradient, function seems flat")
                break

        gradient = {}
        for (name, value) in theta.items():
            gradient[name] = (f1 - f2) / (2.0 * c * delta[name])

        if self.previous_gradient != {}:
            gradient = linear_combinaison(0.1, gradient, 0.9, self.previous_gradient)

        self.previous_gradient = gradient

        return gradient


    def create_delta(self, m):
        """
        Create a random direction to estimate the stochastic gradient.
        We use a Bernouilli distribution : delta = (+1,+1,-1,+1,-1,.....)
        """
        delta = {}
        for (name, value) in m.items():
            delta[name] = 1 if random.randint(0, 1) else -1


        g = norm(self.previous_gradient)
        d = norm(delta)

        if g > 0.00001:
            delta = linear_combinaison(0.55        , delta, \
                                       0.25 * d / g, self.previous_gradient)

        return delta


    def average_evaluations(self, n):
        """
        Return the average of the n last evaluations of the goal function.

        This is a fast function which uses the last evaluations already
        done by the SPSA algorithm to return an approximation of the current
        goal value (note that we do not call the goal function another time,
        so the returned value is an upper bound of the true value).
        """

        assert(self.history_count > 0),"not enough evaluations in average_evaluations!"

        if n <= 0                 : n = 1
        if n > 1000               : n = 1000
        if n > self.history_count : n = self.history_count

        s = 0.0
        for i in range(n):

            j = ((self.history_count - 1) % 1000) - i
            if j < 0 : j += 1000

            s += self.history[j]

        # return the average
        return s / (1.0 * n)


### Helper functions


def norm(m):
    """
    Return the norm of the point m
    """
    s = 0.0
    for (name, value) in m.items():
        s += value ** 2
    return math.sqrt(s)


def linear_combinaison(alpha = 1.0, m1 = {},
                       beta = None, m2 = {}):
    """
    Return the linear combinaison m = alpha * m1 + beta * m2.
    """
    if m2 == {}:
        m2 = m1
        beta = 0.0

    m = {}
    for (name, value) in m1.items():
        m[name] = alpha * value + beta * m2.get(name, 0.0)

    return m


###### Examples

if __name__ == "__main__":
    """
    Some tests functions for our minimizer, mostly from the following sources:
    https://en.wikipedia.org/wiki/Test_functions_for_optimization
    http://www.sfu.ca/~ssurjano/optimization.html
    """

    def f(x, y):
        return x * 100.0 + y * 3.0
    print(SPSA_minimization(f, {"x" : 3.0, "y" : 2.0 } , 10000).run())



    def quadratic(x):
        return x * x + 4 * x + 3
    print(SPSA_minimization(quadratic, {"x" : 10.0} , 1000).run())



    def g(**args):
        x = args["x"]
        return x * x
    print(SPSA_minimization(g, {"x" : 3.0} , 1000).run())



    def rastrigin(x, y):
        A = 10
        return 2 * A + (x*x - A * math.cos(2*math.pi*x)) \
                     + (y*y - A * math.cos(2*math.pi*y))
    print(SPSA_minimization(rastrigin, {"x" : 5.0, "y" : 20.0 } , 1000).run())



    def rosenbrock(x, y):
        return 100.0*((y-x*x)**2) + (x-1.0)**2
    print(SPSA_minimization(rosenbrock, {"x" : 1.0, "y" : 1.0 } , 1000).run())




    def himmelblau(x, y):
        return (x*x + y - 11)**2 + (x + y*y - 7)**2
    theta0 = {"x" : 0.0, "y" : 0.0 }
    m = SPSA_minimization(himmelblau, theta0, 10000)



    minimum = m.run()
    print("minimum =", minimum)
    print("goal at minimum =", m.evaluate_goal(minimum))




