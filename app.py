from dash import Dash, html
import pandas as pd

app = Dash()

app.layout = [html.Div(children="Hello World")]

if __name__ == "__main__":
    app.run(debug=True)