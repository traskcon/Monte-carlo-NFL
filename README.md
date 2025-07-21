# Monte-carlo-NFL
Play-by-play simulations of NFL matchups

### Time Test
* Single Game Simulation (verbose=True): 0.1868s
* Single Game Simulation (verbose=False): 0.1309s

Serial vs Parallel:
* 100 Games: 17.04s (Serial), 12.05s (Parallel, 8 cores)
* 1,000 Games: 171.42s (Serial), 27.22s (Parallel, 8 cores)
* 10,000 Games: ~27 minutes (Serial), 234.95s (Parallel, 8 cores)

Back of napkin estimates place the number of simulations required to achieve a robust estimate at 10,000 - 100,000 depending on confidence level and score range

## TODO
* Add Documentation for existing sim capabilities
    * Function descriptions/comments as well as high-level overview
* Write-up proper README
* Add Home/description page to shiny app
* Add link to github and youtube channel to top right
* Additional Visualization options
* Additional Sim capabilities
* Data selection/player attribute modification abilities
* Improve defensive and OL modeling

## Current Limitations
* Limited defensive modeling
    * Historical passing yards allowed and rushing yards allowed are only defensive stats
    * No player-level defensive data/simulation
    * No fumbles or sacks
    * As a result, games are slightly offensively biased and assume no defensive changes from 2024 to 2025
* Only using a single season's worth of player data (2024)
    * Relatively straightforward to add additional historical data
        * However doing this naively would introduce issues of data drift (player improvement/regression)
        * Likely have to weight data by recency
* Static coaching decisions
    * Current model captures playcalling tendencies by down, distance, and red zone
    * Lacks ability to adjust based on game clock 
* Static game length
    * All games are 124 snaps long (league average) and there is no game clock
        * As a result, there is no halftime possession switch or clock-informed coaching decisions
        * No hurry-up, 2-minute drill, 4-minute offense, etc.
* No injury modeling
    * Injury probabilities within a given game are assumed to be rare
    * Game-to-game injuries can be simulated by changing the team's depth chart
* Static depth charts
    * Play time based on Mike Clay projections, cutting off at RB2, WR4, and TE2
    * Assumes players beyond these cutoffs do not significantly factor into the team's offensive performance
* No Kick Returns
* Limited offensive line modeling
    * No player-level offensive line data
    * OL has no effect on pass game
    * OL has minimal effect on run game