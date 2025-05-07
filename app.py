import pandas as pd
import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

# Carregar o arquivo CSV
df = pd.read_csv('Summer_olympic_Medals.csv')
# Substituir 'United States' por 'Estados Unidos da América' na coluna 'Country_Name'
df['Country_Name'] = df['Country_Name'].replace('United States', 'Estados Unidos da América')

# Filtrar os dados entre 1992 e 2020
df = df[(df['Year'] >= 1992) & (df['Year'] <= 2020)]

# Calcular o total de medalhas para cada país
df['Total_Medals'] = df['Gold'] + df['Silver'] + df['Bronze']


# Funções para gerar os gráficos
def create_map_fig(medal_type='Todas'):
    if medal_type != 'Todas':
        df_country_medals = df.groupby('Country_Name')[medal_type].sum().reset_index()
        color_col = medal_type
    else:
        df_country_medals = df.groupby('Country_Name')['Total_Medals'].sum().reset_index()
        color_col = 'Total_Medals'

    map_fig = px.choropleth(df_country_medals,
                            locations='Country_Name',
                            locationmode='country names',
                            color=color_col,
                            hover_name='Country_Name',
                            color_continuous_scale=px.colors.sequential.YlOrRd,
                            title='Total de Medalhas de 1992 a 2020')
    map_fig.update_layout(title_x=0.5) # Centralizar o título
    return map_fig


def create_area_fig(medal_type='Todas'):
    top_countries = df.groupby('Country_Name')['Total_Medals'].sum().nlargest(10).index
    df_countries = df.groupby(['Country_Name', 'Year'])['Total_Medals'].sum().reset_index()
    df_top_10_countries = df_countries[df_countries['Country_Name'].isin(top_countries)]

    if medal_type != 'Todas':
        area_fig = px.area(df_top_10_countries,
                           x="Year",
                           y=medal_type,
                           color="Country_Name",
                           title=f'Top 10 Países por {medal_type} Medalhas de 1992 a 2020')
    else:
        area_fig = px.area(df_top_10_countries,
                           x="Year",
                           y="Total_Medals",
                           color="Country_Name",
                           title='Top 10 Países por Total de Medalhas de 1992 a 2020')
    area_fig.update_layout(title_x=0.5) # Centralizar o título
    return area_fig


def create_bar_fig(year=None, medal_type='Todas'):
    filtered_df = df[df['Year'] == year] if year else df
    df_top_countries_gold = filtered_df.groupby('Country_Name')[medal_type if medal_type != 'Todas' else 'Gold'].sum().nlargest(
        10).reset_index()
    bar_fig = px.bar(df_top_countries_gold,
                     x='Country_Name',
                     y=medal_type if medal_type != 'Todas' else 'Gold',
                     color_discrete_sequence=['gold'],
                     title=f'Top 10 Países com Mais {medal_type if medal_type != "Todas" else "Ouro"} Medalhas'
                           f' {"de 1992 a 2020" if not year else f"em {year}"}')
    bar_fig.update_layout(title_x=0.5) # Centralizar o título
    return bar_fig


def create_pie_chart(country):
    filtered_df = df[df['Country_Name'] == country]
    medal_counts = filtered_df[['Gold', 'Silver', 'Bronze']].sum()
    fig = px.pie(
        values=medal_counts.values,
        names=medal_counts.index,
        title=f'Distribuição de Medalhas para {country}',
        hole=0.3,
        labels={'Gold': 'Ouro', 'Silver': 'Prata', 'Bronze': 'Bronze'}
    )
    fig.update_layout(title_x=0.5) # Centralizar o título
    return fig


# Criar um aplicativo Dash
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Graph(figure=create_map_fig(), id='map', style={'height': '50vh', 'width': '100%'}),
    html.Div([
        dcc.Graph(figure=create_area_fig(), id='area-chart'),
        dcc.Graph(figure=create_bar_fig(), id='bar-chart')
    ], style={'display': 'flex'}),
    html.Div([
        html.Label('Selecione o País:'),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in df['Country_Name'].unique()],
            value='Estados Unidos da América'
        ),
        dcc.Graph(id='pie-chart')
    ]),
    html.Div([
        html.Label('Selecione o Tipo de Medalha:'),
        dcc.Dropdown(
            id='medal-type-dropdown',
            options=[
                {'label': 'Todas', 'value': 'Todas'},
                {'label': 'Ouro', 'value': 'Gold'},
                {'label': 'Prata', 'value': 'Silver'},
                {'label': 'Bronze', 'value': 'Bronze'}
            ],
            value='Todas'
        )
    ]),
    html.Div([
        html.Label('Selecione o Ano Olímpico:'),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': year, 'value': year} for year in df['Year'].unique()],
            value=df['Year'].min()
        )
    ])
])


# Callbacks para atualizar os gráficos
@app.callback(
    Output('map', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_map(medal_type):
    return create_map_fig(medal_type)


@app.callback(
    Output('area-chart', 'figure'),
    [Input('medal-type-dropdown', 'value')]
)
def update_area_chart(medal_type):
    return create_area_fig(medal_type)


@app.callback(
    Output('bar-chart', 'figure'),
    [Input('year-dropdown', 'value'), Input('medal-type-dropdown', 'value')]
)
def update_bar_chart(year, medal_type):
    return create_bar_fig(year, medal_type)


@app.callback(
    Output('pie-chart', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_pie_chart(country):
    return create_pie_chart(country)


# Executar o aplicativo
if __name__ == '__main__':
    app.run(debug=False)