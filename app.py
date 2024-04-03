#pergunta 1
import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
import re

# Carregar os dados
df = pd.read_csv("https://raw.githubusercontent.com/bryanthebem/plot_gustavo/main/1%20-%20Base%20de%20Dados.csv")

# Remover caracteres não numéricos e converter para float
df['Valor_Produto'] = df['Valor_Produto'].apply(lambda x: float(re.sub(r'[^\d.]', '', x)))
df['Valor_Total_Venda'] = df['Valor_Total_Venda'].apply(lambda x: float(re.sub(r'[^\d.]', '', x)))

# Calcular Total de Vendas por Regional
vendas_por_regional = df.groupby('Regional')['Valor_Total_Venda'].sum().reset_index()

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Desempenho de Vendas - 2020"),
    
    # Gráfico: Total de Vendas por Mês
    dcc.Graph(id='vendas-por-mes', figure=px.line(df, x='Data_Pedido', y='Valor_Total_Venda', 
                                                   title='Total de Vendas por Mês')),
    
    # Gráfico: Total de Vendas por Representante
    dcc.Graph(id='vendas-por-representante', figure=px.bar(df, x='Nome_Representante', 
                                                           y='Valor_Total_Venda', 
                                                           title='Total de Vendas por Representante')),
    
    # Tabela: Total de Vendas por Produto
    html.H2("Total de Vendas por Produto"),
    dcc.Graph(id='vendas-por-produto', figure=px.bar(df, x='Nome_Produto', 
                                                     y='Quantidade_Vendida', 
                                                     title='Total de Vendas por Produto')),
    
    # Gráfico: Total de Vendas por Regional
    html.H2("Total de Vendas por Regional"),
    dcc.Graph(id='vendas-por-regional', figure=px.pie(vendas_por_regional, 
                                                      values='Valor_Total_Venda', 
                                                      names='Regional', 
                                                      title='Total de Vendas por Regional')),
    
    # Gráfico: Total de Vendas por Estado
    dcc.Graph(id='vendas-por-estado', figure=px.bar(df, x='Estado_Cliente', 
                                                    y='Valor_Total_Venda', 
                                                    title='Total de Vendas por Estado')),
])

# Executar o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)


# Pergunta 2
import pandas as pd
import dash
from dash import html, dcc, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
import re

# Carregar os dados
df = pd.read_csv('1 - Base de Dados.csv')

# Remover caracteres não numéricos e converter para float
df['Valor_Produto'] = df['Valor_Produto'].apply(lambda x: float(re.sub(r'[^\d.]', '', x)))
df['Valor_Total_Venda'] = df['Valor_Total_Venda'].apply(lambda x: float(re.sub(r'[^\d.]', '', x)))

# Calcular Total de Vendas por Regional
vendas_por_regional = df.groupby('Regional')['Valor_Total_Venda'].sum().reset_index()

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Desempenho de Vendas - 2020"),
    
    # Dropdown: Filtro por Mês
    html.Label('Filtrar por Mês:'),
    dcc.Dropdown(
        id='filtro-mes',
        options=[{'label': mes, 'value': mes} for mes in df['Data_Pedido'].str.split('-', expand=True)[1].unique()],
        multi=True,
        value=df['Data_Pedido'].str.split('-', expand=True)[1].unique()
    ),
    
    # Gráfico: Total de Vendas por Mês
    dcc.Graph(id='vendas-por-mes'),
    
    # Dropdown: Filtro por Representante
    html.Label('Filtrar por Representante:'),
    dcc.Dropdown(
        id='filtro-representante',
        options=[{'label': rep, 'value': rep} for rep in df['Nome_Representante'].unique()],
        multi=True,
        value=df['Nome_Representante'].unique()
    ),
    
    # Gráfico: Total de Vendas por Representante
    dcc.Graph(id='vendas-por-representante'),
    
    # Dropdown: Filtro por Regional
    html.Label('Filtrar por Regional:'),
    dcc.Dropdown(
        id='filtro-regional',
        options=[{'label': reg, 'value': reg} for reg in df['Regional'].unique()],
        multi=True,
        value=df['Regional'].unique()
    ),
    
    # Gráfico: Total de Vendas por Regional
    dcc.Graph(id='vendas-por-regional'),
])

# Callback para atualizar o gráfico de vendas por mês
@app.callback(
    Output('vendas-por-mes', 'figure'),
    [Input('filtro-mes', 'value')]
)
def update_graph_mes(selected_mes):
    filtered_df = df[df['Data_Pedido'].str.split('-', expand=True)[1].isin(selected_mes)]
    fig = px.line(filtered_df, x='Data_Pedido', y='Valor_Total_Venda', title='Total de Vendas por Mês')
    return fig

# Callback para atualizar o gráfico de vendas por representante
@app.callback(
    Output('vendas-por-representante', 'figure'),
    [Input('filtro-representante', 'value')]
)
def update_graph_representante(selected_representante):
    filtered_df = df[df['Nome_Representante'].isin(selected_representante)]
    fig = px.bar(filtered_df, x='Nome_Representante', y='Valor_Total_Venda', title='Total de Vendas por Representante')
    return fig

# Callback para atualizar o gráfico de vendas por regional
@app.callback(
    Output('vendas-por-regional', 'figure'),
    [Input('filtro-regional', 'value')]
)
def update_graph_regional(selected_regional):
    filtered_df = df[df['Regional'].isin(selected_regional)]
    vendas_por_regional = filtered_df.groupby('Regional')['Valor_Total_Venda'].sum().reset_index()
    fig = px.pie(vendas_por_regional, values='Valor_Total_Venda', names='Regional', title='Total de Vendas por Regional')
    return fig

# Executar o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)

#Pergunta 3

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Desempenho de Vendas - 2020"),
    
    # Dropdown: Filtro por Estado
    html.Label('Filtrar por Estado:'),
    dcc.Dropdown(
        id='filtro-estado',
        options=[{'label': estado, 'value': estado} for estado in df['Estado_Cliente'].unique()],
        multi=False,
        value=None
    ),
    
    # Dropdown: Filtro por Cidade do Cliente
    html.Label('Filtrar por Cidade do Cliente:'),
    dcc.Dropdown(
        id='filtro-cidade',
        multi=False,
        value=None
    ),
    
    # Gráfico: Total de Vendas por Estado e Cidade do Cliente
    dcc.Graph(id='vendas-por-estado-e-cidade'),
])

# Callback para atualizar as opções do filtro de cidade com base no estado selecionado
@app.callback(
    Output('filtro-cidade', 'options'),
    [Input('filtro-estado', 'value')]
)
def update_cidades_options(selected_estado):
    if selected_estado is not None:
        cidades_estado = df[df['Estado_Cliente'] == selected_estado]['Cidade_Cliente'].unique()
        options = [{'label': cidade, 'value': cidade} for cidade in cidades_estado]
        return options
    else:
        return []

# Callback para atualizar o gráfico de vendas por estado e cidade do cliente
@app.callback(
    Output('vendas-por-estado-e-cidade', 'figure'),
    [Input('filtro-estado', 'value'),
     Input('filtro-cidade', 'value')]
)
def update_graph_estado_cidade(selected_estado, selected_cidade):
    filtered_df = df
    if selected_estado is not None:
        filtered_df = filtered_df[filtered_df['Estado_Cliente'] == selected_estado]
    if selected_cidade is not None:
        filtered_df = filtered_df[filtered_df['Cidade_Cliente'] == selected_cidade]
        
    fig = px.bar(filtered_df, x='Estado_Cliente', y='Valor_Total_Venda', 
                 title=f'Total de Vendas por Estado ({selected_estado}) e Cidade do Cliente ({selected_cidade})')
    return fig

# Executar o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
