import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

CSS = """
<style>
    :root {
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --secondary: #ef4444;
        --secondary-hover: #dc2626;
        --success: #10b981;
        --warning: #f59e0b;
        --background: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --border-color: #e5e7eb;
    }
    
    * { transition: all 0.3s ease; }
    
    button[kind="primary"] {
        background-color: var(--primary);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    button[kind="primary"]:hover {
        background-color: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    button[kind="secondary"] {
        background-color: var(--secondary);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    button[kind="secondary"]:hover {
        background-color: var(--secondary-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stForm {
        background: var(--card-bg);
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .stTextInput > div > input, .stNumberInput > div > input, 
    .stDateInput > div > input, .stTimeInput > div > input,
    .stSelectbox > div > select {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 10px 12px;
        width: 100%;
    }
    .stTextInput > div > input:focus, .stNumberInput > div > input:focus, 
    .stDateInput > div > input:focus, .stTimeInput > div > input:focus,
    .stSelectbox > div > select:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        outline: none;
    }
    .dashboard-header {
        background: linear-gradient(135deg, var(--primary) 0%, #1d4ed8 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .dashboard-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: bold;
        margin: 0;
        margin-bottom: 8px;
    }
    .dashboard-header .subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1rem;
        margin: 0;
    }
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-bottom: 25px;
    }
    .metric-item {
        background: var(--card-bg);
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    .metric-value { font-size: 1.5em; font-weight: bold; color: var(--text-primary); }
    .metric-label { color: var(--text-secondary); font-size: 0.8em; margin-top: 4px; }
    .positive-value { color: var(--success); }
    .negative-value { color: var(--secondary); }
    .stTabs [role="tablist"] { gap: 10px; }
    .stTabs [role="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        background-color: #f1f5f9;
        color: var(--text-secondary);
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: var(--primary);
        color: white;
    }
    .stTabs [role="tab"]:hover { background-color: #e5e7eb; }
    .stTabs [role="tab"][aria-selected="true"]:hover { background-color: var(--primary-hover); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 20px;
    }
    /* CSS do bet.py integrado */
    .stApp { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
    .liga-header {
        background-color: #f0f2f6;
        padding: 6px 12px;
        font-weight: 700;
        color: #333;
        border-radius: 4px;
        margin-top: 15px;
        margin-bottom: 8px;
        font-size: 16px;
    }
    .odd-value {
        background-color: #e8f5e9;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        color: #2e7d32;
        text-align: center;
        display: block;
    }
    .live {
        color: #d32f2f;
        font-weight: bold;
        font-size: 14px;
    }
    .placar {
        text-align: center;
        background-color: #f1f1f1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
    }
    .data-hora-container {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 12px;
        color: #666;
        margin-bottom: 2px;
    }
    .tempo-evento {
        font-size: 14px;
        color: #333;
        text-align: center;
    }
    .stColumn > div { padding: 0 4px; }
    @media (max-width: 768px) {
        .metric-container { grid-template-columns: 1fr 1fr; }
        .dashboard-header h1 { font-size: 1.8rem; }
    }
    @media (max-width: 480px) { .metric-container { grid-template-columns: 1fr; } }
</style>
"""

def aplicar_estilo_grafico(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1f2937'),
        hovermode='x unified',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def criar_grafico_horas(cronograma_despesas, cronograma_receitas):
    despesas_hora = cronograma_despesas[[f"{i}h" for i in range(24)]].sum()
    receitas_hora = cronograma_receitas[[f"{i}h" for i in range(24)]].sum()
    df = pd.concat([
        pd.DataFrame({'Hora': [f"{i}h" for i in range(24)], 'Valor': despesas_hora, 'Tipo': 'Despesas'}),
        pd.DataFrame({'Hora': [f"{i}h" for i in range(24)], 'Valor': receitas_hora, 'Tipo': 'Receitas'})
    ])
    fig = px.line(df, x='Hora', y='Valor', color='Tipo', markers=True,
                 title='Distribuição por Hora (Despesas vs Receitas)',
                 labels={'Valor': 'Valor (R$)', 'Hora': 'Hora'},
                 color_discrete_map={'Despesas': '#EF4444', 'Receitas': '#10B981'})
    fig.update_traces(line_width=3)
    return aplicar_estilo_grafico(fig)

def criar_grafico_distributicao_hora_dia(cronograma_despesas, cronograma_receitas):
    hoje = datetime.now().strftime('%d/%m/%Y')
    hoje_dt = pd.to_datetime(hoje, format='%d/%m/%Y')
    despesas_hora = [cronograma_despesas.loc[hoje_dt, f"{i}h"] if hoje_dt in cronograma_despesas.index else 0 for i in range(24)]
    receitas_hora = [cronograma_receitas.loc[hoje_dt, f"{i}h"] if hoje_dt in cronograma_receitas.index else 0 for i in range(24)]
    df = pd.concat([
        pd.DataFrame({'Hora': [f'{i}h' for i in range(24)], 'Valor': despesas_hora, 'Tipo': 'Despesas'}),
        pd.DataFrame({'Hora': [f'{i}h' for i in range(24)], 'Valor': receitas_hora, 'Tipo': 'Receitas'})
    ])
    fig = px.bar(df, x='Hora', y='Valor', color='Tipo', barmode='group',
                 title=f'Distribuição por Hora - Hoje ({hoje})',
                 labels={'Valor': 'Valor Total (R$)', 'Hora': 'Hora do Dia'},
                 color_discrete_map={'Despesas': '#EF4444', 'Receitas': '#10B981'})
    fig.update_layout(bargap=0.2)
    return aplicar_estilo_grafico(fig)

def criar_grafico_comparacao_receitas_despesas(cronograma_despesas, cronograma_receitas, data_inicio, data_fim):
    todas_datas = pd.date_range(start=data_inicio, end=data_fim, freq='D')
    despesas_totais = cronograma_despesas['Total do Dia'].reindex(todas_datas, fill_value=0)
    receitas_totais = cronograma_receitas['Total do Dia'].reindex(todas_datas, fill_value=0)
    df = pd.DataFrame({'Data': todas_datas, 'Despesas': despesas_totais.values, 'Receitas': receitas_totais.values})
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')
    df_long = df.melt(id_vars=['Data'], value_vars=['Despesas', 'Receitas'], var_name='Tipo', value_name='Valor')
    fig = px.bar(df_long, x='Data', y='Valor', color='Tipo', barmode='group',
                 title='Comparação de Receitas e Despesas por Dia',
                 labels={'Valor': 'Valor Total (R$)', 'Data': 'Data'},
                 color_discrete_map={'Despesas': '#EF4444', 'Receitas': '#10B981'})
    fig.update_layout(xaxis={'type': 'category', 'tickangle': -45})
    return aplicar_estilo_grafico(fig)

def criar_grafico_categorias(despesas, receitas):
    df_despesas = pd.DataFrame(despesas)
    df_receitas = pd.DataFrame(receitas)
    if df_despesas.empty and df_receitas.empty:
        return None
    if not df_despesas.empty:
        df_despesas['Tipo'] = 'Despesas'
    if not df_receitas.empty:
        df_receitas['Tipo'] = 'Receitas'
    df = pd.concat([df_despesas, df_receitas])
    df_grouped = df.groupby(['categoria', 'Tipo'])['valor'].sum().reset_index()
    fig = px.bar(df_grouped, x='categoria', y='valor', color='Tipo',
                 title='Distribuição por Categoria',
                 labels={'valor': 'Valor Total (R$)', 'categoria': 'Categoria'},
                 color_discrete_map={'Despesas': '#EF4444', 'Receitas': '#10B981'},
                 barmode='group')
    fig.update_layout(xaxis={'tickangle': -45})
    return aplicar_estilo_grafico(fig)