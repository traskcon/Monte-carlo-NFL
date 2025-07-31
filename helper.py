import pandas as pd
import numpy as np

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