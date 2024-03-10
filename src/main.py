import dash
from dash import dcc, dash_table, html
from dash.dependencies import Input, Output

def main():
    app = dash.Dash(__name__)

    app.scripts.config.serve_locally = True
    app.css.config.serve_locally = True

    def home_page():
        return [
            html.Div(
                children=[html.H1('Bull Bot', style={'margin-left' : '2.22%', 'color' : '#85B79D', 'height' : '100%', 'margin-left' : '5%'})],
                style={'display':'inline-block', 'vertical_align':'left', 'height' : '5%', 'width' : '100%', 'backgroundColor' : '#0F0F0F'}
            )
        ]

    app.layout = html.Div(
        children=home_page(),
        style={'background-image' : 'http://127.0.0.1:8050/assets/gangster_sponge.jpg'},
        id="app"
    )

    app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter


if __name__ == "__main__":
    main()