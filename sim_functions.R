library(nflverse)
library(tidyverse)

monte_carlo_model <- function(team, games, week_num, ...) {
  # Simulation model must create result column where result is number of points 
  # home team won by
  games <- games |>
    mutate(result = )
  list(teams = teams, games = games)
}

rushes <- load_pbp(2024) |>
  filter(play_type == "run") |>
  mutate(pos_team = ifelse(posteam_type == "home", home_team, away_team)) |>
  mutate(def_team = ifelse(posteam_type == "home", away_team, home_team)) |>
  select(rusher_player_name, rusher_player_id, pos_team, def_team, yards_gained)

current_rosters <- load_rosters(2025) |>
  select(full_name, gsis_id)

punts <- read.csv("c:/users/ctrask/Documents/Monte-carlo-NFL/punts.csv")
ggplot(punts, aes(x=kick_distance)) + geom_histogram()
write.csv(rushes, "c:/users/geniu/Documents/Monte-carlo-NFL/2024_passes.csv")

passes <- load_pbp(2024) |>
  filter(play_type == "pass") |>
  select(receiver_player_name, receiver_player_id, passer_player_name, 
         passer_player_id, complete_pass, air_yards, yards_after_catch)