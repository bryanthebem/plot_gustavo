import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np

# Constantes para filtros "Todos"
ALL_VALUES = "TODOS"

# Carregamento e pré-processamento dos dados
def load_data():
    """
    Carrega todos os arquivos CSV, unifica os dados de vendas,
    clientes e realiza os merges necessários.
    """
    try:
        # Carregar arquivos de cadastro
        df_produtos = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Cadastro%20Produtos.csv', encoding='utf-8')
        df_lojas = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Cadastro%20Lojas.csv', encoding='utf-8')
        df_clientes = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Cadastro%20Clientes.csv', encoding='utf-8')

        # Carregar arquivos de vendas
        df_vendas_2020 = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Base%20Vendas%20-%202020.csv', encoding='utf-8')
        df_vendas_2021 = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Base%20Vendas%20-%202021.csv', encoding='utf-8')
        df_vendas_2022 = pd.read_csv('https://raw.githubusercontent.com/bryanthebem/plot_gustavo/refs/heads/main/Base%20Vendas%20-%202022.csv', encoding='utf-8')
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado. Verifique se os CSVs estão no diretório correto. Detalhe: {e}")
        return pd.DataFrame() # Retorna DataFrame vazio em caso de erro

    # Unificar colunas Nome e Sobrenome em Clientes
    df_clientes['Nome Completo'] = df_clientes['Primeiro Nome'] + ' ' + df_clientes['Sobrenome']

    # Unificar tabelas de vendas
    df_vendas_total = pd.concat([df_vendas_2020, df_vendas_2021, df_vendas_2022], ignore_index=True)

    # Converter 'Data da Venda' para datetime e extrair Ano e Mês-Ano
    df_vendas_total['Data da Venda'] = pd.to_datetime(df_vendas_total['Data da Venda'], dayfirst=True, errors='coerce')
    df_vendas_total['Ano da Venda'] = df_vendas_total['Data da Venda'].dt.year
    df_vendas_total['MesAno da Venda'] = df_vendas_total['Data da Venda'].dt.to_period('M').astype(str)


    # Merge das tabelas
    # Vendas com Clientes
    df_merged = pd.merge(df_vendas_total, df_clientes, on='ID Cliente', how='left')
    # Vendas com Produtos
    df_merged = pd.merge(df_merged, df_produtos, on='SKU', how='left')
    # Vendas com Lojas
    df_merged = pd.merge(df_merged, df_lojas, on='ID Loja', how='left')

    # Tratar possíveis NAs após o merge (especialmente se houver IDs não correspondentes)
    # Para colunas usadas em cálculos ou agrupamentos, preencher com valores neutros ou remover
    df_merged['Preço Unitario'] = pd.to_numeric(df_merged['Preço Unitario'], errors='coerce').fillna(0)
    df_merged['Qtd Vendida'] = pd.to_numeric(df_merged['Qtd Vendida'], errors='coerce').fillna(0)

    # Calcular Receita
    df_merged['Receita'] = df_merged['Qtd Vendida'] * df_merged['Preço Unitario']
    
    # Remover linhas onde 'Data da Venda' não pôde ser convertida (se houver)
    df_merged.dropna(subset=['Data da Venda'], inplace=True)

    # Garantir que colunas categóricas usadas em filtros não tenham NaNs (substituir por string 'Desconhecido')
    cols_to_fill_na = ['Produto', 'Nome da Loja', 'Nome Completo', 'Marca', 'Tipo do Produto']
    for col in cols_to_fill_na:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna('Desconhecido')
        else:
            print(f"Aviso: Coluna {col} não encontrada no DataFrame final após merges.")
    return df_merged

# Carregar os dados globalmente para serem usados nas callbacks
df_global = load_data()

# Inicializar o aplicativo Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Para implantação no Render

# Helper function to generate dropdown options
def get_dropdown_options(df, column_name, add_all_values_option=True):
    """
    Generates a list of options for a dcc.Dropdown.
    
    Args:
        df (pd.DataFrame): The DataFrame to get unique values from.
        column_name (str): The name of the column.
        add_all_values_option (bool): Whether to add an 'ALL_VALUES' option at the beginning.
        
    Returns:
        list: A list of dictionaries formatted for dcc.Dropdown options.
    """
    options = []
    if add_all_values_option:
        options.append({'label': ALL_VALUES, 'value': ALL_VALUES})
    
    if not df.empty and column_name in df.columns:
        unique_values = sorted(df[column_name].dropna().unique())
        options.extend([{'label': str(i), 'value': str(i)} for i in unique_values])
    return options


# --- Layout do Dashboard ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("Dashboard de Vendas Interativo", style={'textAlign': 'center', 'color': '#007BFF', 'marginBottom': '30px'}),

    # --- Seção de Filtros Globais ---
    html.Div(className="global-filters-container", style={'marginBottom': '40px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'backgroundColor': '#f9f9f9'}, children=[
        html.H3("Filtros Globais", style={'marginTop': '0', 'marginBottom': '20px', 'color': '#333'}),
        html.Div(className="filters-row", style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}, children=[
            html.Div(style={'flex': '1 1 180px'}, children=[
                html.Label("Produto:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-produto',
                    options=get_dropdown_options(df_global, 'Produto'),
                    value=ALL_VALUES,
                    multi=True, 
                    placeholder="Selecione Produtos"
                )
            ]),
            html.Div(style={'flex': '1 1 180px'}, children=[
                html.Label("Loja:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-loja',
                    options=get_dropdown_options(df_global, 'Nome da Loja'),
                    value=ALL_VALUES,
                    multi=True,
                    placeholder="Selecione Lojas"
                )
            ]),
            html.Div(style={'flex': '1 1 180px'}, children=[
                html.Label("Cliente:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-cliente',
                    options=get_dropdown_options(df_global, 'Nome Completo'),
                    value=ALL_VALUES,
                    multi=True,
                    placeholder="Selecione Clientes"
                )
            ]),
            html.Div(style={'flex': '1 1 180px'}, children=[
                html.Label("Marca do Produto:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-marca',
                    options=get_dropdown_options(df_global, 'Marca'),
                    value=ALL_VALUES,
                    multi=True,
                    placeholder="Selecione Marcas"
                )
            ]),
            html.Div(style={'flex': '1 1 180px'}, children=[
                html.Label("Tipo do Produto:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-tipo-produto',
                    options=get_dropdown_options(df_global, 'Tipo do Produto'),
                    value=ALL_VALUES,
                    multi=True,
                    placeholder="Selecione Tipos"
                )
            ]),
        ])
    ]),

    # --- Seção dos 6 Gráficos Principais ---
    html.Div(className="charts-grid", style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(400px, 1fr))', 'gap': '20px'}, children=[
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Receita Total por Ano", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-receita-ano')
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Top 10 Clientes por Receita", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-top-clientes')
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Top 10 Produtos por Receita", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-top-produtos')
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Distribuição de Receita por Loja", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-receita-loja')
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Receita por Tipo de Produto (Mensal)", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-receita-tipo-produto-tempo')
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
            html.H4("Resumo de Vendas por Marca", style={'textAlign': 'center'}),
            dash_table.DataTable(
                id='table-vendas-marca',
                columns=[], 
                data=[],    
                style_table={'overflowX': 'auto', 'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px', 'minWidth': '100px', 'width': '150px', 'maxWidth': '200px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                page_size=10,
            )
        ]),
    ]),

    # --- Seção do Filtro Cascata e Gráfico Associado ---
    html.Div(className="cascading-filter-section", style={'marginTop': '40px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'backgroundColor': '#f9f9f9'}, children=[
        html.H3("Análise Detalhada por Tipo e Marca de Produto", style={'marginTop': '0', 'marginBottom': '20px', 'color': '#333'}),
        html.Div(className="filters-row", style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
            html.Div(style={'flex': '1'}, children=[
                html.Label("Selecione o Tipo do Produto:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-cascata-tipo-produto',
                    options=get_dropdown_options(df_global, 'Tipo do Produto', add_all_values_option=False), # No 'ALL' option here
                    placeholder="Selecione um Tipo"
                )
            ]),
            html.Div(style={'flex': '1'}, children=[
                html.Label("Selecione a Marca:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='dropdown-cascata-marca',
                    placeholder="Selecione uma Marca (após Tipo)"
                )
            ]),
        ]),
        html.Div(className="chart-container", style={'border': '1px solid #eee', 'borderRadius': '8px', 'padding': '15px', 'backgroundColor': '#fff'}, children=[
             html.H4("Receita por Produto (Filtrado por Tipo e Marca)", style={'textAlign': 'center'}),
            dcc.Graph(id='graph-cascata-resultado')
        ])
    ]),
    html.Footer("Dashboard desenvolvido com Dash e Plotly", style={'textAlign': 'center', 'marginTop': '40px', 'padding': '20px', 'fontSize': '0.9em', 'color': '#777'})
])

# --- Callbacks ---

def apply_filters(df, selected_produtos, selected_lojas, selected_clientes, selected_marcas, selected_tipos_produto):
    """Aplica os filtros globais ao DataFrame."""
    dff = df.copy()
    # Ensure selections are lists, even if single value or None is passed initially by multi-select dropdowns
    if selected_produtos and not (isinstance(selected_produtos, list) and ALL_VALUES in selected_produtos) and ALL_VALUES not in selected_produtos:
         if not isinstance(selected_produtos, list): selected_produtos = [selected_produtos]
         dff = dff[dff['Produto'].isin(selected_produtos)]
    
    if selected_lojas and not (isinstance(selected_lojas, list) and ALL_VALUES in selected_lojas) and ALL_VALUES not in selected_lojas:
        if not isinstance(selected_lojas, list): selected_lojas = [selected_lojas]
        dff = dff[dff['Nome da Loja'].isin(selected_lojas)]

    if selected_clientes and not (isinstance(selected_clientes, list) and ALL_VALUES in selected_clientes) and ALL_VALUES not in selected_clientes:
        if not isinstance(selected_clientes, list): selected_clientes = [selected_clientes]
        dff = dff[dff['Nome Completo'].isin(selected_clientes)]

    if selected_marcas and not (isinstance(selected_marcas, list) and ALL_VALUES in selected_marcas) and ALL_VALUES not in selected_marcas:
        if not isinstance(selected_marcas, list): selected_marcas = [selected_marcas]
        dff = dff[dff['Marca'].isin(selected_marcas)]

    if selected_tipos_produto and not (isinstance(selected_tipos_produto, list) and ALL_VALUES in selected_tipos_produto) and ALL_VALUES not in selected_tipos_produto:
        if not isinstance(selected_tipos_produto, list): selected_tipos_produto = [selected_tipos_produto]
        dff = dff[dff['Tipo do Produto'].isin(selected_tipos_produto)]
    return dff

@app.callback(
    [Output('graph-receita-ano', 'figure'),
     Output('graph-top-clientes', 'figure'),
     Output('graph-top-produtos', 'figure'),
     Output('graph-receita-loja', 'figure'),
     Output('graph-receita-tipo-produto-tempo', 'figure'),
     Output('table-vendas-marca', 'data'),
     Output('table-vendas-marca', 'columns')],
    [Input('dropdown-produto', 'value'),
     Input('dropdown-loja', 'value'),
     Input('dropdown-cliente', 'value'),
     Input('dropdown-marca', 'value'),
     Input('dropdown-tipo-produto', 'value')]
)
def update_main_graphs(selected_produtos, selected_lojas, selected_clientes, selected_marcas, selected_tipos_produto):
    if df_global.empty: 
        empty_fig = {'data': [], 'layout': {'title': 'Dados não disponíveis'}}
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, [], []
    
    dff = apply_filters(df_global, selected_produtos, selected_lojas, selected_clientes, selected_marcas, selected_tipos_produto)

    if dff.empty: 
        empty_fig = {'data': [], 'layout': {'title': 'Nenhum dado para os filtros selecionados'}}
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, [], []

    # Gráfico 1: Receita Total por Ano
    receita_ano_df = dff.groupby('Ano da Venda')['Receita'].sum().reset_index()
    fig_receita_ano = px.line(receita_ano_df, x='Ano da Venda', y='Receita', markers=True,
                              labels={'Ano da Venda': 'Ano', 'Receita': 'Receita Total (R$)'})
    fig_receita_ano.update_layout(xaxis_type='category') 

    # Gráfico 2: Top 10 Clientes por Receita
    top_clientes_df = dff.groupby('Nome Completo')['Receita'].sum().nlargest(10).reset_index()
    fig_top_clientes = px.bar(top_clientes_df, y='Nome Completo', x='Receita', orientation='h',
                              labels={'Nome Completo': 'Cliente', 'Receita': 'Receita Total (R$)'})
    fig_top_clientes.update_layout(yaxis={'categoryorder':'total ascending'})

    # Gráfico 3: Top 10 Produtos por Receita
    top_produtos_df = dff.groupby('Produto')['Receita'].sum().nlargest(10).reset_index()
    fig_top_produtos = px.bar(top_produtos_df, x='Produto', y='Receita',
                               labels={'Produto': 'Produto', 'Receita': 'Receita Total (R$)'})
    fig_top_produtos.update_layout(xaxis={'categoryorder':'total descending'})

    # Gráfico 4: Distribuição de Receita por Loja
    receita_loja_df = dff.groupby('Nome da Loja')['Receita'].sum().reset_index()
    fig_receita_loja = px.pie(receita_loja_df, names='Nome da Loja', values='Receita', hole=0.3)

    # Gráfico 5: Receita por Tipo de Produto ao Longo do Tempo (Mensal)
    receita_tipo_tempo_df = dff.groupby(['MesAno da Venda', 'Tipo do Produto'])['Receita'].sum().reset_index()
    receita_tipo_tempo_df = receita_tipo_tempo_df.sort_values('MesAno da Venda')
    fig_receita_tipo_tempo = px.area(receita_tipo_tempo_df, x='MesAno da Venda', y='Receita', color='Tipo do Produto',
                                     labels={'MesAno da Venda': 'Mês-Ano', 'Receita': 'Receita (R$)', 'Tipo do Produto': 'Tipo de Produto'})
    fig_receita_tipo_tempo.update_xaxes(tickangle=45)

    # Tabela 6: Resumo de Vendas por Marca
    vendas_marca_df = dff.groupby('Marca').agg(
        Total_Qtd_Vendida=('Qtd Vendida', 'sum'),
        Total_Receita=('Receita', 'sum')
    ).reset_index()
    vendas_marca_df.rename(columns={'Marca': 'Marca', 
                                    'Total_Qtd_Vendida': 'Quantidade Vendida Total', 
                                    'Total_Receita': 'Receita Total (R$)'}, inplace=True)
    
    table_cols = [{"name": i, "id": i} for i in vendas_marca_df.columns]
    table_data = vendas_marca_df.to_dict('records')

    return fig_receita_ano, fig_top_clientes, fig_top_produtos, fig_receita_loja, fig_receita_tipo_tempo, table_data, table_cols

@app.callback(
    Output('dropdown-cascata-marca', 'options'),
    [Input('dropdown-cascata-tipo-produto', 'value')]
)
def update_marcas_dropdown(selected_tipo_produto):
    if not selected_tipo_produto or df_global.empty:
        return []
    
    # Filter df_global for the selected 'Tipo do Produto' first
    marcas_df = df_global[df_global['Tipo do Produto'] == selected_tipo_produto]
    
    # Then get unique 'Marca' values from this filtered DataFrame
    options = get_dropdown_options(marcas_df, 'Marca', add_all_values_option=False) # No 'ALL' for this one
    return options

@app.callback(
    Output('graph-cascata-resultado', 'figure'),
    [Input('dropdown-cascata-tipo-produto', 'value'),
     Input('dropdown-cascata-marca', 'value')]
)
def update_cascata_graph(selected_tipo_produto, selected_marca):
    if df_global.empty or not selected_tipo_produto or not selected_marca:
        return {'data': [], 'layout': {'title': 'Selecione Tipo de Produto e Marca para ver os dados'}}

    dff_cascata = df_global[
        (df_global['Tipo do Produto'] == selected_tipo_produto) &
        (df_global['Marca'] == selected_marca)
    ]

    if dff_cascata.empty:
        return {'data': [], 'layout': {'title': f'Nenhum dado para {selected_tipo_produto} - {selected_marca}'}}

    receita_produto_filtrado_df = dff_cascata.groupby('Produto')['Receita'].sum().reset_index().sort_values(by='Receita', ascending=False)
    
    fig_cascata = px.bar(receita_produto_filtrado_df, x='Produto', y='Receita',
                         labels={'Produto': 'Produto', 'Receita': 'Receita Total (R$)'},
                         title=f"Receita por Produto: {selected_tipo_produto} - {selected_marca}")
    fig_cascata.update_layout(xaxis={'categoryorder':'total descending'})
    return fig_cascata


if __name__ == '__main__':
    if df_global.empty:
        print("Não foi possível carregar os dados. O dashboard não será iniciado.")
    else:
        print("Dados carregados com sucesso. Iniciando o dashboard...")
        app.run(debug=True) # Alterado de app.run_server para app.run
