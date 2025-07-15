import json
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st

param_dict = json.load(open("./data/params.json", "r"))
player_id = "00-0036389"

player_params = param_dict["yards_gained"][player_id]
dist = getattr(st, "genextreme")

player_dist = dist(*player_params)
x = np.linspace(-5,100,1000)
plt.plot(x, player_dist.pdf(x))
plt.show()