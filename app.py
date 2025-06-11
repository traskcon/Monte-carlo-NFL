import plotly.express as px
from shiny import App, ui, reactive
from shinywidgets import render_plotly, output_widget
import pandas as pd
import numpy as np

def load_game(home, away):
    game_str = "./results/" + home + "v" + away + "stats.csv"
    return pd.read_csv(game_str, header=[0,1], index_col=0)

test_df = load_game("PHI", "DAL")
players = pd.unique(test_df.columns.get_level_values(1))

app_ui = ui.page_sidebar(
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
        )
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Stats"),
            output_widget("stat_hist"),
            full_screen=True
        )
    )
)

def server(input, output, session):
    
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