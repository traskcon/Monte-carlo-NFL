import numpy as np
import scipy.stats as st
import pandas as pd

def rush_yds(team, rb_dist, defense_dist):
    # Based on RB, OL, Def distributions, randomly sample and return rush yards on a given play
    # Weighting factors
    lambda_rb, lambda_ol, lambda_def = 1, 1, 1
    # Offensive line yards before contact for 2024
    ol_ybc = {"ATL":2.2,"BUF":2.5,"CAR":2.7,"CHI":2.5,"CIN":2.7,"CLE":2.5,"IND":2.9,"ARI":3.0,"DAL":2.1,"DEN":2.4,"DET":2.6,"GB":2.4,"HOU":2.4,
              "JAX":2.0,"KC":2.4,"MIA":2.3,"MIN":2.3,"NO":2.5,"NE":2.4,"NYG":2.5,"NYJ":2.1,"TEN":2.1,"PIT":2.2,"PHI":3.2,"LV":1.9,"LAR":2.2,
              "BAL":3.3,"LAC":2.0,"SEA":2.4,"SF":2.7,"TB":2.8,"WAS":2.9}
    rb_yac = rb_dist.rvs(1)[0]
    def_yards = defense_dist.rvs(1)[0]
    return (lambda_rb*rb_yac + lambda_def*def_yards + lambda_ol*ol_ybc[team]) / (lambda_rb+lambda_ol+lambda_def)

def build_rb_run_distributions(rb, run_data):
    # calculate/fit distributions of rush yards per carry for RB
    # Generalized Extreme Value Distribution chosen as best fitting distribution
    dist = getattr(st, "genextreme")
    # RB Data & distribution
    try:
        # Fit RB specific distribution
        rb_data = run_data[run_data["rusher_player_name"] == rb]["yards_gained"]
        rb_params = dist.fit(rb_data)
    except:
        # Otherwise just use league average
        rb_data = run_data["yards_gained"]
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
        
def print_play_type(play_type, args):
    match play_type:
        case "pass":
            net_yards, yardline, target = args
            print("Result of play: {} to {} for {} yards, to the {} yardline".format(play_type,target,net_yards,yardline))
        case "run":
            net_yards, yardline, rb = args
            print("Result of play: {} by {} for {} yards, to the {} yardline".format(play_type,rb,net_yards,yardline))
        case "field_goal":
            print("Result of play: {}".format(play_type))
        case "punt":
            print("Result of play: {}".format(play_type))

def sim_game(home, away, team_rosters, playcall_profiles, yard_dist, snap_counts, verbose=False):
    # Given two teams, simulate a single game and return both team's scores
    total_snaps = 124 # Average number of offensive snaps per game
    scores = {home:0, away:0}
    down, distance = 1, 10
    yardline = 65
    rng = np.random.default_rng()
    pos_team = rng.choice((home, away), 1)[0]
    def_team = home if pos_team == away else away
    for i in range(total_snaps):
        if verbose:
            print("Offense: {}".format(pos_team))
            print("Down: {}, Distance: {} on the {} yardline".format(down, distance, yardline))
        # Set relevant variables
        redzone = True if yardline <= 20 else False
        dist_type = determine_dist_type(down, distance)
        # Get coach playcalling tendency for down and distance
        pos_coach = team_rosters.loc[team_rosters["team"] == pos_team, "coach"].iloc[0]
        tendencies = playcall_profiles.loc[(playcall_profiles["coach"]==pos_coach) & (playcall_profiles["down"]==down) 
                                           & (playcall_profiles["distance"] == dist_type) & (playcall_profiles["red_zone"] == redzone), 
                                           ["pass_prob","run_prob","fg_prob","punt_prob"]].iloc[0]
        play_type = rng.choice(("pass","run","field_goal","punt"), 1, p=tendencies)[0]
        # Based on what play_type is chosen, run yardage function
        match play_type:
            case "pass":
                pass_yds()
                net_yards = 0
            case "run":
                rb_carries = snap_counts["rushers"]
                rb = rng.choice(team_rosters[team_rosters["team"] == pos_team][["rb_1","rb_2"]].iloc[0],1,p=list(rb_carries[pos_team].values()))[0]
                net_yards = rush_yds(pos_team, yard_dist["rush_rb"][rb], yard_dist["rush_def"][def_team])
                yardline -= net_yards
                distance -= net_yards
                play_details = [net_yards, yardline, rb]
            case "field_goal":
                field_goal_attempt()
                net_yards = 0
            case "punt":
                punt()
                net_yards = 0
        # Update relevant variables (can happen inside the functions)
        if yardline < 0:
            scores[pos_team] += 7 # Assuming automatic extra point on every touchdown (fix later)
            down, distance, yardline = 1, 10, 65
            pos_team, def_team = def_team, pos_team
        elif down == 4 and distance > 0:
            # Turnover on downs
            down, distance = 1, 10
            yardline = 100 - yardline
            pos_team, def_team = def_team, pos_team
        elif distance <= 0:
            # First down
            down, distance = 1, 10
        else:
            down += 1
        if verbose:
            print_play_type(play_type, play_details)
    return scores[home], scores[away]

def monte_carlo_sim(n, home, away, verbose):
    # Simulate n games between two teams, returning summary statistics
    home_scores, away_scores = [], []
    # Load relevant data
    rush_data = pd.read_csv("2024_rushes.csv")
    team_rosters = pd.read_csv("teams.csv")
    playcall_profiles = pd.read_csv("playcall_profiles.csv")
    rush_pct = pd.read_csv("rush_pct.csv", index_col="team")
    # create relevant distributions
    rbs = team_rosters.loc[team_rosters["team"].isin([home, away]), ["rb_1","rb_2"]].values.flatten().tolist()
    # TODO: change from rb names to rb ids
    rb_dists = {rb:build_rb_run_distributions(rb, rush_data) for rb in rbs}
    rush_def_dists = {defense:build_def_run_distributions(defense, rush_data) for defense in (home, away)}
    yard_distributions = {"rush_rb":rb_dists, "rush_def":rush_def_dists}
    # Load Snap/target percentages for each position
    rb_carries = rush_pct.to_dict("index")
    snap_counts = {"rushers":rb_carries}
    for game in range(n):
        home_score, away_score = sim_game(home, away, team_rosters, playcall_profiles, yard_distributions, snap_counts, verbose)
        home_scores.append(home_score)
        away_scores.append(away_score)
    return home_scores, away_scores

print(monte_carlo_sim(1,"PHI","DAL",True))