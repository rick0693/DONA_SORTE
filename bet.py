import streamlit as st
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
import time
import pandas as pd
from datetime import datetime

global_driver = None

def inicializar_navegador():
    global global_driver
    if global_driver is None:
        user_agent = UserAgent()
        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={user_agent.random}')
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')  # Executa o Chrome em modo headless (sem interface gráfica)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('log-level=3')
        global_driver = webdriver.Chrome(options=options)
        global_driver.maximize_window()
    return global_driver

def fechar_navegador():
    global global_driver
    if global_driver is not None:
        global_driver.quit()
        global_driver = None

def adicionar_coluna_tempo_evento():
    try:
        conn = sqlite3.connect('informacoes_eventos.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(resultados)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'TempoEvento' not in columns:
            cursor.execute("ALTER TABLE resultados ADD COLUMN TempoEvento TEXT")
            conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao adicionar coluna TempoEvento: {e}")

def obter_informacoes_evento(link_evento):
    driver = inicializar_navegador()
    informacoes = {
        "Informações do Torneio": None, "Hora": None, "Casa / Fora": None, "Status": None, "TempoEvento": None,
        "bet365": None, "Betano.br": None, "BetEsporte": None, "Estrelabet": None, "Superbet.br": None,
        "Esportivabet": None, "KTO.br": None, "Link": link_evento
    }

    try:
        driver.get(link_evento)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'duelParticipant')))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        nav = soup.find("nav", class_="wcl-breadcrumbs_SRNRR detail__breadcrumbs--content")
        if nav:
            informacoes["Informações do Torneio"] = " _ ".join(
                span.text.strip() for item in nav.find_all("li", class_="wcl-breadcrumbItem_CiWQ7")
                if (span := item.find("span", class_="wcl-overline_rOFfd wcl-scores-overline-03_0pkdl"))
            )
        else:
            torneio = soup.find("span", class_="wcl-overline_rOFfd wcl-scores-overline-03_0pkdl") or \
                     (soup.find("div", class_="tournamentHeader__sportContent") and 
                      soup.find("span", class_="tournamentHeader__country"))
            informacoes["Informações do Torneio"] = torneio.text.strip() if torneio else None

        participant = soup.find(class_="duelParticipant")
        informacoes["Hora"] = participant.find(class_="duelParticipant__startTime").text.strip() if participant.find(class_="duelParticipant__startTime") else "N/A"
        time_casa = participant.find(class_="participant__participantNameWrapper").find("a").text.strip() if participant.find(class_="participant__participantNameWrapper") else "N/A"
        time_fora = participant.find_all(class_="participant__participantNameWrapper")[-1].find("a").text.strip() if participant.find_all(class_="participant__participantNameWrapper") else "N/A"
        placar = participant.find(class_="detailScore__matchInfo")
        placar_casa, placar_fora = (spans[0].text.strip(), spans[2].text.strip()) if placar and len(spans := placar.find_all("span")) >= 3 else ("N/A", "N/A")
        informacoes["Casa / Fora"] = f"{time_casa} {placar_casa} x {placar_fora} {time_fora}"

        tempo_evento = soup.find("div", class_="eventAndAddedTime")
        informacoes["TempoEvento"] = tempo_evento.find("span", class_="eventTime").text.strip() if tempo_evento and tempo_evento.find("span", class_="eventTime") else None
        try:
            evento_dt = datetime.strptime(informacoes["Hora"], "%d.%m.%Y %H:%M")
            informacoes["Status"] = "Aguardando início" if evento_dt > datetime.now() else \
                                   participant.find(class_="fixedHeaderDuel__detailStatus").text.strip() if participant.find(class_="fixedHeaderDuel__detailStatus") else "N/A"
        except ValueError:
            informacoes["Status"] = "N/A"
        if informacoes["Status"].lower() in ["encerrado", "concluído"] and not informacoes["TempoEvento"]:
            informacoes["TempoEvento"] = "Encerrado"

        is_live = informacoes["Status"].lower() in ["intervalo", "1º tempo", "2º tempo"]
        if is_live:
            odds_wrapper = soup.find("div", class_="oddsWrapper liveOdds")
            if odds_wrapper:
                for row in odds_wrapper.find_all("div", class_="oddsRowContent"):
                    bookmaker = row.find("a", class_="prematchLink")
                    if bookmaker and (name := bookmaker.get("title")) in informacoes:
                        odds = row.find_all("span", class_="oddsValueInner")
                        if len(odds) >= 3:
                            informacoes[name] = f"1: {odds[0].text.strip() or '-'}, X: {odds[1].text.strip() or '-'}, 2: {odds[2].text.strip() or '-'}"
        else:
            odds_link = link_evento.replace('#/resumo-de-jogo/estatisticas-de-jogo/0', '#/comparacao-de-odds/1x2-odds/tempo-regulamentar')
            driver.get(odds_link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ui-table')))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            odds_table = soup.find("div", class_="ui-table oddsCell__odds")
            if odds_table:
                for row in odds_table.find_all("div", class_="ui-table__row"):
                    bookmaker = row.find("a", class_="prematchLink")
                    if bookmaker and (name := bookmaker.get("title")) in informacoes:
                        odds = row.find_all("span", class_="")
                        if len(odds) >= 3:
                            informacoes[name] = f"1: {odds[0].text}, X: {odds[1].text}, 2: {odds[2].text}"

        return informacoes
    except Exception as e:
        st.error(f"Erro ao extrair informações do evento {link_evento}: {e}")
        return None

def inserir_atualizar_informacoes_banco_dados(informacoes):
    try:
        with sqlite3.connect('informacoes_eventos.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Link FROM resultados WHERE Link = ?", (informacoes["Link"],))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE resultados SET Informacoes_do_Torneio=?, Hora=?, Casa_Fora=?, Status=?, 
                    bet365=?, Betano_br=?, BetEsporte=?, Estrelabet=?, Superbet_br=?, Esportivabet=?, KTO_br=?, TempoEvento=?
                    WHERE Link=?""", (
                    informacoes["Informações do Torneio"], informacoes["Hora"], informacoes["Casa / Fora"], informacoes["Status"],
                    informacoes["bet365"], informacoes["Betano.br"], informacoes["BetEsporte"], informacoes["Estrelabet"],
                    informacoes["Superbet.br"], informacoes["Esportivabet"], informacoes["KTO.br"], informacoes["TempoEvento"],
                    informacoes["Link"]
                ))
            else:
                cursor.execute("""
                    INSERT INTO resultados (Informacoes_do_Torneio, Hora, Casa_Fora, Status, bet365, Betano_br, BetEsporte, 
                    Estrelabet, Superbet_br, Esportivabet, KTO_br, TempoEvento, Link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    informacoes["Informações do Torneio"], informacoes["Hora"], informacoes["Casa / Fora"], informacoes["Status"],
                    informacoes["bet365"], informacoes["Betano.br"], informacoes["BetEsporte"], informacoes["Estrelabet"],
                    informacoes["Superbet.br"], informacoes["Esportivabet"], informacoes["KTO.br"], informacoes["TempoEvento"],
                    informacoes["Link"]
                ))
            conn.commit()
    except Exception as e:
        st.error(f"Erro ao inserir/atualizar informações no banco de dados: {e}")

def atualizar_eventos_do_banco():
    with sqlite3.connect('informacoes_eventos.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Link, Hora, Status FROM resultados")
        eventos = cursor.fetchall()

    eventos_para_atualizar = [
        link for link, hora, status in eventos
        if hora and datetime.strptime(hora, "%d.%m.%Y %H:%M") <= datetime.now() and status not in ["Concluído", "Encerrado"]
    ]

    if eventos_para_atualizar:
        #st.write(f"Eventos a serem atualizados: {len(eventos_para_atualizar)}")
        for link in eventos_para_atualizar:
            #st.write(f"Atualizando: {link}")
            if informacoes := obter_informacoes_evento(link):
                inserir_atualizar_informacoes_banco_dados(informacoes)
    else:
        st.write("Nenhum evento precisa ser atualizado.")

def parse_teams_and_score(casa_fora):
    default = ("Desconhecido", "-", "Desconhecido", "-")
    if not isinstance(casa_fora, str) or not casa_fora.strip():
        return default
    try:
        if "N/A" in casa_fora or ' - ' in casa_fora or ' vs ' in casa_fora:
            parts = casa_fora.split(' x ' if ' x ' in casa_fora else ' - ' if ' - ' in casa_fora else ' vs ')
            return (parts[0].strip(), '-', parts[1].strip(), '-') if len(parts) == 2 else default
        parts = casa_fora.split(' x ')
        if len(parts) != 2:
            return default
        home_parts = parts[0].rsplit(' ', 1)
        away_parts = parts[1].split(' ', 1)
        return (home_parts[0].strip(), home_parts[1].strip(), away_parts[1].strip(), away_parts[0].strip()) if len(home_parts) == 2 and len(away_parts) == 2 else default
    except Exception:
        return default

def parse_bet365_odds(odds_str):
    default = ('-', '-', '-')
    if not odds_str or pd.isna(odds_str):
        return default
    try:
        parts = odds_str.split(', ')
        return (
            parts[0].split(': ')[1] if len(parts) > 0 and ': ' in parts[0] else '-',
            parts[1].split(': ')[1] if len(parts) > 1 and ': ' in parts[1] else '-',
            parts[2].split(': ')[1] if len(parts) > 2 and ': ' in parts[2] else '-'
        )
    except Exception:
        return default

def carregar_eventos_ativos_hoje():
    with sqlite3.connect("informacoes_eventos.db") as conn:
        df = pd.read_sql_query("SELECT * FROM resultados", conn)
    df['Hora'] = pd.to_datetime(df['Hora'], format='%d.%m.%Y %H:%M', errors='coerce')
    agora = datetime.now().replace(second=0, microsecond=0)
    df_filtrado = df[
        (df['Hora'].dt.date == agora.date()) &
        (df['Hora'] <= agora) &
        (df['Status'].str.lower() != 'encerrado')
    ].copy()
    df_filtrado[['HomeTeam', 'HomeScore', 'AwayTeam', 'AwayScore']] = pd.DataFrame(df_filtrado['Casa_Fora'].apply(parse_teams_and_score).tolist(), index=df_filtrado.index)
    df_filtrado[['Odds_1', 'Odds_X', 'Odds_2']] = pd.DataFrame(df_filtrado['bet365'].apply(parse_bet365_odds).tolist(), index=df_filtrado.index)
    return df_filtrado.sort_values('Informacoes_do_Torneio')

def formatar_status(status, hora):
    base_status = status.split(' ', 1)[0].lower()
    return "LIVE" if base_status in ['em andamento', 'ao vivo', 'live', 'intervalo', '1º tempo', '2º tempo'] else \
           "Aguardando início" if base_status in ['não iniciado', 'agendado'] else status

def exibir_eventos_apostas():
    adicionar_coluna_tempo_evento()
    st.title("⚽ Eventos de Hoje - Até a Hora Atual (Excluindo Encerrados)")
    placeholder_eventos = st.empty()

    # Lista de colunas de odds em ordem de prioridade
    odds_columns = ['bet365', 'Betano_br', 'Estrelabet', 'Superbet_br', 'BetEsporte', 'Esportivabet', 'KTO_br']

    def get_valid_odds(evento):
        for col in odds_columns:
            odds_str = evento[col]
            if odds_str and not pd.isna(odds_str):
                odds = parse_bet365_odds(odds_str)  # Reutiliza a função de parsing
                if odds != ('-', '-', '-'):  # Verifica se as odds são válidas
                    return odds
        return ('-', '-', '-')  # Retorna padrão se nenhuma coluna tiver odds válidas

    try:
        while True:
            ciclo_inicio = time.time()
            atualizar_eventos_do_banco()
            dados = carregar_eventos_ativos_hoje()
            
            with placeholder_eventos.container():
                if dados.empty:
                    st.info("Nenhum evento ativo encontrado até agora.")
                else:
                    for torneio in dados['Informacoes_do_Torneio'].unique():
                        st.markdown(f"<div class='liga-header'>{torneio}</div>", unsafe_allow_html=True)
                        for _, evento in dados[dados['Informacoes_do_Torneio'] == torneio].iterrows():
                            status = formatar_status(evento['Status'], evento['Hora'])
                            is_live = evento['Status'].lower() in ['em andamento', 'ao vivo', 'live', 'intervalo', '1° tempo', '2° tempo']
                            if pd.notnull(evento['Hora']):
                                st.markdown(f"<div class='data-hora-container'>{evento['Hora'].strftime('%d.%m.%Y %H:%M')}</div>", unsafe_allow_html=True)
                            cols = st.columns([1, 1, 1, 3, 2, 2])
                            with cols[0]:
                                st.markdown(f"<span class='live'>{status}</span>" if is_live else status, unsafe_allow_html=True)
                            with cols[1]:
                                tempo = "Encerrado" if evento['Status'].lower() in ['encerrado', 'concluído'] else \
                                        evento['TempoEvento'] if pd.notnull(evento['TempoEvento']) else '-'
                                st.markdown(f"<div class='tempo-evento'>{tempo}</div>", unsafe_allow_html=True)
                            with cols[2]:
                                st.markdown(f"<a href='{evento['Link']}' target='_blank'>Link do evento</a>", unsafe_allow_html=True)
                            with cols[3]:
                                st.markdown(f"{evento['HomeTeam']} {evento['HomeScore']} - {evento['AwayScore']} {evento['AwayTeam']}")
                            with cols[4]:
                                odds = get_valid_odds(evento)  # Busca odds válidas
                                c1, c2, c3 = st.columns(3)
                                for col, odd in zip([c1, c2, c3], odds):
                                    with col:
                                        st.markdown(f"<div class='odd-value'>{odd}</div>", unsafe_allow_html=True)
                            with cols[5]:
                                tempo_decorrido = time.time() - ciclo_inicio
                                progresso = min(tempo_decorrido / 120, 1.0)
                                st.progress(progresso)
                                st.write(f"{int(progresso * 100)}%")
                            st.markdown("<hr style='margin:2px 0; opacity:0.3;'>", unsafe_allow_html=True)

            # Loop para atualizar a barra de progresso em tempo real
            while time.time() - ciclo_inicio < 120:
                with placeholder_eventos.container():
                    if dados.empty:
                        st.info("Nenhum evento ativo encontrado até agora.")
                    else:
                        for torneio in dados['Informacoes_do_Torneio'].unique():
                            st.markdown(f"<div class='liga-header'>{torneio}</div>", unsafe_allow_html=True)
                            for _, evento in dados[dados['Informacoes_do_Torneio'] == torneio].iterrows():
                                status = formatar_status(evento['Status'], evento['Hora'])
                                is_live = evento['Status'].lower() in ['em andamento', 'ao vivo', 'live', 'intervalo', '1° tempo', '2° tempo']
                                if pd.notnull(evento['Hora']):
                                    st.markdown(f"<div class='data-hora-container'>{evento['Hora'].strftime('%d.%m.%Y %H:%M')}</div>", unsafe_allow_html=True)
                                cols = st.columns([1, 1, 1, 3, 2, 2])
                                with cols[0]:
                                    st.markdown(f"<span class='live'>{status}</span>" if is_live else status, unsafe_allow_html=True)
                                with cols[1]:
                                    tempo = "Encerrado" if evento['Status'].lower() in ['encerrado', 'concluído'] else \
                                            evento['TempoEvento'] if pd.notnull(evento['TempoEvento']) else '-'
                                    st.markdown(f"<div class='tempo-evento'>{tempo}</div>", unsafe_allow_html=True)
                                with cols[2]:
                                    st.markdown(f"<a href='{evento['Link']}' target='_blank'>Link do evento</a>", unsafe_allow_html=True)
                                with cols[3]:
                                    st.markdown(f"{evento['HomeTeam']} {evento['HomeScore']} - {evento['AwayScore']} {evento['AwayTeam']}")
                                with cols[4]:
                                    odds = get_valid_odds(evento)
                                    c1, c2, c3 = st.columns(3)
                                    for col, odd in zip([c1, c2, c3], odds):
                                        with col:
                                            st.markdown(f"<div class='odd-value'>{odd}</div>", unsafe_allow_html=True)
                                with cols[5]:
                                    tempo_decorrido = time.time() - ciclo_inicio
                                    progresso = min(tempo_decorrido / 120, 1.0)
                                    st.progress(progresso)
                                    st.write(f"{int(progresso * 100)}%")
                                st.markdown("<hr style='margin:2px 0; opacity:0.3;'>", unsafe_allow_html=True)
                time.sleep(1)  # Atualiza a cada segundo

    except Exception as e:
        st.error(f"Erro na execução: {e}")
    finally:
        fechar_navegador()