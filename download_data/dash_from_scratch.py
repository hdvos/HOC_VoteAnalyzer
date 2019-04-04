import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

app = dash.Dash()

app.layout = html.Div(children = [
    dcc.Dropdown(
    id='input',
    options=[
        {'label': 'New York City', 'value': 'NYC'},
        {'label': 'Montreal', 'value': 'MTL'},
        {'label': 'San Francisco', 'value': 'SF'}
    ],
    value=['MTL', 'NYC'],
    multi=True
    ),
    html.Div(id='output')
    ])




@app.callback(
    Output(component_id= 'output', component_property='children'),
    [Input(component_id='input', component_property='value')])
def update_value(input_data):
    try:
        return str(input_data)
    except:
        return "Some Error"


if __name__ == "__main__":
    app.run_server(debug=True)