import numpy as np
import scipy.stats as st
import pandas as pd
from time import time
from sklearn.linear_model import LogisticRegression
from collections import defaultdict
import warnings
from tqdm import tqdm
warnings.filterwarnings("ignore", category=UserWarning)
pd.options.mode.chained_assignment = None

class Monte_Carlo_Sim:
    def __init__(self):
        # Load relevant data
        self.load_data()
        self.build_distributions()
        self.rng = np.random.default_rng()

    def load_data(self):
        rush_data = pd.read_csv("2024_rushes.csv")
        self.fg_data = pd.read_csv("field_goals.csv")
        punt_data = pd.read_csv("punts.csv")
        pass_data = pd.read_csv("2024_passes.csv")
        pass_yards = pass_data[pass_data["complete_pass"] == 1]
        self.yard_data = {"rb":rush_data, "punt":punt_data, "rush_def":rush_data, "ay":pass_yards, "yac":pass_yards, "pass_def":pass_yards}
        self.team_rosters = pd.read_csv("teams.csv")
        self.playcall_profiles = pd.read_csv("playcall_profiles.csv")
        target_data = pd.read_csv("target_pct.csv", index_col="team")
        rush_pct = pd.read_csv("rush_pct.csv", index_col="team")
        # Load Snap/target percentages for each position
        self.rb_carries = rush_pct.to_dict("index")
        self.target_rates = target_data.to_dict("index")
        player_ids = pd.read_csv("player_ids.csv", index_col=0)
        self.id_dict = dict(zip(player_ids.full_name,player_ids.gsis_id))
        # Calculate Catch, Completion percentages
        catch_pct = pass_data[["receiver_player_id","complete_pass"]].groupby(["receiver_player_id"]).mean()
        self.catch_pct = dict(zip(catch_pct.index, catch_pct.complete_pass))
        comp_pct = pass_data[["passer_player_id","complete_pass"]].groupby(["passer_player_id"]).mean()
        self.comp_pct = dict(zip(comp_pct.index, comp_pct.complete_pass))

    def get_ids(self, player_names):
        return [self.id_dict[player] for player in player_names]
    
    def get_names(self, player_ids):
        name_dict = {id: name for name, id in self.id_dict.items()}
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
                print("Result of play: {} to {} for {:.1f} yards, to the {:.0f} yardline".format(play_type,args[2],args[0],args[1]))
            case "run":
                print("Result of play: {} by {} for {:.1f} yards, to the {:.0f} yardline".format(play_type,args[2],args[0],args[1]))
            case "field_goal":
                if args[0]:
                    print("Result of play: Field Goal by {} is good!".format(args[1]))
                else:
                    print("Result of play: Field Goal by {} is no good".format(args[1]))
            case "punt":
                print("Result of play: {}".format(play_type))

    def build_distributions(self):
        # Get player names
        rbs = self.team_rosters[["rb_1","rb_2"]].to_numpy().flatten().tolist()
        kickers = self.team_rosters[["kicker"]].values.flatten().tolist()
        punters = self.team_rosters[["punter"]].values.flatten().tolist()
        teams = self.team_rosters[["team"]].values.flatten().tolist()
        targets = self.team_rosters.iloc[:,3:11].to_numpy().flatten().tolist()
        qbs = self.team_rosters[["qb"]].to_numpy().flatten().tolist()
        # Fit Distributions/Models
        self.rb_dists = {rb:self.build_yardage_distribution("rb",rb) for rb in self.get_ids(rbs)}
        self.rush_def_dists = {defense:self.build_yardage_distribution("rush_def",defense) for defense in teams}
        self.fg_dists = {kicker:self.fit_fg_model(kicker) for kicker in self.get_ids(kickers)}
        self.punt_dists = {punter:self.build_yardage_distribution("punt",punter) for punter in self.get_ids(punters)}
        self.ay_dists = {qb:self.build_yardage_distribution("ay",qb) for qb in self.get_ids(qbs)}
        self.yac_dists = {target:self.build_yardage_distribution("yac",target) for target in self.get_ids(targets)}
        self.pass_def_dists = {defense:self.build_yardage_distribution("pass_def",defense) for defense in teams}

    def build_yardage_distribution(self, dist_type, id):
        # Generalized function for building yardage distributions
        id_keys = {"punt":"punter_player_id", "rb":"rusher_player_id", "rush_def":"def_team",
                   "ay":"passer_player_id", "yac":"receiver_player_id", "pass_def":"def_team"}
        yard_keys = {"punt":"kick_distance", "rb":"yards_gained", "rush_def":"yards_gained",
                     "ay":"air_yards", "yac":"yards_after_catch", "pass_def":"yards_gained"}
        # Normal distribution for punts, genextreme for all others
        dist = getattr(st, "norm") if dist_type == "punt" else getattr(st, "genextreme")
        data = self.yard_data[dist_type]
        yard_data = data[data[id_keys[dist_type]] == id][yard_keys[dist_type]]
        # Confirm there's enough specific data, otherwise use league average
        yard_data = yard_data if len(yard_data) > 5 else data[yard_keys[dist_type]]
        yard_data.dropna(inplace=True)
        params = dist.fit(yard_data)
        yard_dist = dist(*params)
        return yard_dist
    
    def fit_fg_model(self, kicker):
        fg_data = self.fg_data[self.fg_data["kicker_player_id"] == kicker]
        # Check there's enough FG specific data to be robust, otherwise use league average
        fg_data = fg_data if len(fg_data) > 5 else self.fg_data
        # Fit Sigmoid/logistic model for fg make probability
        fg_model = LogisticRegression(random_state=0).fit(fg_data[["yardline_100"]],fg_data["result"])
        return fg_model

    def rush_yds(self):
        # Pick RB1 or RB2 based on snap counts
        # TODO: Add QB runs
        rb = self.rng.choice(self.team_rosters[self.team_rosters["team"] == self.pos_team][["rb_1","rb_2"]].iloc[0],1,
                             p=list(self.rb_carries[self.pos_team].values()))[0]
        rb_id = self.get_ids([rb])[0]
        # Based on RB, OL, Def distributions, randomly sample and return rush yards on a given play
        rb_yac = self.rb_dists[rb_id].rvs(1)[0]
        def_yards = self.rush_def_dists[self.def_team].rvs(1)[0]
        # Weighting factors
        lambda_rb, lambda_ol, lambda_def = 1, 0.5, 1
        # Offensive line yards before contact for 2024
        ol_ybc = {"ATL":2.2,"BUF":2.5,"CAR":2.7,"CHI":2.5,"CIN":2.7,"CLE":2.5,"IND":2.9,"ARI":3.0,"DAL":2.1,"DEN":2.4,"DET":2.6,"GB":2.4,"HOU":2.4,
                "JAX":2.0,"KC":2.4,"MIA":2.3,"MIN":2.3,"NO":2.5,"NE":2.4,"NYG":2.5,"NYJ":2.1,"TEN":2.1,"PIT":2.2,"PHI":3.2,"LV":1.9,"LAR":2.2,
                "BAL":3.3,"LAC":2.0,"SEA":2.4,"SF":2.7,"TB":2.8,"WAS":2.9}
        return (lambda_rb*rb_yac + lambda_def*def_yards + lambda_ol*ol_ybc[self.pos_team]) / (lambda_rb+lambda_ol+lambda_def), rb
    
    def pass_yds(self):
        # Based on QB, WR, Def distributions, randomly sample and return pass yards on a given play
        qb = self.team_rosters[self.team_rosters["team"] == self.pos_team]["qb"].iloc[0]
        qb_id = self.get_ids([qb])[0]
        # Choose target based on target_pct
        target = self.rng.choice(self.team_rosters[self.team_rosters["team"] == self.pos_team].iloc[0,3:11], 1,
                                 p=list(self.target_rates[self.pos_team].values()))[0]
        target_id = self.get_ids([target])[0]
        # Calculate weighted completion pct (qb_cmp_pct, catch_pct)
        # Use league averages for rookies
        comp_pct = self.comp_pct.get(qb_id, np.mean(list(self.comp_pct.values())))
        catch_pct = self.catch_pct.get(target_id, np.mean(list(self.catch_pct.values())))
        if self.rng.uniform() < ((comp_pct + catch_pct)/2):
            self.stats["rec"][target] = self.stats["rec"].get(target,0) + 1
            # If complete, sample from yardage distributions
            air_yards = self.ay_dists[qb_id].rvs(1)[0]
            yac = self.yac_dists[target_id].rvs(1)[0]
            def_yards = self.pass_def_dists[self.def_team].rvs(1)[0]
            lambda_ay, lambda_yac, lambda_def = 1, 1, 1
            return (lambda_ay*air_yards + lambda_yac*yac + lambda_def*def_yards) / (0.5*lambda_ay+0.5*lambda_yac+lambda_def), target, qb
        # Else netyards = 0
        return 0, target, qb

    def field_goal_attempt(self):
        kicker = self.team_rosters[self.team_rosters["team"] == self.pos_team]["kicker"].iloc[0]
        kicker_id = self.get_ids([kicker])[0]
        fg_model = self.fg_dists[kicker_id]
        make_prob = fg_model.predict_proba(np.array([[self.yardline]]))[0,0]
        return make_prob >= self.rng.uniform(), kicker
    
    def punt(self):
        punter = self.team_rosters[self.team_rosters["team"] == self.pos_team]["punter"].iloc[0]
        punter_id = self.get_ids([punter])[0]
        punt_dist = self.punt_dists[punter_id]
        # Weighting factors
        lambda_pr = 1
        lambda_pay = 1
        # Punt Returner projections from Mike Clay: https://g.espncdn.com/s/ffldraftkit/25/NFLDK2025_CS_ClayProjections2025.pdf?adddata=2025CS_ClayProjections2025
        punt_returners = {"ATL":258/27,"BUF":317/28,"CAR":231/27,"CHI":257/29,"CIN":259/27,"CLE":252/27,"IND":283/28,"ARI":272/28,"DAL":276/27,"DEN":443/29,"DET":410/31,"GB":258/29,"HOU":290/30,
                "JAX":259/27,"KC":266/28,"MIA":214/28,"MIN":284/30,"NO":258/27,"NE":437/29,"NYG":228/29,"NYJ":230/29,"TEN":252/27,"PIT":317/30,"PHI":247/28,"LV":258/27,"LAR":264/28,
                "BAL":288/30,"LAC":336/27,"SEA":206/30,"SF":237/27,"TB":235/28,"WAS":243/25}
        punt_yards = punt_dist.rvs(1)[0]
        return (lambda_pr*punt_returners[self.def_team]+lambda_pay*punt_yards)/(lambda_pr+lambda_pay)
    
    def __turnover(self, downs):
        self.down = 1 if downs else 0
        self.distance = 10
        self.yardline = 100 - self.yardline
        self.pos_team, self.def_team = self.def_team, self.pos_team

    def run_simulations(self, home, away, n, verbose=False):
        # Simulate n games between two teams, returning summary statistics
        home_scores, away_scores = [], []
        stat_names = ["pass_yards","pass_tds","rush_yards","rush_tds", "rec", "rec_yards", "rec_tds"]
        self.sim_stats = {stat:defaultdict(list) for stat in stat_names}
        self.verbose = verbose
        for game in tqdm(range(n)):
            home_score, away_score = self.sim_game(home, away)
            home_scores.append(home_score)
            away_scores.append(away_score)
            for stat, players in self.stats.items():
                for player in players:
                    self.sim_stats[stat][player].append(self.stats[stat][player])
        return home_scores, away_scores

    def sim_game(self, home, away):
        # Given two teams, simulate a single game and return both teams' scores
        total_snaps = 124 # Average number of offensive snaps per game
        scores = {home:0, away:0}
        self.stats = {"pass_yards":{},"pass_tds":{},"rush_yards":{},"rush_tds":{},
                     "rec":{}, "rec_yards":{}, "rec_tds":{}}
        self.down, self.distance, self.yardline = 1, 10, 65
        self.pos_team = self.rng.choice((home, away), 1)[0]
        self.def_team = home if self.pos_team == away else away
        for i in range(total_snaps):
            if self.verbose:
                print("Offense: {}".format(self.pos_team))
                print("Down: {}, Distance: {:.0f} on the {:.0f} yardline".format(self.down, self.distance, self.yardline))
            # Set relevant variables
            redzone = self.yardline <= 20
            dist_type = self.__determine_dist_type(self.down, self.distance)
            # Get coach playcalling tendency for down and distance
            pos_coach = self.team_rosters.loc[self.team_rosters["team"] == self.pos_team, "coach"].iloc[0]
            tendencies = self.playcall_profiles.loc[(self.playcall_profiles["coach"]==pos_coach) & (self.playcall_profiles["down"]==self.down) 
                                            & (self.playcall_profiles["distance"] == dist_type) & (self.playcall_profiles["red_zone"] == redzone), 
                                            ["pass_prob","run_prob","fg_prob","punt_prob"]].iloc[0]
            play_type = self.rng.choice(("pass","run","field_goal","punt"), 1, p=tendencies)[0]
            # Based on what play_type is chosen, run yardage function
            match play_type:
                case "pass":
                    net_yards, target, qb = self.pass_yds()
                    net_yards = min(net_yards, self.yardline+1) #cap yards by yardline
                    self.yardline -= net_yards
                    self.distance -= net_yards
                    play_details = [net_yards,self.yardline,target]
                    self.stats["pass_yards"][qb] = self.stats["pass_yards"].get(qb, 0) + net_yards
                    self.stats["rec_yards"][target] = self.stats["rec_yards"].get(target, 0) + net_yards
                case "run":
                    net_yards, rb = self.rush_yds()
                    net_yards = min(net_yards, self.yardline+1)
                    self.yardline -= net_yards
                    self.distance -= net_yards
                    play_details = [net_yards, self.yardline, rb]
                    self.stats["rush_yards"][rb] = self.stats["rush_yards"].get(rb, 0) + net_yards
                case "field_goal":
                    good, kicker = self.field_goal_attempt()
                    if good:    
                        scores[self.pos_team] += 3
                        self.down, self.distance, self.yardline = 0, 10, 65
                    play_details = [good, kicker]
                case "punt":
                    net_yards = self.punt()
                    self.yardline -= net_yards if net_yards > 0 else 20
                    self.__turnover(downs=False)
            # Update relevant variables (can happen inside the functions)
            if self.yardline < 0:
                scores[self.pos_team] += 7 # Assuming automatic extra point on every touchdown (fix later)
                self.down, self.distance, self.yardline = 1, 10, 65
                self.pos_team, self.def_team = self.def_team, self.pos_team
                if play_type == "pass":
                    self.stats["pass_tds"][qb] = self.stats["pass_tds"].get(qb, 0) + 1
                    self.stats["rec_tds"][target] = self.stats["rec_tds"].get(target, 0) + 1
                else:
                    self.stats["rush_tds"][rb] = self.stats["rush_tds"].get(rb, 0) + 1
            elif self.down == 4 and self.distance > 0:
                # Turnover on downs
                self.__turnover(downs=True)
            elif self.distance <= 0:
                # First down
                self.down, self.distance = 1, 10
            else:
                self.down += 1
            if self.verbose:
                self.__print_play_type(play_type, play_details)
        return scores[home], scores[away]
    
    def export_stats(self,path="stats.csv"):
        reformed_stats = {(stat, player): values for stat, players in self.sim_stats.items() for player, values in players.items()}
        n = max(len(value) for value in reformed_stats.values())
        fill = [0] * n
        padded_stats = {player:stats[:n] + fill[len(stats):] for player, stats in reformed_stats.items()}
        stat_df = pd.DataFrame(padded_stats)
        game_str = self.pos_team + "v" + self.def_team
        stat_df.to_csv(game_str+path)

sim_test = Monte_Carlo_Sim()
phi, dal = sim_test.run_simulations("PHI","DAL",100)
print("Simulation Results - PHI: {:.2f}, DAL: {:.2f}".format(np.mean(phi), np.mean(dal)))
sim_test.export_stats()