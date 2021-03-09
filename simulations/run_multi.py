import numpy as np
import st2_gamma
import st2_fuzzy
from fareast import fareast
import matplotlib.pyplot as plt

pulls=[[],[],[]]
for l in range(5, 50, 10):
    # means = np.arange(0, 100, 100 / l) / 100
    means = np.arange(0, l*2, 5) / 100
    epsilon = 0.37
    # means = np.ones(l)
    # means[-1] = 0.18
    # epsilon = 0.8
    delta = 0.01
    noise_var = 1
    maxpulls = 1e9
    gamma=0

    instance = st2_gamma.st2(epsilon, means, noise_var, delta, gamma=gamma,
                   maxpulls=maxpulls)
    instance.run()
    pulls[0].append(instance.total_pulls)

    instance = st2_fuzzy.st2(epsilon, means, noise_var, delta, gamma=gamma,
                             maxpulls=maxpulls)
    instance.run()
    pulls[1].append(instance.total_pulls)

    instance = fareast(epsilon, means, noise_var, delta, gamma=gamma, kappa=0.5)
    instance.run()
    pulls[2].append(instance.total_pulls)

    # print(pulls)

plt.plot(range(5, 50, 10), pulls[0], label="st2")
plt.plot(range(5, 50, 10), pulls[1], label="fuzzy_st2")
plt.plot(range(5, 50, 10), pulls[2], label="fareast")
plt.legend()
plt.title("Complexity as a function of the number of arms")
plt.xlabel("Number of Arms")
plt.ylabel("Iterations")
plt.show()