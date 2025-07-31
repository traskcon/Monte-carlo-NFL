import plotly.express as px
from shiny import App, ui, reactive, render
from shinywidgets import render_plotly, output_widget
import pandas as pd
import numpy as np
from monte_carlo import Monte_Carlo_Sim
from helper import get_player_stats
from multiprocessing import cpu_count
import os
import json

pd.set_option("display.float_format", "{:.2f}".format)

# Need to make reactive in order to update after users run simulations
def get_results(dir_path="./results", suffix="stats.csv"):
    file_names = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,f))]
    game_results = [f.replace(suffix,"") for f in file_names if suffix in f]
    return game_results

def get_saved_scores(dir_path="./results/"):
    scores_file = dir_path + "scores.json"
    game_scores = json.load(open(scores_file, "r")) if os.path.exists(scores_file) else dict()
    return game_scores

sim = Monte_Carlo_Sim()

test_df = pd.read_csv("./results/BUFvBALstats.csv", header=[0,1], index_col=0)
players = pd.unique(test_df.columns.get_level_values(1))

team_names = ["Arizona Cardinals","Atlanta Falcons","Baltimore Ravens","Buffalo Bills",
              "Carolina Panthers","Chicago Bears","Cincinnati Bengals","Cleveland Browns",
              "Dallas Cowboys","Denver Broncos","Detroit Lions","Green Bay Packers",
              "Houston Texans","Indianapolis Colts","Jacksonville Jaguars","Kansas City Chiefs",
              "Las Vegas Raiders","Los Angeles Chargers","Los Angeles Rams","Miami Dolphins",
              "Minnesota Vikings","New England Patriots","New Orleans Saints","New York Giants",
              "New York Jets","Philadelphia Eagles","Pittsburgh Steelers","San Francisco 49ers",
              "Seattle Seahawks","Tampa Bay Buccaneers","Tennessee Titans","Washington Commanders"]

team_dict = {"Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL",
             "Buffalo Bills":"BUF","Carolina Panthers":"CAR","Chicago Bears":"CHI",
             "Cincinnati Bengals":"CIN","Cleveland Browns":"CLE","Dallas Cowboys":"DAL",
             "Denver Broncos":"DEN","Detroit Lions":"DET","Green Bay Packers":"GB",
              "Houston Texans":"HOU","Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX",
              "Kansas City Chiefs":"KC","Las Vegas Raiders":"LV","Los Angeles Chargers":"LAC",
              "Los Angeles Rams":"LAR","Miami Dolphins":"MIA","Minnesota Vikings":"MIN",
              "New England Patriots":"NE","New Orleans Saints":"NO","New York Giants":"NYG",
              "New York Jets":"NYJ","Philadelphia Eagles":"PHI","Pittsburgh Steelers":"PIT",
              "San Francisco 49ers":"SF","Seattle Seahawks":"SEA","Tampa Bay Buccaneers":"TB",
              "Tennessee Titans":"TEN","Washington Commanders":"WAS"}

app_ui = ui.page_fluid(
    ui.navset_tab(
        ui.nav_panel("Introduction",
            ui.card(
                ui.card_header("Introduction"),
                ui.markdown(
                    '''
                    # Monte Carlo NFL Simulations

                    Welcome! This is an app for simulating thousands of NFL games at a play-by-play level.
                    Detailed information on each tab below:

                    ## Sim

                    The heart of this simulation capability, this tab is where users can specify and run simulations.
                    Home and Away teams are selected from their respective dropdown menus (NOTE: Currently there is no homefield advantage in the simulation).
                    Users can also specify how many times the matchup should be simulated and how many CPU cores to allocate to the simulation.
                    Additionally, if one wants to analyze the player stats for a given matchup, the "Export Stats" button should be selected.
                    Once ready, press Run and the simulation will start running, returning the average scores of each team when complete.

                    ## Stat Summary

                    Because this simulation models player-level actions, the resulting player stats from each matchup can be tabulated and returned.
                    These are exported in a [Home]v[Away]stats.csv file to the ./results folder.
                    The Stat Summary tab reads any stats files currently in the ./results folder and displays the average stats for each player.

                    ## Visualizations

                    While the Stat Summary tab provides a clean overview of every players stats for a given game, sometimes additional detail is desired.
                    The Visualizations tab shows the full distribution of player stats generated during simulation.

                    '''
                )
            )),
        ui.nav_panel("Sim",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Home"),
                    ui.input_selectize(
                        "home_team",
                        "Home Team",
                        choices = team_names
                    ),
                    ui.output_image("home_image", fill=True, width="90%"),
                    ui.output_text("home_score")
                ),
                ui.card(
                    ui.card_header(""),
                    ui.input_numeric("n", "Number of Games:", 1000, min=1, max=100000),
                    ui.output_text("time_estimate"),
                    ui.input_checkbox("stats","Export Stats"),
                    ui.input_slider("cpus", "CPUs to Use:", min=1, max=cpu_count(), value=1),
                    ui.input_action_button("run", "Run")
                ),
                ui.card(
                    ui.card_header("Away"),
                    ui.input_selectize(
                        "away_team",
                        "Away Team",
                        choices = team_names,
                        selected="Washington Commanders"
                    ),
                    ui.output_image("away_image", fill=True, width="90%"),
                    ui.output_text("away_score")
                ),
                col_widths=(5,2,5), height="90vh"
            )
        ),
        ui.nav_panel("Stat Summary",
            ui.layout_columns(
                ui.input_selectize(
                        "game_stats",
                        "Select Matchup",
                        choices=get_results()
                ),
                ui.input_action_button(
                    "refresh_stats",
                    "Refresh Stats"
                ),
                ui.card(
                    ui.card_header("Home"),
                    ui.output_table("home_stats")
                ),
                ui.card(
                    ui.card_header("Away"),
                    ui.output_table("away_stats")
                ),
                col_widths=(-2,4,4,-2,6,6),
                row_heights=("10vh", "80vh")
            )),
        ui.nav_panel("Visualizations",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_selectize(
                        "players",
                        "Select Player",
                        choices=list(players),
                        selected="Jalen Hurts"
                    ),
                    ui.input_selectize(
                        "stat",
                        "Select Stat",
                        choices={"pass_yards":"Pass Yards", "rec_yards":"Rec Yards", "rush_yards":"Rush Yards"},
                        selected="pass_yards"
                    ),
                    ui.input_selectize(
                        "game",
                        "Select Matchup",
                        choices=get_results(),
                        selected="PHIvDAL"
                    ),
                    position="left"
                ),
                ui.card(
                    ui.card_header("Stats"),
                    output_widget("stat_hist"),
                    full_screen=True
                ), height="90vh"
            )
        ),
    id="tab",
    )
)

def server(input, output, session):
    home_scores = reactive.value([0])
    away_scores = reactive.value([0])

    @reactive.effect()
    @reactive.event(input.run)
    def get_scores():
        home, away = team_dict[input.home_team()], team_dict[input.away_team()]
        game_results = get_saved_scores()
        with ui.Progress(min=1, max=input.n()) as p:
            p.set(message="Simulating Games")
            home_results, away_results = sim.parallel_sim(home, away, input.n(), cpu_count=input.cpus(), progress=p)
            home_scores.set(list(home_results))
            away_scores.set(list(away_results))
            game_results[home+"v"+away] = [home_results, away_results]
            with open("./results/scores.json", "w") as f:
                json.dump(game_results, f)
            if input.stats():
                sim.export_stats(home, away)

    @render.text
    def home_score():
        return "Home Score: {:.0f}".format(np.mean(home_scores.get()))
    
    @render.text
    def away_score():
        return "Away Score: {:.0f}".format(np.mean(away_scores.get()))

    @render.text
    def time_estimate():
        #Empirically derived time estimate
        time = (input.n()*(0.161-0.05646*np.log(input.cpus()))+5.1)/60
        return "Estimated Simulation Time: {:.2f} minutes".format(time)

    @render.image #type: ignore
    def home_image():
        source = "./logos/" + input.home_team().replace(" ","_") + ".svg"
        img = {"src": source, "width":"100%"}
        return img
    
    @render.image #type: ignore
    def away_image():
        source = "./logos/" + input.away_team().replace(" ","_") + ".svg"
        img = {"src": source, "width":"100%"}
        return img

    #Update available players when game, stat data changes
    @reactive.effect
    def _():
        players = list(pd.unique(get_game()[input.stat()].columns))
        ui.update_selectize("players", choices=players, selected=players[0])
 
    @reactive.effect
    @reactive.event(input.refresh_stats)
    def _update():
        games = get_results()
        ui.update_selectize("game", choices=games)
        ui.update_selectize("game_stats", choices=games)

    # Read game data
    @reactive.calc
    def get_game():
        game = input.game()
        game_str = "./results/" + game + "stats.csv"
        return pd.read_csv(game_str, header=[0,1], index_col=0)

    @render_plotly
    def stat_hist():
        data = get_game()[input.stat()]
        average = np.mean(data[input.players()])
        fig = px.histogram(data, x=input.players())
        fig.add_vline(x=average, line_color="red",
                      annotation_text="Average: {:.1f} yards".format(average),
                      annotation_position="top right")
        return fig
    
    @render.table
    def home_stats():
        matchup = input.game_stats()
        team = matchup.split("v")[0]
        return get_player_stats(team, matchup)
    
    @render.table
    def away_stats():
        matchup = input.game_stats()
        team = matchup.split("v")[1]
        return get_player_stats(team, matchup)

app = App(app_ui, server)