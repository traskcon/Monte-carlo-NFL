import pandas as pd
import numpy as np
from time import time
from monte_carlo import Monte_Carlo_Sim

def reshape_team_stats(team:str) -> pd.DataFrame:
    roster_df = pd.read_csv("./data/teams.csv", index_col=0)
    positions = ["qb","rb_1","rb_2","wr_1","wr_2","wr_3","wr_4","te_1","te_2"]
    players = roster_df.loc[team, positions] #type:ignore
    team_stats = players.T.to_frame() #type:ignore
    team_stats["position"] = team_stats.index
    team_stats.reset_index(drop=True, inplace=True)
    team_stats.columns = ["Player", "Pos"]
    team_stats["Pos"] = team_stats["Pos"].str.split("_",n=1).str[0]
    team_stats["Pos"] = team_stats["Pos"].str.upper()
    return team_stats

def get_player_stats(team:str, matchup:str) -> pd.DataFrame:
    team_stats = reshape_team_stats(team)
    game_file = "./results/" + matchup + "stats.csv"
    stat_df = pd.read_csv(game_file, header=[0,1], index_col=0)
    stats = ["pass_yards","pass_tds","ints","rush_yards","rush_tds","rec","rec_yards",
             "rec_tds"]
    for stat in stats:
        team_stats[stat] = team_stats["Player"].apply(lambda x: 
                                            np.mean(stat_df[stat].get(x,0)))
    return team_stats

def time_test(sim:Monte_Carlo_Sim, type:str, n:int, cpu:int, verbose=False,
              inlcude_startup=False):
    # Currently just use PHI and DAL as default values for time_test
    # Since we are only interested in timing and not results
    home, away = "PHI", "DAL"
    if inlcude_startup:
        t1 = time()
        sim = Monte_Carlo_Sim()
    if type == "series":
        t1 = time() if not inlcude_startup else t1
        sim.run_simulations(home, away, n, verbose)
        t2 = time()
        return t2-t1
    elif type == "parallel":
        t1 = time() if not inlcude_startup else t1
        sim.parallel_sim(home, away, n, cpu, verbose)
        t2 = time()
        return t2-t1
    else:
        print("Incorrect type argument. Please select 'series' or 'parallel'")