import json
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st
import pandas as pd

player_id = "00-0039040"

pass_data = pd.read_csv("./data/pass_data.csv")
catch_yards = pass_data[pass_data["complete_pass"] == 1]
yard_data = catch_yards[catch_yards["receiver_player_id"] == player_id]["yards_after_catch"]

param_dict = json.load(open("./data/params.json", "r"))

player_params = param_dict["yards_after_catch"][player_id]
dist = getattr(st, "invgauss")

params = dist.fit(yard_data)

player_dist = dist(*params)
print(np.mean(np.clip(player_dist.rvs(10000),-10,100)))
x = np.linspace(-5,100,1000)
plt.plot(x, player_dist.pdf(x))
plt.hist(yard_data, density=True)
plt.show()