import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_game(home, away):
    game_str = "./results/" + home + "v" + away + "stats.csv"
    return pd.read_csv(game_str, header=[0,1], index_col=0)

def plot_stat_hist(game_data, stat, player):
    player_stats = game_data[stat][player]
    plt.hist(player_stats, bins=20, density=True)
    plt.axvline(np.mean(player_stats),color="r", label="Average: {:.0f}".format(np.mean(player_stats)))
    plt.title("{} : {}".format(player, stat))
    plt.ylabel("Probability Density")
    plt.xlabel(stat)
    plt.legend()
    plt.show()


game_data = load_game("PHI", "DAL")
plot_stat_hist(game_data, "pass_yards", "Jalen Hurts")