# Data Dictionary

## Historical Data

### 2024_passes.csv

Description:
Play-by-play pass data from 2024

Creation:
Run sim_functions.R, followed by get_yardage_data(2024, "pass", export=TRUE)

Fields:
* receiver_player_name: String name for targeted receiver
* receiver_player_id: Unique ID string for targeted receiver
* passer_player_name: String name for player who attempted the pass
* passer_player_id: Unique ID string for player who attempted the pass
* complete_pass: Binary indicator of whether or not the pass was complete
* air_yards: Numeric value for distance in yards perpendicular to the line of scrimmage at where the targeted receiver either caught or didn't catch the ball.
* yards_after_catch: Numeric value for distance in yards perpendicular to the yard line where the receiver made the reception to where the play ended.
* defteam: String abbreviation for team on defense
* yards_gained_pass: Numeric yards gained/lost by the possessing team 
    (air_yards + yards_after_catch)

### 2024_rushes.csv

Description:
Play-by-play rush data from 2024

Creation:
Run sim_functions.R, followed by get_yardage_data(2024, "run", export=TRUE)

Fields:
* rusher_player_name: String name for the player that attempted the run
* rusher_player_id: Unique ID string for player who attempted the run
* pos_team: String abbreviation for the team with possesion
* defteam: String abbreviation for team on defense
* yards_gained_rush: Numeric yards gained by the possessing team

### field_goals.csv

Description:
Field goal data from 2024

Creation:
Run sim_functions.R, followed by get_yardage_data(2024, "field goal", export=T)

Fields:
* kicker_player_name: String name of the player who attempted the kick
* kicker_player_id: Unique ID string of the player who attempted the kick
* yardline_100: Numeric distance in yards from the opponent's endzone for the team with possession
* result: Binary indicator of whether the field goal was good or not

### punts.csv

Description:
Punt data from 2024

Creation:
Run sim_functions.R, followed by get_yardage_data(2024, "punt", export=TRUE)

Fields:
* punter_player_name: String name of the player who punted
* punter_player_id: Unique ID string of the player who punted
* kick_distance: Numeric distance in yards the punt travelled past the line of scrimmage

### league_avg_playcalls.csv

Description:
League average playcalling tendencies by down, distance, and red zone status

Creation:
Run league_avg_profile.R

Fields:
* coach: String name of coach ("League Average")
* down: Integer representing the down - [1, 4]
* red_zone: Boolean indicating whether the team is within 20 yards of the opponent's endzone
* distance: String category measuring the distance to the first down marker ("All":[1,99], "Short":[1, 4), "Mid":[4,6], "Long":(6, 99])
* pass_prob: Float representing number of times a play was a pass in a given situation (# of pass plays in given situation / total # of plays in given situation)
* run_prob: Float representing number of times a play was a run in a given situation
* fg_prob: Float representing number of times a play was a field goal in a given situation
* punt_prob: Float representing number of times a play was a punt in a given situation

### playcall_profiles.csv

Description:
Playcalling tendencies by coach, down, distance, and red zone status

Creation:
Run playcall_profiles.R

Fields:
* coach: String name of coach
* down: Integer representing the down - [1, 4]
* red_zone: Boolean indicating whether the team is within 20 yards of the opponent's endzone
* distance: String category measuring the distance to the first down marker ("All":[1,99], "Short":[1, 4), "Mid":[4,6], "Long":(6, 99])
* pass_prob: Float representing number of times a play was a pass in a given situation (# of pass plays in given situation / total # of plays in given situation)
* run_prob: Float representing number of times a play was a run in a given situation
* fg_prob: Float representing number of times a play was a field goal in a given situation
* punt_prob: Float representing number of times a play was a punt in a given situation

### player_ids.csv

Description:
Every NFL player's full name and unique ID

Creation:
Run sim_functions.R, followed by get_player_ids(2025, export=TRUE)

Fields:
* full_name: String name of player (Firstname Lastname)
* gsis_id: Unique ID string for each player (00-00XXXXX)

### rush_pct.csv

Description:
Percentage of team's carries each RB is projected to receive

Creation:
Manually created from Mike Clay's Projections: https://g.espncdn.com/s/ffldraftkit/25/NFLDK2025_CS_ClayProjections2025.pdf?adddata=2025CS_ClayProjections2025

Fields:
* team: String team name abbreviation
* rb_1: Float representing percentage of carries team's RB1 is expected to receive
* rb_2: Float representing percentage of carries team's RB2 is expected to receive

### target_pct.csv

Description:
Percentage of team's targets each player is projected to receive

Creation:
Manually created from Mike Clay's Projections: https://g.espncdn.com/s/ffldraftkit/25/NFLDK2025_CS_ClayProjections2025.pdf?adddata=2025CS_ClayProjections2025

Fields:
* team: String team name abbreviation
* rb_1: Float representing percentage of targets team's RB1 is expected to receive
* rb_2: Float representing percentage of targets team's RB2 is expected to receive
* wr_1: Float representing percentage of targets team's WR1 is expected to receive
* wr_2: Float representing percentage of targets team's WR2 is expected to receive
* wr_3: Float representing percentage of targets team's WR3 is expected to receive
* wr_4: Float representing percentage of targets team's WR4 is expected to receive
* te_1: Float representing percentage of targets team's TE1 is expected to receive
* te_2: Float representing percentage of targets team's TE2 is expected to receive

### teams.csv

Description:
Each team's projected coach and starting depth chart

Creation:
Manually created from Mike Clay's Projections: https://g.espncdn.com/s/ffldraftkit/25/NFLDK2025_CS_ClayProjections2025.pdf?adddata=2025CS_ClayProjections2025

Fields:
* team: String team name abbreviation
* rb_1: String name of team's starting running back (RB1)
* rb_2: String name of team's backup running back (RB2)
* wr_1: String name of team's WR1
* wr_2: String name of team's WR1
* wr_3: String name of team's WR1
* wr_4: String name of team's WR1
* te_1: String name of team's WR1
* te_2: String name of team's WR1