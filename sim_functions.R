library(nflverse)
library(tidyverse)

get_yardage_data <- function(years, play, export=FALSE) {
  fields <- switch(
    play,
    "run"= c("rusher_player_name","rusher_player_id","posteam","defteam","yards_gained"),
    "pass"= c("receiver_player_name","receiver_player_id","passer_player_name",
              "passer_player_id","complete_pass","air_yards","yards_after_catch",
              "yards_gained","defteam","interception"),
    "field goal"= c("kicker_player_name","kicker_player_id","yardline_100","result"),
    "punt"= c("punter_player_name","punter_player_id","kick_distance"),
    "Invalid play type"
  )
  yard_data <- load_pbp(years) |> filter(play_type == play) |> select(all_of(fields))
  if (play == "run") {
    yard_data <- rename(yard_data, yards_gained_rush = yards_gained)
  } else if (play == "pass") {
    yard_data <- rename(yard_data, yards_gained_pass = yards_gained)
  }
  if (export) {
    write.csv(yard_data, paste0("./data/", play,"_data.csv"))
  } else {
    return(yard_data)
  }
}

get_player_ids <- function(years, export=FALSE) {
  current_rosters <- load_rosters(years) |>
    select(full_name, gsis_id)
  if (export) {
    write.csv(current_rosters, "./data/player_ids.csv")
  } else {
    return(current_rosters)
  }
}