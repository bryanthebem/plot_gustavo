import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Carregar o arquivo CSV
df = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Summer_olympic_Medals.csv')
# Substituir 'United States' por 'Estados Unidos da América' na coluna 'Country_Name'
df['Country_Name'] = df['Country_Name'].replace('United States', 'Estados Unidos da América')

# Filtrar os dados entre 1992 e 2020
df = df[(df['Year'] >= 1992) & (df['Year'] <= 2020)].copy() # Usar .copy() para evitar SettingWithCopyWarning

# Calcular o total de medalhas para cada país
df['Total_Medals'] = df['Gold'] + df['Silver'] + df['Bronze']

# Preparar opções para o dropdown de Ano Olímpico (com país sede)
year_host_map = df.groupby('Year')['Host_country'].first().reset_index()
year_host_map.sort_values('Year', ascending=False, inplace=True)
year_options_for_dropdown = [{'label': f"{row['Year']} ({row['Host_country']})", 'value': row['Year']}
                             for index, row in year_host_map.iterrows()]
default_year = year_host_map['Year'].max() if not year_host_map.empty else None


# Funções para gerar os gráficos
def create_map_fig(medal_type='Todas'):
    if medal_type != 'Todas':
        df_country_medals = df.groupby('Country_Name')[medal_type].sum().reset_index()
        color_col = medal_type
        title_text = f'Total de Medalhas de {medal_type.lower()} por País (1992-2020)'
    else:
        df_country_medals = df.groupby('Country_Name')['Total_Medals'].sum().reset_index()
        color_col = 'Total_Medals'
        title_text = 'Total Geral de Medalhas por País (1992-2020)'

    map_fig = px.choropleth(df_country_medals,
                            locations='Country_Name',
                            locationmode='country names',
                            color=color_col,
                            hover_name='Country_Name',
                            color_continuous_scale=px.colors.sequential.YlOrRd,
                            title=title_text,
                            labels={color_col: 'Medalhas'})
    map_fig.update_layout(title_x=0.5)
    return map_fig


def create_area_fig(medal_type='Todas'):
    y_column = medal_type if medal_type != 'Todas' else 'Total_Medals'
    title_medal_desc = medal_type.lower() if medal_type != 'Todas' else 'total de'

    # Determinar os top 10 países com base no tipo de medalha selecionado
    top_countries_names = df.groupby('Country_Name')[y_column].sum().nlargest(10).index
    df_filtered_top_countries = df[df['Country_Name'].isin(top_countries_names)]

    # Agrupar dados para o gráfico de área
    df_plot = df_filtered_top_countries.groupby(['Country_Name', 'Year'])[y_column].sum().reset_index()

    area_fig = px.area(df_plot,
                       x="Year",
                       y=y_column,
                       color="Country_Name",
                       title=f'Top 10 Países por {title_medal_desc} Medalhas (1992-2020)',
                       labels={y_column: f'{title_medal_desc.capitalize()} Medalhas', 'Year': 'Ano'})
    area_fig.update_layout(title_x=0.5)
    return area_fig


def create_bar_fig(year=None, medal_type='Todas'):
    temp_df = df.copy()
    fig_title_year_part = "(1992-2020)"
    host_country_name = ""

    if year:
        temp_df = temp_df[temp_df['Year'] == year]
        host_info = year_host_map[year_host_map['Year'] == year]
        if not host_info.empty:
            host_country_name = host_info['Host_country'].iloc[0]
            fig_title_year_part = f"em {year} ({host_country_name})"

    y_column = medal_type
    title_medal_desc = medal_type.lower()
    bar_color = None

    if medal_type == 'Todas':
        y_column = 'Total_Medals'
        title_medal_desc = 'total de'
    elif medal_type == 'Gold':
        bar_color = 'gold'
    elif medal_type == 'Silver':
        bar_color = 'silver'
    elif medal_type == 'Bronze':
        bar_color = '#CD7F32'  # Cor para bronze

    medal_summary_by_country = temp_df.groupby('Country_Name')[['Gold', 'Silver', 'Bronze', 'Total_Medals']].sum()
    top_10_data = medal_summary_by_country.nlargest(10, y_column).reset_index()

    bar_fig = px.bar(top_10_data,
                     x='Country_Name',
                     y=y_column,
                     title=f'Top 10 Países por {title_medal_desc} Medalhas {fig_title_year_part}',
                     labels={y_column: f'{title_medal_desc.capitalize()} Medalhas', 'Country_Name': 'País'})

    if bar_color:
        bar_fig.update_traces(marker_color=bar_color)
    
    bar_fig.update_layout(title_x=0.5)
    return bar_fig


def create_pie_chart(country):
    filtered_df = df[df['Country_Name'] == country]
    # Somar medalhas ao longo de todos os anos para o país selecionado
    medal_counts = filtered_df[['Gold', 'Silver', 'Bronze']].sum()
    
    # Lidar com o caso de não haver medalhas ou país não encontrado (embora o dropdown deva prevenir isso)
    if medal_counts.sum() == 0:
        return px.pie(title=f'Nenhuma medalha encontrada para {country} (1992-2020)').update_layout(title_x=0.5)

    fig = px.pie(
        values=medal_counts.values,
        names=medal_counts.index,
        title=f'Distribuição de Medalhas para {country} (1992-2020)',
        hole=0.3,
        color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': '#CD7F32'}
    )
    fig.update_layout(title_x=0.5)
    return fig


# Criar um aplicativo Dash
app = dash.Dash(__name__)
server = app.server # Para deploy no Gunicorn/Heroku etc.

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1("Dashboard de Medalhas Olímpicas (1992-2020)", style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Label('Selecione o Tipo de Medalha para os gráficos principais:', style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='medal-type-dropdown',
            options=[
                {'label': 'Todas', 'value': 'Todas'},
                {'label': 'Ouro', 'value': 'Gold'},
                {'label': 'Prata', 'value': 'Silver'},
                {'label': 'Bronze', 'value': 'Bronze'}
            ],
            value='Todas',
            clearable=False,
            style={'width': '200px', 'display': 'inline-block'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '30px'}),

    dcc.Graph(
        id='map',
        figure=create_map_fig(), # Figura inicial
        style={'height': '60vh', 'width': '100%', 'marginBottom': '30px'}
    ),

    html.Div([
        html.Div([
            dcc.Graph(id='area-chart', figure=create_area_fig()) # Figura inicial
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '1%'}),

        html.Div([
            html.Label('Selecione o Ano Olímpico (País Sede):'),
            dcc.Dropdown(
                id='year-dropdown',
                options=year_options_for_dropdown,
                value=default_year, # Padrão para o ano mais recente
                clearable=False,
                style={'marginBottom': '10px'}
            ),
            dcc.Graph(id='bar-chart', figure=create_bar_fig(year=default_year)) # Figura inicial
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '1%'})

    ], style={'display': 'flex', 'marginBottom': '30px'}),

    html.Div([
        html.H3("Detalhes de Medalhas por País", style={'textAlign': 'center', 'marginTop': '20px'}),
        html.Label('Selecione o País:', style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in sorted(df['Country_Name'].unique())],
            value='Estados Unidos da América', # Padrão
            clearable=False,
            style={'width': '300px', 'display': 'inline-block', 'marginBottom': '10px'}
        ),
        dcc.Graph(id='pie-chart', figure=create_pie_chart('Estados Unidos da América')) # Figura inicial
    ], style={'width': '70%', 'margin': 'auto', 'textAlign': 'center', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px'})
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
    [Input('year-dropdown', 'value'),
     Input('medal-type-dropdown', 'value')]
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
    app.run_server(debug=True)
