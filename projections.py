from monte_carlo import Monte_Carlo_Sim
import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm
from multiprocessing import freeze_support
import json

# Create season matchups as dictionary
# keys = weeks, values = list of (home, away) tuples
# Potentially more efficient way, look at how nflverse does theirs
season = {1:[("PHI","DAL"),("LAC","KC"),("ATL","TB"),("CLE","CIN"),("IND","MIA"),
             ("NE","LV"),("NO","ARI"),("NYJ","PIT"),("WAS","NYG"),("JAX","CAR"),
             ("DEN","TEN"),("SEA","SF"),("GB","DET"),("LAR","HOU"),("BUF","BAL"),
             ("CHI","MIN")],
          2:[("GB","WAS"),("CIN","JAX"),("DAL","NYG"),("DET","CHI"),("TEN","LAR"),
             ("MIA","NE"),("NO","SF"),("NYJ","BUF"),("PIT","SEA"),("BAL","CLE"),
             ("IND","DEN"),("ARI","CAR"),("KC","PHI"),("MIN","ATL"),("HOU","TB"),
             ("LV","LAC")],
          3:[("BUF","MIA"),("CLE","GB"),("TEN","IND"),("MIN","CIN"),("NE","PIT"),
             ("PHI","LAR"),("TB","NYJ"),("WAS","LV"),("CAR","ATL"),("JAX","HOU"),
             ("LAC","DEN"),("SEA","NO"),("CHI","DAL"),("SF","ARI"),("NYG","KC"),
             ("BAL","DET")],
          4:[("ARI","SEA"),("PIT","MIN"),("ATL","WAS"),("BUF","NO"),("DET","CLE"),
             ("NE","CAR"),("NYG","LAC"),("TB","PHI"),("HOU","TEN"),("LAR","IND"),
             ("SF","JAX"),("KC","BAL"),("LV","CHI"),("DAL","GB"),("MIA","NYJ"),
             ("DEN","CIN")],
          5:[("LAR","SF"),("CLE","MIN"),("IND","LV"),("NO","NYG"),("NYJ","DAL"),
             ("PHI","DEN"),("CAR","MIA"),("BAL","HOU"),("ARI","TEN"),("SEA","TB"),
             ("CIN","DET"),("LAC","WAS"),("BUF","NE"),("JAX","KC")],
          6:[("NYG","PHI"),("NYJ","DEN"),("IND","ARI"),("MIA","LAC"),("PIT","CLE"),
             ("TB","SF"),("CAR","DAL"),("JAX","SEA"),("BAL","LAR"),("LV","TEN"),
             ("GB","CIN"),("NO","NE"),("KC","DET"),("ATL","BUF"),("WAS","CHI")],
          7:[("CIN","PIT"),("JAX","LAR"),("CHI","NO"),("CLE","MIA"),("TEN","NE"),
             ("KC","LV"),("MIN","PHI"),("NYJ","CAR"),("DEN","NYG"),("LAC","IND"),
             ("DAL","WAS"),("ARI","GB"),("SF","ATL"),("DET","TB"),("SEA","HOU")],
          8:[("LAC","MIN"),("ATL","MIA"),("CIN","NYJ"),("NE","CLE"),("PHI","NYG"),
             ("CAR","BUF"),("BAL","CHI"),("HOU","SF"),("NO","TB"),("DEN","DAL"),
             ("IND","TEN"),("PIT","GB"),("KC","WAS")],
          9:[("MIA","BAL"),("CIN","CHI"),("DET","MIN"),("GB","CAR"),("TEN","LAC"),
             ("NE","ATL"),("NYG","SF"),("PIT","IND"),("HOU","DEN"),("LV","JAX"),
             ("LAR","NO"),("BUF","KC"),("WAS","SEA"),("DAL","ARI")],
          10:[("DEN","LV"),("IND","ATL"),("CHI","NYG"),("MIA","BUF"),("MIN","BAL"),
             ("NYJ","CLE"),("TB","NE"),("CAR","NO"),("HOU","JAX"),("SEA","ARI"),
             ("SF","LAR"),("WAS","DET"),("LAC","PIT"),("GB","PHI")],
          11:[("NE","NYJ"),("MIA","WAS"),("ATL","CAR"),("BUF","TB"),("TEN","HOU"),
             ("MIN","CHI"),("NYG","GB"),("PIT","CIN"),("JAX","LAC"),("LAR","SEA"),
             ("ARI","SF"),("CLE","BAL"),("DEN","KC"),("PHI","DET"),("LV","DAL")],
          12:[("HOU","BUF"),("CHI","PIT"),("CIN","NE"),("DET","NYG"),("GB","MIN"),
             ("TEN","SEA"),("KC","IND"),("BAL","NYJ"),("LV","CLE"),("ARI","JAX"),
             ("DAL","PHI"),("NO","ATL"),("LAR","TB"),("SF","CAR")],
          13:[("DET","GB"),("DAL","KC"),("BAL","CIN"),("PHI","CHI"),("CLE","SF"),
             ("TEN","JAX"),("IND","HOU"),("MIA","NO"),("NYJ","ATL"),("TB","ARI"),
             ("CAR","LAR"),("SEA","MIN"),("PIT","BUF"),("LAC","LV"),("WAS","DEN"),
             ("NE","NYG")],
          14:[("DET","DAL"),("ATL","SEA"),("CLE","TEN"),("GB","CHI"),("MIN","WAS"),
             ("NYJ","MIA"),("TB","NO"),("JAX","IND"),("BAL","PIT"),("LV","DEN"),
             ("BUF","CIN"),("ARI","LAR"),("KC","HOU"),("LAC","PHI")],
          15:[("TB","ATL"),("CHI","CLE"),("CIN","BAL"),("KC","LAC"),("NE","BUF"),
             ("NYG","WAS"),("PHI","LV"),("JAX","NYJ"),("HOU","ARI"),("DEN","GB"),
             ("LAR","DET"),("NO","CAR"),("SF","TEN"),("SEA","IND"),("DAL","MIN"),
             ("PIT","MIA")],
          16:[("SEA","LAR"),("CHI","GB"),("WAS","PHI"),("CLE","BUF"),("DAL","LAC"),
             ("TEN","KC"),("NO","NYJ"),("NYG","MIN"),("CAR","TB"),("BAL","NE"),
             ("DEN","JAX"),("ARI","ATL"),("DET","PIT"),("HOU","LV"),("MIA","CIN"),
             ("IND","SF")],
          17:[("WAS","DAL"),("MIN","DET"),("KC","DEN"),("CLE","PIT"),("TEN","NO"),
             ("IND","JAX"),("MIA","TB"),("NYJ","NE"),("BUF","PHI"),("SF","CHI"),
             ("ATL","LAR"),("CIN","ARI"),("GB","BAL"),("LV","NYG"),("LAC","HOU"),
             ("CAR","SEA")],
          18:[("ATL","NO"),("BUF","NYJ"),("CHI","DET"),("CIN","CLE"),("DEN","LAC"),
             ("LV","KC"),("LAR","ARI"),("MIN","GB"),("NE","MIA"),("NYG","DAL"),
             ("PHI","WAS"),("PIT","BAL"),("SF","SEA"),("TB","CAR"),("JAX","TEN"),
             ("HOU","IND")]}
sim = Monte_Carlo_Sim()
n = 100
cpus = 10

results = defaultdict(dict)
stats = defaultdict(lambda: defaultdict(list))


if __name__ == "__main__":
    freeze_support()

    for week, games in tqdm(season.items()):
        for matchup in tqdm(games):
            name = matchup[0] + "v" + matchup[1]
            home_results, away_results = sim.parallel_sim(matchup[0], matchup[1],n,
                                                        cpus)
            results[week][name] = (np.mean(home_results),np.mean(away_results))
            reformed_stats = {(stat, player): values 
                            for stat, players in sim.sim_stats.items() 
                            for player, values in players.items()}
            i = max(len(value) for value in reformed_stats.values())
            fill = [0] * i
            padded_stats = {player:stats[:n] + fill[len(stats):] 
                            for player, stats in reformed_stats.items()}
            for key, game_stats in padded_stats.items():
                stat, player = key[0], key[1]
                stats[player][stat].append(np.mean(game_stats))

    with open("./results/season_scores.json", "w") as f:
        json.dump(results, f)

    with open("./results/season_stats.json", "w") as f:
        json.dump(stats, f)