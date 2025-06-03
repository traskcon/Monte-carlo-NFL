library(nflverse)

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

ggplot(games, aes(x=yards_gained)) + geom_histogram()
write.csv(rushes, "c:/users/geniu/Documents/Monte-carlo-NFL/2024_rushes.csv")
