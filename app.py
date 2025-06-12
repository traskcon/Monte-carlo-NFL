import plotly.express as px
from shiny import App, ui, reactive, render
from shinywidgets import render_plotly, output_widget
import pandas as pd
import numpy as np
from monte_carlo import Monte_Carlo_Sim

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

app_ui = ui.page_fluid(
    ui.navset_tab(
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
                        choices=["BUFvBAL","CHIvMIN","LACvKC","PHIvDAL"],
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
        ui.nav_panel("Sim",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Home"),
                    ui.output_image("home_image", fill=False),
                    ui.input_selectize(
                        "home_team",
                        "Home Team",
                        choices = team_names
                    )
                ),
                ui.card(
                    ui.card_header(""),
                    ui.input_numeric("n", "Number of Games:", 1000, min=1, max=100000),
                    ui.output_text("time_estimate"),
                    ui.input_action_button("run", "Run")
                ),
                ui.card(
                    ui.card_header("Away"),
                    ui.output_image("away_image", fill=True),
                    ui.input_selectize(
                        "away_team",
                        "Away Team",
                        choices = team_names,
                        selected="Washington Commanders"
                    )
                ),
                col_widths=(5,2,5)
            )
        ),
    id="tab",
    )
)

def server(input, output, session):

    @reactive.event(input.run)
    def scores():
        sim.run_simulations(input.home_team(), input.away_team(), input.n())

    @render.text
    def time_estimate():
        return "Estimated Simulation Time: {:.2f} minutes".format(input.n()/(6*60))

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