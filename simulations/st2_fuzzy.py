### Implementation of LUCB scheme for all epsilon good arms

import numpy as np 
from utils import *

class st2(all_eps_bandit):
    def __init__(self, epsilon, means, noise_var, delta, gamma=0, gamma2=1e-1,
                                                            burn_amt=1,
                                                            maxpulls=1e5,
                                                            printeach=5000,
                                                            verbose=True):
        super().__init__(epsilon, means, noise_var, delta)
        self.maxpulls = maxpulls
        self.burn_amt = burn_amt
        self.emp_good = []
        self.emp_bad = []
        self.return_set = []
        self.unknown_arms = list(range(self.narms))
        self.f_scores, self.emp_correct = [], []
        self.precision_vals, self.recall_vals = [], []
        # divide by two so gamma = bound width not half width
        self.gamma = gamma
        self.argmax_ucb = 0         # arm with highest UCB
        self.argmin_good = 0        # emp good arm with lowest LCB
        self.argmax_bad = 0         # emp bad arm with highest UCB
        self.printeach = printeach
        self.recordeach = 10000
        self.verbose = verbose
        self.gamma2 = gamma2
        self.did_update_thresh = False
        self.d = 0
        self.ratio = 0

    def arms_to_pull(self):
        ''' Computes shich are the three arms to pull per round.
            NOTE: good and bad sets must be fresh (call compute_sets).
        '''
        # set flags so we don't pull
        self.argmax_ucb, self.argmin_good, self.argmax_bad = -1, -1, -1
        # arm with highest upper bound
        self.argmax_ucb = np.argmax(self.ubs)
        # Empirically good arm with lowest lcb
        if len(self.emp_good):
            good_idx = np.argmin(self.lbs[self.emp_good])
            self.argmin_good = self.emp_good[good_idx]
        # Empirically bad arm with highest ucb if exists
        if len(self.emp_bad):
            bad_idx = np.argmax(self.ubs[self.emp_bad])
            self.argmax_bad = self.emp_bad[bad_idx]

    def is_known(self, i):
        '''Is arm i certified good or bad wrt thresh_ub or thresh_lb'''
        return self.lbs[i] > self.thresh_ub or self.ubs[i] < self.thresh_lb

    def all_semi_known(self, li):
        bounds = [self.ubs[i] - self.emps[i] for i in li]
        return np.sum(bounds) < min(self.gamma2, self.d/4)
        # return all([self.is_semi_known(i) for i in li])

    def compute_thresh(self):
        '''Computes bounds on threshold'''
        self.thresh_emp = max(self.emps) - self.epsilon
        self.thresh_ub = max(self.ubs) - self.epsilon - self.gamma
        self.thresh_lb = max(self.lbs) - self.epsilon

    def compute_sets(self):
        '''Compute sets of empirically good and bad arms.'''
        # self.unknown_arms = [i for i in range(self.narms)
        #                         if not self.is_known(i)]
        # # unknown empirically good arms with width > gamma
        # self.emp_good = [i for i in self.unknown_arms
        #                         if self.emps[i] >= self.thresh_emp]
        # # unknown empirically bad arms with width > gamma
        # self.emp_bad = [i for i in self.unknown_arms
        #                         if self.emps[i] < self.thresh_emp]

        # vectorized code
        # self.unknown_arms = list(filter(lambda x: not self.is_known(x), np.arange(self.narms)))
        # self.semi_known_arms = list(filter(lambda x: self.is_semi_known(x), np.arange(self.narms)))

        self.unknown_arms = [i for i in range(self.narms) if not self.is_known(i)]
        self.emp_good = np.flatnonzero(self.emps >= self.thresh_emp)
        self.emp_bad = np.flatnonzero(self.emps < self.thresh_emp)

    def compute_return_set(self):
        # All arms I cannot certify are below threshold
        self.return_set = {i for i in range(self.narms)
                            if self.ubs[i] >= self.thresh_lb}

    def compute_err(self):
        '''Compute error on empirically good set'''
        compare = self.eps_good_arms
        self.compute_return_set()
        s = self.return_set
        self.f_scores.append(self.f_score(s, compare=compare))
        self.recall_vals.append(self.recall(s, compare=compare))
        self.precision_vals.append(self.precision(s, compare=compare))
        self.emp_correct.append(s == compare)

    def stopping_condition(self):
        '''Stop when lowest good lb above theshold UB and
            highest bad ub below threshold LB or hit maxpulls.
        '''
        if self.total_pulls >= self.maxpulls: return True
        if not len(self.unknown_arms): return True  
        return False
        
    def printout(self):
        if self.verbose:
            len_return_set = sum(self.ubs > self.thresh_lb)
            ngood = len(self.eps_good_arms)
            print('Pulls: {}, f score: {:.4f}, return set: {}/{}'\
                .format(self.total_pulls, self.f_scores[-1],
                            len_return_set, ngood))

    def round_setup(self):
        '''Initialize arms, sets and err before round'''
        # copies = self.pulls_per_round() # num of copies based on prev
        self.compute_thresh()                # compute current threshold 
        self.compute_sets()                  # compute good and bad sets
        self.arms_to_pull()
        self.d = self.emps[self.argmin_good] - self.emps[self.argmax_bad]

        # update epsilon
        if self.all_semi_known([self.argmax_ucb, self.argmin_good, self.argmax_bad]) and not self.did_update_thresh:
        # if len(self.semi_known_arms) == self.narms and not self.did_update_thresh and (self.ubs[self.argmax_ucb] - self.emps[self.argmax_ucb] < self.gamma2):
            display_bounds(self, "st2_fuzzy_pre")
            old_eps = self.epsilon
            # self.epsilon = max(self.epsilon - self.gamma2, self.emps[self.argmax_ucb] - np.average([self.emps[self.argmin_good],  self.emps[self.argmax_bad]]))
            self.epsilon = self.emps[self.argmax_ucb] - np.average([self.emps[self.argmin_good],  self.emps[self.argmax_bad]])
            print(f"updating epsilon from {old_eps} to {self.epsilon}")
            self.did_update_thresh = True
            display_bounds(self, "st2_fuzzy_post")

            self.compute_sets()
            self.compute_thresh()
            self.arms_to_pull()

            # find put which arm to pull
        # self.compute_err(copies=copies)      # compute current error

    def pull_round(self):
        '''Pull three specified arms'''
        if self.argmax_ucb != -1: self.pull(self.argmax_ucb)
        if self.argmin_good != -1: self.pull(self.argmin_good)
        if self.argmax_bad != -1: self.pull(self.argmax_bad)  

    def run(self):
        '''Function to run LUCB all epsilon'''
        self.burn_in(amount=self.burn_amt)
        self.round_setup()
        self.compute_err()
        while not self.stopping_condition():
            self.pull_round()   # pull current arms
            self.round_setup()  # result
            if self.total_pulls % self.printeach < 3: self.printout()
            if self.total_pulls % self.recordeach: self.compute_err()
        self.printout()
        self.compute_return_set()


def small_alpha_example():
    means = np.ones(100)
    means[-1:] = 0.18
    means[-2] = 0.4
    epsilon = 0.65
    noise_var = 1
    delta = 0.01
    gamma=0
    maxpulls=1e9
    instance = st2(epsilon, means, noise_var, delta, gamma=gamma,
                   maxpulls=maxpulls)
    instance.run()
    display_bounds(instance, "st2_gamma")

def small_beta_example():
    means = np.ones(100)
    means[-1:] = 0.18
    means[-2] = 0.4
    epsilon = 0.8
    noise_var = 1
    delta = 0.01
    gamma=0
    maxpulls=1e9
    instance = st2(epsilon, means, noise_var, delta, gamma=gamma,
                   maxpulls=maxpulls)
    instance.run()
    display_bounds(instance, "st2_gamma")

if __name__ == '__main__':
    small_alpha_example()
    small_beta_example()

