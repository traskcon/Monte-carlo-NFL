import plotly.express as px
from shiny import App, ui, reactive, render
from shinywidgets import render_plotly, output_widget
import pandas as pd
import numpy as np
from monte_carlo import Monte_Carlo_Sim
from multiprocessing import cpu_count
import os
import json

def get_results(dir_path="./results", suffix="stats.csv"):
    file_names = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,f))]
    game_results = [f.replace(suffix,"") for f in file_names]
    return game_results

def get_saved_scores(dir_path="./results/"):
    scores_file = dir_path + "scores.json"
    game_scores = json.load(open(scores_file, "r")) if os.path.exists(scores_file) else dict()
    return game_scores

sim = Monte_Carlo_Sim()

test_df = pd.read_csv("./results/PHIvDALstats.csv", header=[0,1], index_col=0)
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

                    [How it works, how to use it, etc.]

                    ## Stat Summary

                    [Shows each player's relevant stats after a simulation has been run and stats exported]

                    ## Visualizations

                    [Visualizations of stat distributions across the thousands of simulated games]

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
        ui.nav_panel("Stat Summary"),
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
                )
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
            home_scores.set(home_results)
            away_scores.set(away_results)
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
        #TODO: Develop more accurate simulation time estimates
        return "Estimated Simulation Time: {:.2f} minutes".format(input.n()/(6*60*input.cpus()))

    @render.image
    def home_image():
        source = "./logos/" + input.home_team().replace(" ","_") + ".svg"
        img = {"src": source, "width":"100%"}
        return img
    
    @render.image
    def away_image():
        source = "./logos/" + input.away_team().replace(" ","_") + ".svg"
        img = {"src": source, "width":"100%"}
        return img

    #Update available players when game, stat data changes
    @reactive.effect
    def _():
        players = list(pd.unique(get_game()[input.stat()].columns))
        ui.update_selectize("players", choices=players, selected=players[0])

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

app = App(app_ui, server)