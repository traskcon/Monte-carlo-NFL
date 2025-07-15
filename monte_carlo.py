import numpy as np
import scipy.stats as st
import pandas as pd
from time import time
from sklearn.linear_model import LogisticRegression
from collections import defaultdict
import warnings
from tqdm import tqdm
import istarmap
from multiprocessing import Pool, freeze_support
import json
import os
warnings.filterwarnings("ignore", category=UserWarning)
pd.options.mode.chained_assignment = None

class Monte_Carlo_Sim:
    """Class for simulating many NFL games at a play-by-play level.
    
    This class simulates NFL games at a play-by-play level by building and 
    sampling from statistical distributions of relevant stats & playcalling 
    tendencies. The load_data() and build_distributions() functions initialize
    these distributions based on historical data. The sim_game() function
    simulates a single game, which is called by run_simulations() and parallel_sim()
    to simulate n games. 

    Typical usage example:

        sim = Monte_Carlo_Sim()
        home_scores, away_scores, stats = sim.parallel_sim("PHI","DAL",10000)

    Attributes:
        sim_stats:
        verbose:

    """
    
    def __init__(self):
        # Load relevant data
        self.load_data()
        self.build_distributions()

    def load_data(self):
        rush_data = pd.read_csv("./data/2024_rushes.csv")
        self._fg_data = pd.read_csv("./data/field_goals.csv")
        punt_data = pd.read_csv("./data/punts.csv")
        pass_data = pd.read_csv("./data/2024_passes.csv")
        pass_yards = pass_data[pass_data["complete_pass"] == 1]
        self._yard_data = {"rb":rush_data, "punt":punt_data, "rush_def":rush_data, 
                          "ay":pass_yards, "yac":pass_yards, "pass_def":pass_yards}
        self._team_rosters = pd.read_csv("./data/teams.csv")
        self._playcall_profiles = pd.read_csv("./data/playcall_profiles.csv")
        target_data = pd.read_csv("./data/target_pct.csv", index_col="team")
        rush_pct = pd.read_csv("./data/rush_pct.csv", index_col="team")
        # Load Snap/target percentages for each position
        self._rb_carries = rush_pct.to_dict("index")
        self._target_rates = target_data.to_dict("index")
        player_ids = pd.read_csv("./data/player_ids.csv", index_col=0)
        self.__id_dict = dict(zip(player_ids.full_name,player_ids.gsis_id))
        # Calculate Catch, Completion, Interception percentages
        self._catch_pct = self.__get_rates(pass_data,"receiver_player_id","complete_pass")
        self._comp_pct = self.__get_rates(pass_data,"passer_player_id","complete_pass")
        self._int_rate = self.__get_rates(pass_data,"passer_player_id","interception")
        self._def_ints = self.__get_rates(pass_data,"defteam","interception")

    def __get_rates(self, pass_data:pd.DataFrame, id, stat):
        stat_pct = pass_data[[id,stat]].groupby([id]).mean()
        return dict(zip(stat_pct.index, stat_pct[stat]))

    def get_ids(self, player_names):
        return [self.__id_dict[player] for player in player_names]
    
    def get_names(self, player_ids):
        name_dict = {id: name for name, id in self.__id_dict.items()}
        return [name_dict[id] for id in player_ids]
    
    def __determine_dist_type(self, down, distance):
        if down == 1:
            return "All"
        else:
            if distance < 4:
                return "Short"
            elif distance > 6:
                return "Long"
            else:
                return "Mid"

    def __print_play_type(self, play_type, args):
        match play_type:
            case "pass":
                self._play_counts[play_type][args[2]] += 1
                print("Result of play: {} to {} for {:.1f} yards, to the {:.0f} yardline".format(play_type,args[2],args[0],args[1]))
            case "run":
                self._play_counts[play_type][args[2]] += 1
                print("Result of play: {} by {} for {:.1f} yards, to the {:.0f} yardline".format(play_type,args[2],args[0],args[1]))
            case "field_goal":
                if args[0]:
                    print("Result of play: Field Goal by {} is good!".format(args[1]))
                else:
                    print("Result of play: Field Goal by {} is no good".format(args[1]))
            case "punt":
                print("Result of play: {}".format(play_type))

    def build_distributions(self):
        params_file = "./data/params.json"
        self.__params = json.load(open(params_file, "r")) if os.path.exists(params_file) else defaultdict(dict)
        # Get player names
        rbs = self._team_rosters[["qb","rb_1","rb_2"]].to_numpy().flatten().tolist()
        kickers = self._team_rosters[["kicker"]].values.flatten().tolist()
        punters = self._team_rosters[["punter"]].values.flatten().tolist()
        teams = self._team_rosters[["team"]].values.flatten().tolist()
        targets = self._team_rosters.iloc[:,3:11].to_numpy().flatten().tolist()
        qbs = self._team_rosters[["qb"]].to_numpy().flatten().tolist()
        # Fit Distributions/Models
        self._rb_dists = {rb:self.build_yardage_distribution("rb",rb) for rb in self.get_ids(rbs)}
        self._rush_def_dists = {defense:self.build_yardage_distribution("rush_def",defense) for defense in teams}
        self._fg_dists = {kicker:self.fit_fg_model(kicker) for kicker in self.get_ids(kickers)}
        self._punt_dists = {punter:self.build_yardage_distribution("punt",punter) for punter in self.get_ids(punters)}
        self._ay_dists = {qb:self.build_yardage_distribution("ay",qb) for qb in self.get_ids(qbs)}
        self._yac_dists = {target:self.build_yardage_distribution("yac",target) for target in self.get_ids(targets)}
        self._pass_def_dists = {defense:self.build_yardage_distribution("pass_def",defense) for defense in teams}
        # If params file doesn't exist, create one with the fitted params
        if not os.path.exists("./data/params.json"):
            with open("./data/params.json", "w") as f:
                json.dump(self.__params, f)

    def build_yardage_distribution(self, dist_type, id):
        # Generalized function for building yardage distributions
        id_keys = {"punt":"punter_player_id","rb":"rusher_player_id",
                   "rush_def":"defteam","ay":"passer_player_id",
                   "yac":"receiver_player_id", "pass_def":"defteam"}
        yard_keys = {"punt":"kick_distance","rb":"yards_gained_rush",
                     "rush_def":"yards_gained_rush","ay":"air_yards",
                     "yac":"yards_after_catch", "pass_def":"yards_gained_pass"}
        # Normal distribution for punts, genextreme for all others
        dist = getattr(st, "norm") if dist_type == "punt" else getattr(st, "genextreme")
        # Use "League Average" id if player is missing their gsis id
        id = "LA" if isinstance(id, float) else id
        if os.path.exists("./data/params.json"):
            # Get params from json file if it exists (pre-computed)
            params = self.__params[yard_keys[dist_type]][id]
        else:
            data = self._yard_data[dist_type]
            yard_data = data[data[id_keys[dist_type]] == id][yard_keys[dist_type]]
            # Confirm there's enough specific data, otherwise use league average
            yard_data = yard_data if len(yard_data) > 5 else data[yard_keys[dist_type]]
            yard_data.dropna(inplace=True)
            params = dist.fit(yard_data)
            self.__params[yard_keys[dist_type]][id] = params
        yard_dist = dist(*params)
        return yard_dist
    
    def fit_fg_model(self, kicker):
        fg_data = self._fg_data[self._fg_data["kicker_player_id"] == kicker]
        # Check there's enough FG specific data to be robust, otherwise use league average
        fg_data = fg_data if len(fg_data) > 5 else self._fg_data
        # Fit Sigmoid/logistic model for fg make probability
        fg_model = LogisticRegression(random_state=0).fit(fg_data[["yardline_100"]],
                                                          fg_data["result"])
        return fg_model

    def rush_yds(self):
        # Pick RB1 or RB2 based on snap counts
        rushers = self._team_rosters[self._team_rosters["team"] == self.__pos_team]
        rb = self.__rng.choice(rushers[["qb","rb_1","rb_2"]].iloc[0], 1, 
                               p=list(self._rb_carries[self.__pos_team].values()))[0]
        rb_id = self.get_ids([rb])[0]
        # Based on RB, OL, Def distributions, randomly sample and return rush yards on a given play
        rb_yac = self._rb_dists[rb_id].rvs(1)[0]
        def_yards = self._rush_def_dists[self.__def_team].rvs(1)[0]
        # Weighting factors (Temporarily removed OL contribution)
        lambda_rb, lambda_ol, lambda_def = 1, 0, 1
        # Offensive line yards before contact for 2024
        ol_ybc = {"ATL":2.2,"BUF":2.5,"CAR":2.7,"CHI":2.5,"CIN":2.7,"CLE":2.5,
                  "IND":2.9,"ARI":3.0,"DAL":2.1,"DEN":2.4,"DET":2.6,"GB":2.4,
                  "HOU":2.4,"JAX":2.0,"KC":2.4,"MIA":2.3,"MIN":2.3,"NO":2.5,
                  "NE":2.4,"NYG":2.5,"NYJ":2.1,"TEN":2.1,"PIT":2.2,"PHI":3.2,
                  "LV":1.9,"LAR":2.2,"BAL":3.3,"LAC":2.0,"SEA":2.4,"SF":2.7,
                  "TB":2.8,"WAS":2.9}
        return (lambda_rb*rb_yac + lambda_def*def_yards + lambda_ol*ol_ybc[self.__pos_team]) / (lambda_rb+lambda_ol+lambda_def), rb
    
    def pass_yds(self, stats):
        # Based on QB, WR, Def distributions, randomly sample and return pass yards on a given play
        qb = self._team_rosters[self._team_rosters["team"] == self.__pos_team]["qb"].iloc[0]
        qb_id = self.get_ids([qb])[0]
        # Choose target based on target_pct
        targets = self._team_rosters[self._team_rosters["team"] == self.__pos_team].iloc[0,3:11]
        target = self.__rng.choice(targets, 1, p=list(self._target_rates[self.__pos_team].values()))[0]
        target_id = self.get_ids([target])[0]
        # Check QB & Defense for interception
        int_pct = self._int_rate.get(qb_id, np.mean(list(self._int_rate.values())))
        def_int_pct = self._def_ints[self.__def_team]
        if self.__rng.uniform() < ((int_pct + def_int_pct)/2):
            stats["ints"][qb] = stats["ints"].get(qb, 0) + 1
            air_yards = self._ay_dists[qb_id].rvs(1)[0]
            # ~40% of interception returns are 0 yards, currently assuming all returns are 0 yards
            self.__yardline -= air_yards
            self.__turnover(downs=False, score=False)
            return 0, target, qb, stats
        # Calculate weighted completion pct (qb_cmp_pct, catch_pct)
        # Use league averages for rookies
        comp_pct = self._comp_pct.get(qb_id, np.mean(list(self._comp_pct.values())))
        catch_pct = self._catch_pct.get(target_id, np.mean(list(self._catch_pct.values())))
        if self.__rng.uniform() < ((comp_pct + catch_pct)/2):
            stats["rec"][target] = stats["rec"].get(target,0) + 1
            # If complete, sample from yardage distributions
            air_yards = self._ay_dists[qb_id].rvs(1)[0]
            yac = self._yac_dists[target_id].rvs(1)[0]
            def_yards = self._pass_def_dists[self.__def_team].rvs(1)[0]
            lambda_ay, lambda_yac, lambda_def = 1, 1, 1
            return (lambda_ay*air_yards + lambda_yac*yac + lambda_def*def_yards) / (0.5*lambda_ay+0.5*lambda_yac+lambda_def), target, qb, stats
        # Else netyards = 0
        return 0, target, qb, stats

    def field_goal_attempt(self):
        kicker = self._team_rosters[self._team_rosters["team"] == self.__pos_team]["kicker"].iloc[0]
        kicker_id = self.get_ids([kicker])[0]
        fg_model = self._fg_dists[kicker_id]
        make_prob = fg_model.predict_proba(np.array([[self.__yardline]]))[0,0]
        return make_prob >= self.__rng.uniform(), kicker
    
    def punt(self):
        punter = self._team_rosters[self._team_rosters["team"] == self.__pos_team]["punter"].iloc[0]
        punter_id = self.get_ids([punter])[0]
        punt_dist = self._punt_dists[punter_id]
        # Weighting factors
        lambda_pr = 1
        lambda_pay = 1
        # Punt Returner projections from Mike Clay: https://g.espncdn.com/s/ffldraftkit/25/NFLDK2025_CS_ClayProjections2025.pdf?adddata=2025CS_ClayProjections2025
        punt_returners = {"ATL":258/27,"BUF":317/28,"CAR":231/27,"CHI":257/29,
                          "CIN":259/27,"CLE":252/27,"IND":283/28,"ARI":272/28,
                          "DAL":276/27,"DEN":443/29,"DET":410/31,"GB":258/29,
                          "HOU":290/30,"JAX":259/27,"KC":266/28,"MIA":214/28,
                          "MIN":284/30,"NO":258/27,"NE":437/29,"NYG":228/29,
                          "NYJ":230/29,"TEN":252/27,"PIT":317/30,"PHI":247/28,
                          "LV":258/27,"LAR":264/28,"BAL":288/30,"LAC":336/27,
                          "SEA":206/30,"SF":237/27,"TB":235/28,"WAS":243/25}
        punt_yards = punt_dist.rvs(1)[0]
        return (lambda_pr*punt_returners[self.__def_team]+lambda_pay*punt_yards)/(lambda_pr+lambda_pay)
    
    def __turnover(self, downs, score):
        self.__down = 1 if downs else 0
        self.__distance = 10
        self.__yardline = 65 if score else 100 - self.__yardline
        self.__pos_team, self.__def_team = self.__def_team, self.__pos_team

    def run_simulations(self, home, away, n, verbose=False, progress = None):
        # Simulate n games between two teams, returning summary statistics
        home_scores, away_scores, stats = [], [], []
        stat_names = ["pass_yards","pass_tds","ints","rush_yards","rush_tds",
                      "rec", "rec_yards", "rec_tds"]
        self.sim_stats = {stat:defaultdict(list) for stat in stat_names}
        self.verbose = verbose
        for game in tqdm(range(n)):
            home_score, away_score, game_stats = self.sim_game(home, away)
            home_scores.append(home_score)
            away_scores.append(away_score)
            stats.append(game_stats)
            if progress is not None:
                progress.set(game, message="Simulating Games")
        self.update_player_stats(stats)
        return home_scores, away_scores
    
    def parallel_sim(self, home, away, n, cpu_count, verbose=False, progress = None):
        """Simulates n NFL games in parallel.
        
        Args:
            home: String team name abbreviation for home team
            away: String team name abbreviation for away team
            n: Integer number of games to simulate (>0)
            cpu_count: Integer number of cores to split simulations across
            verbose: Boolean controlling whether play results should be printed
            progress: Shiny UI object for displaying simulation progress
        
        Returns:
            Two lists, containing final scores for the home and away teams 
            respectively. Player stats are updated and stored in sim_stats.

        """
        stat_names = ["pass_yards","pass_tds","ints","rush_yards","rush_tds",
                      "rec", "rec_yards", "rec_tds"]
        self.sim_stats = {stat:defaultdict(list) for stat in stat_names}
        self.verbose = verbose
        with Pool(cpu_count) as pool:
            results = list()
            i = 0
            for result in pool.istarmap(self.sim_game, zip([home]*n, [away]*n)):
                i += 1
                results.append(result)
                if progress is not None:
                    progress.set(i, message="Simulating Games")
            home_scores, away_scores, stats = zip(*results) #Unpack list of tuples into two lists
        self.update_player_stats(stats)
        return home_scores, away_scores
    
    def update_player_stats(self, stats):
        for game in stats:
            for stat, players in game.items():
                for player in players:
                    self.sim_stats[stat][player].append(game[stat][player])

    def sim_game(self, home, away):
        """Stochastically simulate a single NFL game
        
        A simulated game consists of 124 total plays/snaps. A flowchart detailing 
        the logical flow of each simulated snap is included as "Sim_Game_Flowchart.jpg".

        Args:
            home: String team name abbreviation for home team
            away: String team name abbreviation for away team
        
        Returns:
            Two integers representing the final score for the home and away team
            respectively and a dictionary containing all of the player stats.

        """
        
        self._play_counts = {"pass":defaultdict(int),"run":defaultdict(int),"field_goal":0,"punt":0}
        self.__rng = np.random.default_rng()
        # Given two teams, simulate a single game and return both teams' scores
        total_snaps = 124 # Average number of offensive snaps per game
        scores = {home:0, away:0}
        stats = {"pass_yards":{},"pass_tds":{},"ints":{},"rush_yards":{},
                 "rush_tds":{},"rec":{}, "rec_yards":{}, "rec_tds":{}}
        self.__down, self.__distance, self.__yardline = 1, 10, 65
        self.__pos_team = self.__rng.choice((home, away), 1)[0]
        self.__def_team = home if self.__pos_team == away else away
        for i in range(total_snaps):
            if self.verbose:
                print("Offense: {}".format(self.__pos_team))
                print("Down: {}, Distance: {:.0f} on the {:.0f} yardline".format(
                    self.__down, self.__distance, self.__yardline))
            # Set relevant variables
            redzone = self.__yardline <= 20
            dist_type = self.__determine_dist_type(self.__down, self.__distance)
            # Get coach playcalling tendency for down and distance
            pos_coach = self._team_rosters.loc[self._team_rosters["team"] == self.__pos_team, "coach"].iloc[0]
            tendencies = self._playcall_profiles.loc[(self._playcall_profiles["coach"]==pos_coach) & 
                            (self._playcall_profiles["down"]==self.__down) & 
                            (self._playcall_profiles["distance"] == dist_type) & 
                            (self._playcall_profiles["red_zone"] == redzone), 
                            ["pass_prob","run_prob","fg_prob","punt_prob"]].iloc[0]
            play_type = self.__rng.choice(("pass","run","field_goal","punt"), 1, p=tendencies)[0]
            # Based on what play_type is chosen, run yardage function
            match play_type:
                case "pass":
                    net_yards, target, qb, stats = self.pass_yds(stats)
                    net_yards = min(net_yards, self.__yardline+1) #cap yards by yardline
                    self.__yardline -= net_yards
                    self.__distance -= net_yards
                    play_details = [net_yards,self.__yardline,target]
                    stats["pass_yards"][qb] = stats["pass_yards"].get(qb, 0) + net_yards
                    stats["rec_yards"][target] = stats["rec_yards"].get(target, 0) + net_yards
                case "run":
                    net_yards, rb = self.rush_yds()
                    net_yards = min(net_yards, self.__yardline+1)
                    self.__yardline -= net_yards
                    self.__distance -= net_yards
                    play_details = [net_yards, self.__yardline, rb]
                    stats["rush_yards"][rb] = stats["rush_yards"].get(rb, 0) + net_yards
                case "field_goal":
                    good, kicker = self.field_goal_attempt()
                    if good:    
                        scores[self.__pos_team] += 3
                        self.__turnover(downs=False, score=True)
                    else:
                        self.__turnover(downs=False, score=False)
                    play_details = [good, kicker]
                case "punt":
                    net_yards = self.punt()
                    self.__yardline -= net_yards if net_yards > 0 else 20
                    self.__turnover(downs=False, score=False)
            # Update relevant variables (can happen inside the functions)
            if self.__yardline < 0:
                scores[self.__pos_team] += 7 # Assuming automatic extra point on every touchdown (fix later)
                self.__turnover(downs=True, score=True)
                if play_type == "pass":
                    stats["pass_tds"][qb] = stats["pass_tds"].get(qb, 0) + 1
                    stats["rec_tds"][target] = stats["rec_tds"].get(target, 0) + 1
                else:
                    stats["rush_tds"][rb] = stats["rush_tds"].get(rb, 0) + 1
            elif self.__down == 4 and self.__distance > 0:
                # Turnover on downs
                self.__turnover(downs=True, score=False)
            elif self.__distance <= 0:
                # First down
                self.__down, self.__distance = 1, 10
            else:
                self.__down += 1
            if self.verbose:
                self.__print_play_type(play_type, play_details)
        return scores[home], scores[away], stats
    
    def export_stats(self, home, away, path="./results/", suffix="stats.csv"):
        reformed_stats = {(stat, player): values for stat, players in self.sim_stats.items() for player, values in players.items()}
        n = max(len(value) for value in reformed_stats.values())
        fill = [0] * n
        padded_stats = {player:stats[:n] + fill[len(stats):] for player, stats in reformed_stats.items()}
        stat_df = pd.DataFrame(padded_stats)
        game_str = path + home + "v" + away + suffix
        stat_df.to_csv(game_str)

if __name__ == "__main__":
    freeze_support()
    sim_test = Monte_Carlo_Sim()
    home, away = "PHI", "DAL"
    '''t3 = time()
    home_scores, away_scores = sim_test.parallel_sim(home, away, 1000, 8)
    t4 = time()
    print("Simulation Results - {}: {:.2f}, {}: {:.2f}".format(home, np.mean(home_scores), away, np.mean(away_scores)))
    print("Parallel Sim Time: {:.4f}s".format(t4-t3))
    sim_test.export_stats(home, away, suffix="stats_2.csv")'''
    sim_test.run_simulations(home, away, 1, verbose=True)
    print(sim_test._play_counts)