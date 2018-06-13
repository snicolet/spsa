# -*- coding: utf-8 -*-
"""
Function minimization using the SPSA algorithm.
Author: Stéphane Nicolet
"""

import random
import math
import array
import utils


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
            theta0 (dict) :
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
        self.iter = 0;
        self.max_iter = max_iter
        self.constraints = constraints
        self.options = options

        # some attributes to provide an history of evaluations
        self.previous_gradient    = {}
        self.rprop_previous_g     = {}
        self.rprop_previous_delta = {}

        self.history_eval = array.array('d', range(1000))
        self.history_theta = [theta0 for k in range(1000)]
        self.history_count = 0
        
        self.best_eval = array.array('d', range(1000))
        self.best_theta = [theta0 for k in range(1000)]
        self.best_count = 0

        # These constants are used throughout the SPSA algorithm

        self.a = options.get("a", 1.1)
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
            k = k + 1
            
            self.iter = k

            if self.constraints is not None:
               theta = self.constraints(theta)

            print("theta  = " + utils.pretty(theta))

            c_k = self.c / (k ** self.gamma)
            a_k = self.a / ((k + self.A) ** self.alpha)

            gradient = self.approximate_gradient(theta, c_k)

            #print(str(k) + " gradient = " + utils.pretty(gradient))
            # if k % 1000 == 0:
                # print(k + utils.pretty(theta) + "norm2(g) = " + str(utils.norm2(gradient)))
                # print(k + " theta = " + utils.pretty(theta))

            ## For SPSA we update with a small step (theta = theta - a_k * gradient)
            ## theta = utils.linear_combinaison(1.0, theta, -a_k, gradient)

            ## For steepest descent we update via a constant small step in the gradient direction
            mu = -0.05 / max(1.0, utils.norm2(gradient))
            theta = utils.linear_combinaison(1.0, theta, mu, gradient)

            ## For RPROP, we update with information about the sign of the gradients
            theta = utils.linear_combinaison(1.0, theta, -0.05, self.rprop(theta, gradient))

            ## We then move to the point which gives the best average of goal
            # (avg_goal , avg_theta) = self.average_best_evals(30)
            # theta = utils.linear_combinaison(0.8, theta, 0.2, avg_theta)

            if (k % 100 == 0) or (k <= 1000) :
                (avg_goal , avg_theta) = self.average_evaluations(30)
                print("iter = " + str(k))
                print("mean goal (all)   = " + str(avg_goal))
                print("mean theta (all)  = " + utils.pretty(avg_theta))

                (avg_goal , avg_theta) = self.average_best_evals(30)
                print("mean goal (best)  = " + str(avg_goal))
                print("mean theta (best) = " + utils.pretty(avg_theta))

            print("-----------------------------------------------------------------")

            if k >= self.max_iter:
                break

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

        self.history_eval [self.history_count % 1000] = v
        self.history_theta[self.history_count % 1000] = theta
        self.history_count += 1

        return v


    def approximate_gradient(self, theta, c):
        """
        Return an approximation of the gradient of f at point theta.

        On repeated calls, the esperance of the series of returned values
        converges almost surely to the true gradient of f at theta.
        """

        if self.history_count > 0:
            current_goal, _ = self.average_evaluations(30)
        else:
            current_goal = 100000000000000000.0

        bernouilli = self.create_bernouilli(theta)

        count = 0
        while True:
            # Calculate two evaluations of f at points M + c * bernouilli and
            # M - c * bernouilli to estimate the gradient. We do not want to
            # use a null gradient, so we loop until the two functions evaluations
            # are different. Another trick is that we use the same seed for the
            # random generator for the two function evaluations, to reduce the
            # variance of the gradient if the evaluations use simulations (like
            # in games).
            state = random.getstate()
            theta1 = utils.linear_combinaison(1.0, theta, c, bernouilli)
            f1 = self.evaluate_goal(theta1)

            random.setstate(state)
            theta2 = utils.linear_combinaison(1.0, theta, -c, bernouilli)
            f2 = self.evaluate_goal(theta2)

            if f1 != f2:
                break

            count = count + 1
            if count >= 100:
                # print("too many evaluation to find a gradient, function seems flat")
                break

        # Update the gradient
        gradient = {}
        for (name, value) in theta.items():
            gradient[name] = (f1 - f2) / (2.0 * c * bernouilli[name])

        if (f1 > current_goal) and (f2 > current_goal):
            print("function seems not decreasing")
            gradient = utils.linear_combinaison(0.1, gradient)

        # For the correction factor used in the running average for the gradient,
        # see the paper "Adam: A Method For Stochastic Optimization, Kingma and Lei Ba"

        beta = 0.9
        correction = 1.0 / 1.0 - pow(beta, self.iter)

        gradient = utils.linear_combinaison((1 - beta), gradient, beta, self.previous_gradient)
        gradient = utils.linear_combinaison(correction, gradient)

        # Store the current gradient for the next time, to calculate the running average
        self.previous_gradient = gradient
        
        
        # Store the best the two evals f1 and f2 (or both)
        if (f1 <= current_goal):
            self.best_eval [self.best_count % 1000] = f1
            self.best_theta[self.best_count % 1000] = theta1
            self.best_count += 1
        
        if (f2 <= current_goal):
            self.best_eval [self.best_count % 1000] = f2
            self.best_theta[self.best_count % 1000] = theta2
            self.best_count += 1
        
        # Return the estimation of the new gradient
        return gradient


    def create_bernouilli(self, m):
        """
        Create a random direction to estimate the stochastic gradient.
        We use a Bernouilli distribution : bernouilli = (+1,+1,-1,+1,-1,.....)
        """
        bernouilli = {}
        for (name, value) in m.items():
            bernouilli[name] = 1 if random.randint(0, 1) else -1


        g = utils.norm2(self.previous_gradient)
        d = utils.norm2(bernouilli)

        if g > 0.00001:
            bernouilli = utils.linear_combinaison(0.55        , bernouilli, \
                                                  0.25 * d / g, self.previous_gradient)
        
        for (name, value) in m.items():
            if bernouilli[name] == 0.0:
                bernouilli[name] = 0.2
            if abs(bernouilli[name]) < 0.2:
                bernouilli[name] = 0.2 * utils.sign_of(bernouilli[name])

        return bernouilli


    def average_evaluations(self, n):
        """
        Return the average of the n last evaluations of the goal function.

        This is a fast function which uses the last evaluations already
        done by the SPSA algorithm to return an approximation of the current
        goal value (note that we do not call the goal function another time,
        so the returned value is an upper bound of the true value).
        """

        assert(self.history_count > 0) , "not enough evaluations in average_evaluations!"

        if n <= 0                 : n = 1
        if n > 1000               : n = 1000
        if n > self.history_count : n = self.history_count

        sum_eval  = 0.0
        sum_theta = utils.linear_combinaison(0.0, self.theta0)
        for i in range(n):

            j = ((self.history_count - 1) % 1000) - i
            if j < 0     : j += 1000
            if j >= 1000 : j -= 1000

            sum_eval += self.history_eval[j]
            sum_theta = utils.sum(sum_theta, self.history_theta[j])

        # return the average
        alpha = 1.0 / (1.0 * n)
        return (alpha * sum_eval , utils.linear_combinaison(alpha, sum_theta))
    

    def average_best_evals(self, n):
        """
        Return the average of the n last best evaluations of the goal function.

        This is a fast function which uses the last evaluations already
        done by the SPSA algorithm to return an approximation of the current
        goal value (note that we do not call the goal function another time,
        so the returned value is an upper bound of the true value).
        """

        assert(self.best_count > 0) , "not enough evaluations in average_evaluations!"

        if n <= 0              : n = 1
        if n > 1000            : n = 1000
        if n > self.best_count : n = self.best_count

        sum_eval  = 0.0
        sum_theta = utils.linear_combinaison(0.0, self.theta0)
        for i in range(n):

            j = ((self.best_count - 1) % 1000) - i
            if j < 0     : j += 1000
            if j >= 1000 : j -= 1000

            sum_eval += self.best_eval[j]
            sum_theta = utils.sum(sum_theta, self.best_theta[j])

        # return the average
        alpha = 1.0 / (1.0 * n)
        return (alpha * sum_eval , utils.linear_combinaison(alpha, sum_theta))



    def rprop(self, theta, gradient):

        # get the previous g of the RPROP algorithm
        if self.rprop_previous_g != {}:
            previous_g = self.rprop_previous_g
        else:
            previous_g = gradient

        # get the previous delta of the RPROP algorithm
        if self.rprop_previous_delta != {}:
            delta = self.rprop_previous_delta
        else:
            delta = gradient
            delta = utils.copy_and_fill(delta, 0.5)


        p = utils.hadamard_product(previous_g, gradient)

        print("gradient = " + utils.pretty(gradient))
        print("old_g    = " + utils.pretty(previous_g))
        print("p        = " + utils.pretty(p))

        g = {}
        eta = {}
        for (name, value) in p.items():

            if p[name] > 0   : eta[name] = 1.1   ## building speed
            if p[name] < 0   : eta[name] = 0.5   ## we have passed a local minima: slow down
            if p[name] == 0  : eta[name] = 1.0

            delta[name] = eta[name] * delta[name]
            delta[name] = min(50.0, delta[name])
            delta[name] = max(0.000001, delta[name])

            g[name] = gradient[name]

        print("g        = " + utils.pretty(g))
        print("eta      = " + utils.pretty(eta))
        print("delta    = " + utils.pretty(delta))

        # store the current g and delta for the next call of the RPROP algorithm
        self.rprop_previous_g     = g
        self.rprop_previous_delta = delta

        # calculate the update for the current RPROP
        s = utils.hadamard_product(delta, utils.sign(g))

        print("sign(g)  = " + utils.pretty(utils.sign(g)))
        print("s        = " + utils.pretty(s))

        return s



###### Examples

if __name__ == "__main__":
    """
    Some tests functions for our minimizer, mostly from the following sources:
    https://en.wikipedia.org/wiki/Test_functions_for_optimization
    http://www.sfu.ca/~ssurjano/optimization.html
    """

    def f(x, y):
        return x * 100.0 + y * 3.0
    #print(SPSA_minimization(f, {"x" : 3.0, "y" : 2.0 } , 10000).run())



    def quadratic(x):
        return x * x + 4 * x + 3
    #print(SPSA_minimization(quadratic, {"x" : 10.0} , 1000).run())



    def g(**args):
        x = args["x"]
        return x * x
    print(SPSA_minimization(g, {"x" : 3.0} , 1000).run())



    def rastrigin(x, y):
        A = 10
        return 2 * A + (x * x - A * math.cos(2 * math.pi * x)) \
                     + (y * y - A * math.cos(2 * math.pi * y))
    #print(SPSA_minimization(rastrigin, {"x" : 5.0, "y" : 4.0 } , 1000).run())



    def rosenbrock(x, y):
        return 100.0*((y-x*x)**2) + (x-1.0)**2
    ##print(SPSA_minimization(rosenbrock, {"x" : 1.0, "y" : 1.0 } , 1000).run())




    def himmelblau(x, y):
        return (x*x + y - 11)**2 + (x + y*y - 7)**2
    theta0 = {"x" : 0.0, "y" : 0.0 }
    #m = SPSA_minimization(himmelblau, theta0, 10000)



    ##minimum = m.run()
    #print("minimum =", minimum)
    #print("goal at minimum =", m.evaluate_goal(minimum))




