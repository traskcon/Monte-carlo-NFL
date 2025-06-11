import plotly.express as px
from shiny.express import input, ui
from shinywidgets import render_plotly
import pandas as pd

def load_game(home, away):
    game_str = "./results/" + home + "v" + away + "stats.csv"
    return pd.read_csv(game_str, header=[0,1], index_col=0)

test_df = load_game("PHI", "DAL")

ui.page_opts(title="Monte Carlo Visualizations", fillable=True)

with ui.layout_columns():

    @render_plotly
    def stat_hist():
        return px.histogram(test_df["pass_yards"], x="Jalen Hurts")