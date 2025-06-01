import numpy as np
import scipy.stats as st
import pandas as pd

def rush_yds(team, rb, defense):
    # Based on RB, OL, Def distributions, randomly sample and return rush yards on a given play
    # Offensive line yards before contact for 2024
    ol_ybc = {"ATL":2.2,"BUF":2.5,"CAR":2.7,"CHI":2.5,"CIN":2.7,"CLE":2.5,"IND":2.9,"ARI":3.0,"DAL":2.1,"DEN":2.4,"DET":2.6,"GB":2.4,"HOU":2.4,
              "JAX":2.0,"KC":2.4,"MIA":2.3,"MIN":2.3,"NO":2.5,"NE":2.4,"NYG":2.5,"NYJ":2.1,"TEN":2.1,"PIT":2.2,"PHI":3.2,"LV":1.9,"LAR":2.2,
              "BAL":3.3,"LAC":2.0,"SEA":2.4,"SF":2.7,"TB":2.8,"WAS":2.9}
    pass

def build_rb_run_distributions(rb, run_data):
    # calculate/fit distributions of rush yards per carry for RB
    # Generalized Extreme Value Distribution chosen as best fitting distribution
    dist = getattr(st, "genextreme")
    # RB Data & distribution
    rb_data = run_data[run_data["rusher_player_name"] == rb]["yards_gained"]
    rb_params = dist.fit(rb_data)
    rb_dist = st.genextreme(*rb_params)
    return rb_dist

def build_def_run_distributions(defense, run_data):
    dist = getattr(st, "genextreme")
    def_data = run_data[run_data["def_team"] == defense]["yards_gained"]
    def_params = dist.fit(def_data)
    def_dist = st.genextreme(*def_params)
    return def_dist

def pass_yds():
    # Based on QB, WR, Def distributions, randomly sample and return pass yards on a given play
    pass

def build_pass_distributions():
    # calculate/fit distributions of pass yds per attempt for QB, WR, Def
    pass

def field_goal_attempt():
    pass

def punt():
    pass

def determine_dist_type(down, distance):
    if down == 1:
        return "All"
    else:
        if distance < 4:
            return "Short"
        elif distance > 6:
            return "Long"
        else:
            return "Mid"

def sim_game(home, away, team_rosters, playcall_profiles):
    # Given two teams, simulate a single game and return both team's scores
    total_snaps = 124 # Average number of offensive snaps per game
    scores = {home:0, away:0}
    down, distance = 1, 10
    yardline = 65
    rng = np.random.default_rng()
    pos_team = rng.choice((home, away), 1)
    for i in range(total_snaps):
        # Set relevant variables
        redzone = True if yardline <= 20 else False
        dist_type = determine_dist_type(down, distance)
        # Get coach playcalling tendency for down and distance
        pos_coach = team_rosters[team_rosters["team"] == pos_team]["coach"]
        tendencies = playcall_profiles.loc[(playcall_profiles["coach"]==pos_coach) & (playcall_profiles["down"]==down) 
                                           & (playcall_profiles["distance"] == dist_type) & (playcall_profiles["red_zone"] == redzone), 
                                           ["pass_prob","run_prob","fg_prob","punt_prob"]]
        play_type = rng.choice(("pass","run","field_goal","punt"), 1, p=tendencies)
        # Based on what play_type is chosen, run yardage function
        match play_type:
            case "pass":
                pass_yds()
            case "run":
                rush_yds()
            case "field_goal":
                field_goal_attempt()
            case "punt":
                punt()
        # Update relevant variables (can happen inside the functions)
        if yardline < 0:
            scores[pos_team] += 7 # Assuming automatic extra point on every touchdown (fix later)
            down, distance, yardline = 1, 10, 65
            pos_team = home if pos_team == away else away

def monte_carlo_sim(n, home, away):
    # Simulate n games between two teams, returning summary statistics
    home_scores, away_scores = [], []
    # Load relevant data
    rush_data = pd.read_csv("2024_rushes.csv")
    team_rosters = pd.read_csv("teams.csv")
    playcall_profiles = pd.read_csv("playcall_profiles.csv")
    # create relevant distributions
    rbs = team_rosters.loc[team_rosters["team"] in (home, away), ["rb_1","rb_2"]]
    rb_dists = {rb:build_rb_run_distributions(rb, rush_data) for rb in rbs}
    rush_def_dists = {defense:build_def_run_distributions(defense, rush_data) for defense in (home, away)}
    for game in range(n):
        home_score, away_score = sim_game(home, away, team_rosters, playcall_profiles)
        home_scores.append(home_score)
        away_scores.append(away_score)
    return home_scores, away_scores
