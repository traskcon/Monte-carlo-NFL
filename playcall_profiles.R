# Import Necessary Libraries
library(nflverse)
library(tidyverse)

# Load Data from NFLverse
coaches <- nflseedR::load_schedules(2025) |>
  select(home_coach) |>
  distinct()
games <- nflfastR::load_pbp(2007:2024) |>
  select(season, posteam_type, yardline_100, down, ydstogo, play_type, home_coach, away_coach) |>
  filter(play_type %in% c("run","pass","punt","field_goal")) |>
  mutate(pos_coach = ifelse(posteam_type == "home", home_coach, away_coach), .keep="unused") |>
  mutate(red_zone = ifelse(yardline_100 > 20, F, T))

# Define Functions
get_freq_vector <- function(vec, frequencies) {
  for (type in c("pass","run","field_goal","punt")) {
    play_freq <- subset(frequencies, play_type == type)
    vec <- append(vec, max(play_freq[["freq"]], 0))
  }
  return(vec)
}

calc_frequencies <- function(pbp, distance="All", short=4, long=6) {
  if (distance == "Short") {
    pbp <- filter(pbp, ydstogo < short)
  } else if (distance == "Long") {
    pbp <- filter(pbp, ydstogo > long)
  } else if (distance == "Mid") {
    pbp <- filter(pbp, between(ydstogo, short, long))
  }
  frequencies <- pbp |>
    count(play_type) |>
    mutate(freq = n/sum(n), .keep="unused")
  return(frequencies)
}

# create empty dataframe for storing coach playcalling tendencies
profiles <- data.frame(
  coach = character(), down = integer(), red_zone = logical(), distance = integer(),
  pass_prob = double(), run_prob = double(), fg_prob = double(), punt_prob = double()
)

# calculate every 2025 coach's playcalling tendencies
i = 1
for (hc in coaches[["home_coach"]]) {
  coach_games <- games |>
    filter(pos_coach == hc)
  for (dwn in 1:4) {
    coach_down <- coach_games |>
      filter(down == dwn)
    for (rz in c(T,F)) {
      coach_rz <- coach_down |>
        filter(red_zone == rz)
      if (dwn == 1) {
        vec <- c(hc, dwn, rz, "All")
        frequencies <- calc_frequencies(coach_rz)
        profiles[i, ] <- get_freq_vector(vec, frequencies)
        i = i + 1
      } else {
        for (distance in c("Short","Mid","Long")) {
          vec <- c(hc, dwn, rz, distance)
          frequencies <- calc_frequencies(coach_rz, distance)
          profiles[i, ] <- get_freq_vector(vec, frequencies)
          i = i + 1
        }
      } 
    }
  }
}

# Add code to export profiles to csv
write.csv(profiles, "./data/playcall_profiles.csv")