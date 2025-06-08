# main.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from database import *
from visualization import *
from bet import exibir_eventos_apostas
from double import main as double_main  # Importa a função main de double.py
from double import main as double_interface  # Importa a função main de double.py



st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

def criar_cronograma(despesas, receitas, data_inicio, data_fim):
    cronograma = pd.DataFrame(columns=[f'{i}h' for i in range(24)], dtype=float)
    agora = datetime.now()
    total_despesas = sum(d['valor'] for d in despesas)
    total_receitas = sum(r['valor'] for r in receitas)
    valor_restante = total_despesas - total_receitas

    despesas_df = pd.DataFrame(despesas)
    if not despesas_df.empty:
        despesas_df['data_inicial'] = pd.to_datetime(despesas_df['data_inicial']).clip(lower=agora)
        despesas_df['data_final'] = pd.to_datetime(despesas_df['data_final'])
        mask = (despesas_df['data_inicial'].dt.date <= despesas_df['data_final'].dt.date) & \
               (despesas_df['data_final'].dt.date >= data_inicio) & \
               (despesas_df['data_inicial'].dt.date <= data_fim)
        despesas_df = despesas_df[mask]

        for _, row in despesas_df.iterrows():
            horas = (row['data_final'] - row['data_inicial']).total_seconds() / 3600
            valor_hora = row['valor'] / horas if horas > 0 else 0
            dates = pd.date_range(row['data_inicial'], row['data_final'], freq='H')
            for date in dates:
                day_str = date.strftime('%d/%m/%Y')
                if day_str not in cronograma.index:
                    cronograma.loc[day_str] = 0.0
                cronograma.at[day_str, f'{date.hour}h'] += valor_hora

    receitas_df = pd.DataFrame(receitas)
    if not receitas_df.empty:
        data_final_max = max(despesas_df['data_final'].max() if not despesas_df.empty else agora, agora)
        receitas_df['data_evento'] = pd.to_datetime(receitas_df['data_evento'])
        for _, row in receitas_df.iterrows():
            ultimo_dia = datetime(row['data_evento'].year + (1 if row['data_evento'].month == 12 else 0),
                                1 if row['data_evento'].month == 12 else row['data_evento'].month + 1,
                                1) - timedelta(days=1)
            inicio = max(row['data_evento'], agora)
            fim = min(ultimo_dia, data_final_max) if not despesas_df.empty else ultimo_dia
            if inicio.date() <= fim.date() and fim.date() >= data_inicio and inicio.date() <= data_fim:
                horas = (fim - inicio).total_seconds() / 3600
                abatimento_hora = row['valor'] / horas if horas > 0 else 0
                dates = pd.date_range(inicio, fim, freq='H')
                for date in dates:
                    day_str = date.strftime('%d/%m/%Y')
                    if day_str not in cronograma.index:
                        cronograma.loc[day_str] = 0.0
                    cronograma.at[day_str, f'{date.hour}h'] -= abatimento_hora

    cronograma.index = pd.to_datetime(cronograma.index, format='%d/%m/%Y')
    mask = (cronograma.index >= pd.Timestamp(data_inicio)) & (cronograma.index <= pd.Timestamp(data_fim))
    cronograma = cronograma.loc[mask]
    cronograma['Restante'] = cronograma[[f'{i}h' for i in range(24)]].sum(axis=1)
    return cronograma, total_receitas, valor_restante

def criar_cronograma_receitas(receitas, data_inicio, data_fim):
    cronograma = pd.DataFrame(columns=[f'{i}h' for i in range(24)], dtype=float)
    receitas_df = pd.DataFrame(receitas)
    if not receitas_df.empty:
        receitas_df['data_evento'] = pd.to_datetime(receitas_df['data_evento'])
        mask = (receitas_df['data_evento'].dt.date >= data_inicio) & (receitas_df['data_evento'].dt.date <= data_fim)
        for _, row in receitas_df[mask].iterrows():
            hora = datetime.strptime(row['hora_evento'], '%H:%M:%S').hour
            day_str = row['data_evento'].strftime('%d/%m/%Y')
            if day_str not in cronograma.index:
                cronograma.loc[day_str] = 0.0
            cronograma.at[day_str, f'{hora}h'] += row['valor']
    cronograma.index = pd.to_datetime(cronograma.index, format='%d/%m/%Y')
    cronograma['Total do Dia'] = cronograma[[f'{i}h' for i in range(24)]].sum(axis=1)
    return cronograma

def criar_cronograma_despesas(despesas, data_inicio, data_fim):
    cronograma = pd.DataFrame(columns=[f'{i}h' for i in range(24)], dtype=float)
    agora = datetime.now()
    despesas_df = pd.DataFrame(despesas)
    if not despesas_df.empty:
        despesas_df['data_inicial'] = pd.to_datetime(despesas_df['data_inicial']).clip(lower=agora)
        despesas_df['data_final'] = pd.to_datetime(despesas_df['data_final'])
        mask = (despesas_df['data_inicial'].dt.date <= despesas_df['data_final'].dt.date) & \
               (despesas_df['data_final'].dt.date >= data_inicio) & \
               (despesas_df['data_inicial'].dt.date <= data_fim)
        for _, row in despesas_df[mask].iterrows():
            horas = (row['data_final'] - row['data_inicial']).total_seconds() / 3600
            valor_hora = row['valor'] / horas if horas > 0 else 0
            dates = pd.date_range(row['data_inicial'], row['data_final'], freq='H')
            for date in dates:
                day_str = date.strftime('%d/%m/%Y')
                if day_str not in cronograma.index:
                    cronograma.loc[day_str] = 0.0
                cronograma.at[day_str, f'{date.hour}h'] += valor_hora
    cronograma.index = pd.to_datetime(cronograma.index, format='%d/%m/%Y')
    mask = (cronograma.index >= pd.Timestamp(data_inicio)) & (cronograma.index <= pd.Timestamp(data_fim))
    cronograma = cronograma.loc[mask]
    cronograma['Total do Dia'] = cronograma[[f'{i}h' for i in range(24)]].sum(axis=1)
    return cronograma

def calcular_ganhos_dia_atual(cronograma_receitas):
    hoje = datetime.now().strftime('%d/%m/%Y')
    hoje_dt = pd.to_datetime(hoje, format='%d/%m/%Y')
    return cronograma_receitas.loc[hoje_dt, 'Total do Dia'] if hoje_dt in cronograma_receitas.index else 0

def calcular_despesa_hora_atual(cronograma_despesas):
    agora = datetime.now()
    dia_atual = agora.strftime('%d/%m/%Y')
    hora_atual = agora.hour
    dia_dt = pd.to_datetime(dia_atual, format='%d/%m/%Y')
    return cronograma_despesas.loc[dia_dt, f'{hora_atual}h'] if dia_dt in cronograma_despesas.index else 0

def atualizar_dados(data_inicio, data_fim):
    with st.spinner('Atualizando dados...'):
        despesas = fetch_data("cadastro_despesas")
        receitas = fetch_data("cadastro_receitas")
        cronograma, total_receitas, valor_restante = criar_cronograma(despesas, receitas, data_inicio, data_fim)
        cronograma_receitas = criar_cronograma_receitas(receitas, data_inicio, data_fim)
        cronograma_despesas = criar_cronograma_despesas(despesas, data_inicio, data_fim)
        st.session_state.update({
            'cronograma': cronograma, 'total_receitas': total_receitas, 'valor_restante': valor_restante,
            'cronograma_receitas': cronograma_receitas, 'cronograma_despesas': cronograma_despesas,
            'despesas': despesas, 'receitas': receitas
        })

def main():
    conectar_banco()
    if 'cronograma' not in st.session_state:
        hoje = datetime.now().date()
        st.session_state.update({
            'cronograma': None, 'total_receitas': 0, 'valor_restante': 0,
            'cronograma_receitas': None, 'cronograma_despesas': None,
            'despesas': [], 'receitas': [],
            'data_inicio': hoje, 'data_fim': hoje + timedelta(days=7)
        })

    with st.sidebar:
        st.markdown("""
        <div style='padding: 15px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                    color: white; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: white;'>⚙️ Configurações</h3>
        </div>
        """, unsafe_allow_html=True)
        data_inicio = st.date_input("Data Inicial", value=st.session_state['data_inicio'])
        data_fim = st.date_input("Data Final", value=st.session_state['data_fim'])
        if st.button("Aplicar Filtros", type="primary"):
            st.session_state.update({'data_inicio': data_inicio, 'data_fim': data_fim})
            atualizar_dados(data_inicio, data_fim)
            st.toast("Filtros aplicados com sucesso!", icon="✅")

    st.markdown("""
    <div class="dashboard-header">
        <h1>💰 Gestão Financeira</h1>
        <p class="subtitle">Controle suas receitas, despesas e apostas em tempo real</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Adiciona a aba "Double" ao final da lista de abas
    tabs = st.tabs(["Dashboard", "Cadastro de Despesas", "Cadastro de Receitas", "Editar Registros", "Eventos de Apostas", "Double"])

    with tabs[0]:
        atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
        cronograma = st.session_state['cronograma']
        total_receitas = st.session_state['total_receitas']
        valor_restante = st.session_state['valor_restante']
        cronograma_receitas = st.session_state['cronograma_receitas']
        cronograma_despesas = st.session_state['cronograma_despesas']
        despesas = st.session_state['despesas']
        receitas = st.session_state['receitas']

        total_despesas = total_receitas + valor_restante
        ganhos_dia_atual = calcular_ganhos_dia_atual(cronograma_receitas)
        despesa_hora_atual = calcular_despesa_hora_atual(cronograma_despesas)

        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-item"><div class="metric-value positive-value">R$ {total_receitas:,.2f}</div><div class="metric-label">Total de Receitas</div></div>
            <div class="metric-item"><div class="metric-value negative-value">R$ {total_despesas:,.2f}</div><div class="metric-label">Total de Despesas</div></div>
            <div class="metric-item"><div class="metric-value {'negative-value' if valor_restante > 0 else 'positive-value'}">R$ {abs(valor_restante):,.2f}</div><div class="metric-label">{'Déficit' if valor_restante > 0 else 'Superávit'}</div></div>
            <div class="metric-item"><div class="metric-value positive-value">R$ {ganhos_dia_atual:,.2f}</div><div class="metric-label">Ganhos Dia Atual</div></div>
            <div class="metric-item"><div class="metric-value negative-value">R$ {despesa_hora_atual:,.2f}</div><div class="metric-label">Despesa Hora Atual</div></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📊 Ver Dados Completos", expanded=True):
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Tabela de Dados", "⏱️ Distribuição por Hora", "📆 Comparação Diária", "🗂️ Análise por Categoria"])
            with tab1:
                st.dataframe(cronograma.style.format("{:,.2f}"), use_container_width=True)
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(criar_grafico_distributicao_hora_dia(cronograma_despesas, cronograma_receitas), use_container_width=True)
                with col2:
                    st.plotly_chart(criar_grafico_horas(cronograma_despesas, cronograma_receitas), use_container_width=True)
            with tab3:
                st.plotly_chart(criar_grafico_comparacao_receitas_despesas(cronograma_despesas, cronograma_receitas, st.session_state['data_inicio'], st.session_state['data_fim']), use_container_width=True)
            with tab4:
                grafico = criar_grafico_categorias(despesas, receitas)
                if grafico:
                    st.plotly_chart(grafico, use_container_width=True)
                else:
                    st.info("Nenhum dado disponível para análise por categoria.")

    with tabs[1]:
        with st.form("despesas_form", clear_on_submit=True):
            st.subheader("➕ Cadastrar Nova Despesa")
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição*", placeholder="Ex: Aluguel")
            with col2:
                categoria = st.text_input("Categoria", placeholder="Ex: Moradia", value="Outros")
            col1, col2 = st.columns(2)
            with col1:
                valor = st.number_input("Valor (R$)*", min_value=0.0, format="%.2f", step=10.0)
            with col2:
                data_inicial = st.date_input("Data Inicial*")
            data_final = st.date_input("Data Final*")
            if st.form_submit_button("💾 Cadastrar Despesa", type="primary"):
                if not all([descricao, valor, data_inicial, data_final]):
                    st.error("Todos os campos obrigatórios devem ser preenchidos!")
                elif data_inicial > data_final:
                    st.error("Data inicial deve ser anterior ou igual à data final!")
                else:
                    with st.status("Processando...", expanded=True) as status:
                        time.sleep(0.5)
                        if insert_data("cadastro_despesas", {"descricao": descricao, "valor": valor, 
                                                            "data_inicial": data_inicial.strftime('%Y-%m-%d'), 
                                                            "data_final": data_final.strftime('%Y-%m-%d'), 
                                                            "categoria": categoria}):
                            status.update(label="Despesa cadastrada com sucesso! ✔️", state="complete")
                            atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                            st.toast('Despesa cadastrada com sucesso!', icon='🎉')

    with tabs[2]:
        with st.form("receitas_form", clear_on_submit=True):
            st.subheader("➕ Cadastrar Nova Receita")
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição*", placeholder="Ex: Salário")
            with col2:
                categoria = st.text_input("Categoria", placeholder="Ex: Trabalho", value="Outros")
            col1, col2 = st.columns(2)
            with col1:
                valor = st.number_input("Valor (R$)*", min_value=0.0, format="%.2f", step=10.0)
            with col2:
                data_evento = st.date_input("Data do Evento*")
            hora_evento = st.time_input("Hora do Evento", value=datetime.now().time())
            if st.form_submit_button("💾 Cadastrar Receita", type="primary"):
                if not all([descricao, valor, data_evento]):
                    st.error("Todos os campos obrigatórios devem ser preenchidos!")
                else:
                    with st.status("Processando...", expanded=True) as status:
                        time.sleep(0.5)
                        if insert_data("cadastro_receitas", {"descricao": descricao, "valor": valor, 
                                                            "data_evento": data_evento.strftime('%Y-%m-%d'), 
                                                            "hora_evento": hora_evento.strftime('%H:%M:%S'), 
                                                            "categoria": categoria}):
                            status.update(label="Receita cadastrada com sucesso! ✔️", state="complete")
                            atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                            st.toast('Receita cadastrada com sucesso!', icon='🎉')

    with tabs[3]:
        tipo = st.radio("Tipo de Registro:", ("Despesa", "Receita"), horizontal=True)
        if tipo == "Despesa":
            st.subheader("✏️ Editar Despesa")
            despesas = fetch_data("cadastro_despesas")
            if despesas:
                despesa_selecionada = st.selectbox("Selecione a Despesa", 
                                                  [f"{d['id']} - {d['descricao']} (R${d['valor']:,.2f}) - {d['categoria']}" for d in despesas])
                despesa_id = int(despesa_selecionada.split(" - ")[0])
                despesa = next(d for d in despesas if d['id'] == despesa_id)
                with st.form("edit_despesa_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        descricao = st.text_input("Descrição", value=despesa['descricao'])
                    with col2:
                        categoria = st.text_input("Categoria", value=despesa['categoria'])
                    valor = st.number_input("Valor", value=float(despesa['valor']), min_value=0.0, format="%.2f")
                    col1, col2 = st.columns(2)
                    with col1:
                        data_inicial = st.date_input("Data Inicial", datetime.strptime(despesa['data_inicial'], '%Y-%m-%d'))
                    with col2:
                        data_final = st.date_input("Data Final", datetime.strptime(despesa['data_final'], '%Y-%m-%d'))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                            if data_inicial <= data_final:
                                with st.status("Atualizando...", expanded=True) as status:
                                    time.sleep(0.5)
                                    if update_data("cadastro_despesas", despesa_id, {"descricao": descricao, "valor": valor, 
                                                                                    "data_inicial": data_inicial.strftime('%Y-%m-%d'), 
                                                                                    "data_final": data_final.strftime('%Y-%m-%d'), 
                                                                                    "categoria": categoria}):
                                        status.update(label="Despesa atualizada com sucesso! ✔️", state="complete")
                                        atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                                        st.toast('Despesa atualizada com sucesso!', icon='🎉')
                    with col2:
                        if st.form_submit_button("🗑️ Excluir Despesa", type="secondary"):
                            with st.status("Excluindo...", expanded=True) as status:
                                time.sleep(0.5)
                                if delete_data("cadastro_despesas", despesa_id):
                                    status.update(label="Despesa excluída com sucesso! ✔️", state="complete")
                                    atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                                    st.toast('Despesa excluída com sucesso!', icon='🎉')
            else:
                st.info("Nenhuma despesa cadastrada ainda.")
        else:
            st.subheader("✏️ Editar Receita")
            receitas = fetch_data("cadastro_receitas")
            if receitas:
                receita_selecionada = st.selectbox("Selecione a Receita", 
                                                  [f"{r['id']} - {r['descricao']} (R${r['valor']:,.2f}) - {r['categoria']}" for r in receitas])
                receita_id = int(receita_selecionada.split(" - ")[0])
                receita = next(r for r in receitas if r['id'] == receita_id)
                with st.form("edit_receita_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        descricao = st.text_input("Descrição", value=receita['descricao'])
                    with col2:
                        categoria = st.text_input("Categoria", value=receita['categoria'])
                    valor = st.number_input("Valor", value=float(receita['valor']), min_value=0.0, format="%.2f")
                    col1, col2 = st.columns(2)
                    with col1:
                        data_evento = st.date_input("Data do Evento", datetime.strptime(receita['data_evento'], '%Y-%m-%d'))
                    with col2:
                        hora_evento = st.time_input("Hora do Evento", datetime.strptime(receita['hora_evento'], '%H:%M:%S'))
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                            with st.status("Atualizando...", expanded=True) as status:
                                time.sleep(0.5)
                                if update_data("cadastro_receitas", receita_id, {"descricao": descricao, "valor": valor, 
                                                                                "data_evento": data_evento.strftime('%Y-%m-%d'), 
                                                                                "hora_evento": hora_evento.strftime('%H:%M:%S'), 
                                                                                "categoria": categoria}):
                                    status.update(label="Receita atualizada com sucesso! ✔️", state="complete")
                                    atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                                    st.toast('Receita atualizada com sucesso!', icon='🎉')
                    with col2:
                        if st.form_submit_button("🗑️ Excluir Receita", type="secondary"):
                            with st.status("Excluindo...", expanded=True) as status:
                                time.sleep(0.5)
                                if delete_data("cadastro_receitas", receita_id):
                                    status.update(label="Receita excluída com sucesso! ✔️", state="complete")
                                    atualizar_dados(st.session_state['data_inicio'], st.session_state['data_fim'])
                                    st.toast('Receita excluída com sucesso!', icon='🎉')
            else:
                st.info("Nenhuma receita cadastrada ainda.")

    with tabs[4]:
        exibir_eventos_apostas()

    # Nova aba "Double"
    with tabs[5]:
        double_interface()

if __name__ == "__main__":
    main()