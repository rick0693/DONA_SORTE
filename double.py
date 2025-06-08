import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import datetime
import time
import json
import os
import subprocess

# Configurações globais
DB_NAME = 'blaze_history.db'
POLLING_INTERVAL = 1  # Intervalo de verificação em segundos
CONFIG_PATH = 'config.json'

class BlazeInterface:
    def __init__(self):
        self.db_name = DB_NAME
        self.ultimo_timestamp = None
        # Inicializar session_state para o processo do bot e estado do toggle
        if 'bot_process' not in st.session_state:
            st.session_state.bot_process = None
        if 'bot_running' not in st.session_state:
            st.session_state.bot_running = False
        if 'config_saved' not in st.session_state:
            st.session_state.config_saved = False
        if 'show_main_interface' not in st.session_state:
            st.session_state.show_main_interface = False

    def mapear_cor_para_texto(self, cor):
        """Converte o número da cor para texto para exibição no frontend."""
        if cor is None:
            return "N/A"
        if cor == 1:
            return "Vermelho"
        elif cor == 2:
            return "Preto"
        elif cor == 0:
            return "Branco"
        else:
            return "Desconhecido"

    def carregar_ultimos_2880(self):
        """Carrega os últimos 2880 registros para análise."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT "Data/Hora (BRT)", Cor 
                FROM blaze_history 
                ORDER BY "Data/Hora (BRT)" DESC 
                LIMIT 2880
            ''')
            dados = cursor.fetchall()
            conn.close()
            
            df = pd.DataFrame(dados, columns=['Data/Hora (BRT)', 'Cor'])
            df['Data/Hora (BRT)'] = pd.to_datetime(df['Data/Hora (BRT)'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            if df['Data/Hora (BRT)'].isna().any():
                st.warning("Alguns registros têm formato de data inválido em blaze_history.")
            return df.dropna()
        except Exception as e:
            st.error(f"Erro ao carregar os últimos 2880 registros: {str(e)}")
            return pd.DataFrame()

    def carregar_historico_apostas(self, limite=100):
        """Carrega o histórico de apostas do banco de dados e converte cores para texto."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT "Data/Hora (BRT)", Cor, Roll, Status, Entrada, Dica, Origem_Dica 
                FROM historico_apostas_blaze 
                ORDER BY "Data/Hora (BRT)" DESC 
                LIMIT ?
            ''', (limite,))
            dados = cursor.fetchall()
            conn.close()
            
            if not dados:
                st.info("Nenhum registro encontrado em historico_apostas_blaze.")
                return pd.DataFrame(columns=["Data/Hora (BRT)", "Cor", "Roll", "Status", "Entrada", "Dica", "Origem_Dica"])
            
            df = pd.DataFrame(dados, columns=["Data/Hora (BRT)", "Cor", "Roll", "Status", "Entrada", "Dica", "Origem_Dica"])
            df['Cor'] = df['Cor'].apply(self.mapear_cor_para_texto)
            df['Dica'] = df['Dica'].apply(self.mapear_cor_para_texto)
            df['Status'] = df['Status'].fillna('N/A')
            df['Origem_Dica'] = df['Origem_Dica'].fillna('N/A')
            df['Entrada'] = df['Entrada'].apply(lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "N/A")
            return df
        except Exception as e:
            st.error(f"Erro ao carregar histórico de apostas: {str(e)}")
            return pd.DataFrame()

    def carregar_historico_horas(self):
        """Calcula o histórico de horas diretamente de historico_apostas_blaze."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            # Converter DD/MM/YYYY HH:MM:SS para agrupamento por hora
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', 
                        substr("Data/Hora (BRT)", 7, 4) || '-' || 
                        substr("Data/Hora (BRT)", 4, 2) || '-' || 
                        substr("Data/Hora (BRT)", 1, 2) || 
                        substr("Data/Hora (BRT)", 11)
                    ) as Hora,
                    SUM(CASE WHEN Status = 'Ganhou' THEN 1 ELSE 0 END) as Vitorias,
                    SUM(CASE WHEN Status = 'Perdeu' THEN 1 ELSE 0 END) as Derrotas
                FROM historico_apostas_blaze
                WHERE Status IN ('Ganhou', 'Perdeu')
                GROUP BY strftime('%Y-%m-%d %H:00:00', 
                        substr("Data/Hora (BRT)", 7, 4) || '-' || 
                        substr("Data/Hora (BRT)", 4, 2) || '-' || 
                        substr("Data/Hora (BRT)", 1, 2) || 
                        substr("Data/Hora (BRT)", 11)
                    )
                ORDER BY Hora DESC
                LIMIT 24
            ''')
            dados = cursor.fetchall()
            
            historico = []
            for hora, vitorias, derrotas in dados:
                cursor.execute('''
                    SELECT Status
                    FROM historico_apostas_blaze
                    WHERE strftime('%Y-%m-%d %H:00:00', 
                            substr("Data/Hora (BRT)", 7, 4) || '-' || 
                            substr("Data/Hora (BRT)", 4, 2) || '-' || 
                            substr("Data/Hora (BRT)", 1, 2) || 
                            substr("Data/Hora (BRT)", 11)
                        ) = ?
                    AND Status IN ('Ganhou', 'Perdeu')
                    ORDER BY "Data/Hora (BRT)" ASC
                ''', (hora,))
                status_list = [row[0] for row in cursor.fetchall()]
                
                max_perdas = 0
                current_perdas = 0
                for status in status_list:
                    if status == "Perdeu":
                        current_perdas += 1
                        max_perdas = max(max_perdas, current_perdas)
                    else:
                        current_perdas = 0
                
                historico.append({
                    'Hora': hora,
                    'Vitórias': vitorias or 0,
                    'Derrotas': derrotas or 0,
                    'Maior Seq. de Perdas': max_perdas
                })
            
            conn.close()
            if not historico:
                st.info("Nenhum dado de vitórias/derrotas encontrado em historico_apostas_blaze.")
            return historico
        except Exception as e:
            st.error(f"Erro ao carregar histórico de horas: {str(e)}")
            return []

    def calcular_maior_sequencia_vitorias(self):
        """Calcula a maior sequência de vitórias consecutivas no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Status 
                FROM historico_apostas_blaze 
                WHERE Status IN ('Ganhou', 'Perdeu')
                ORDER BY "Data/Hora (BRT)" ASC
            ''')
            dados = cursor.fetchall()
            conn.close()
            
            max_vitorias = 0
            current_vitorias = 0
            for status, in dados:
                if status == "Ganhou":
                    current_vitorias += 1
                    max_vitorias = max(max_vitorias, current_vitorias)
                else:
                    current_vitorias = 0
            return max_vitorias
        except Exception as e:
            st.error(f"Erro ao calcular maior sequência de vitórias: {str(e)}")
            return 0

    def calcular_maior_sequencia_perdas(self):
        """Calcula a maior sequência de perdas consecutivas no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Status 
                FROM historico_apostas_blaze 
                WHERE Status IN ('Ganhou', 'Perdeu')
                ORDER BY "Data/Hora (BRT)" ASC
            ''')
            dados = cursor.fetchall()
            conn.close()
            
            max_perdas = 0
            current_perdas = 0
            for status, in dados:
                if status == "Perdeu":
                    current_perdas += 1
                    max_perdas = max(max_perdas, current_perdas)
                else:
                    current_perdas = 0
            return max_perdas
        except Exception as e:
            st.error(f"Erro ao calcular maior sequência de perdas: {str(e)}")
            return 0

    def calcular_metricas(self):
        """Calcula métricas atuais com base no histórico de apostas."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Entrada, Status, Cor, Dica, Origem_Dica, Roll 
                FROM historico_apostas_blaze 
                ORDER BY "Data/Hora (BRT)" DESC 
                LIMIT 1
            ''')
            ultima_aposta = cursor.fetchone()
            
            cursor.execute('''
                SELECT COUNT(*) 
                FROM historico_apostas_blaze 
                WHERE Status = 'Ganhou'
            ''')
            ganhos_totais = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) 
                FROM historico_apostas_blaze 
                WHERE Status = 'Perdeu'
            ''')
            perdas_totais = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'valor_atual': float(ultima_aposta[0]) if ultima_aposta and ultima_aposta[0] is not None else 0.10,
                'ganhos_totais': ganhos_totais or 0,
                'perdas_totais': perdas_totais or 0,
                'ultima_cor': ultima_aposta[2] if ultima_aposta else None,
                'ultima_dica': ultima_aposta[3] if ultima_aposta else None,
                'ultima_origem': ultima_aposta[4] if ultima_aposta else None,
                'ultimo_roll': ultima_aposta[5] if ultima_aposta else None,
                'ultimo_status': ultima_aposta[1] if ultima_aposta else "N/A"
            }
        except Exception as e:
            st.error(f"Erro ao calcular métricas: {str(e)}")
            return {
                'valor_atual': 0.50,
                'ganhos_totais': 0,
                'perdas_totais': 0,
                'ultima_cor': None,
                'ultima_dica': None,
                'ultima_origem': None,
                'ultimo_roll': None,
                'ultimo_status': "N/A"
            }

    def get_ultimo_timestamp(self):
        """Obtém o timestamp mais recente da tabela historico_apostas_blaze."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT "Data/Hora (BRT)" 
                FROM historico_apostas_blaze 
                ORDER BY "Data/Hora (BRT)" DESC 
                LIMIT 1
            ''')
            resultado = cursor.fetchone()
            conn.close()
            return resultado[0] if resultado else None
        except Exception as e:
            st.error(f"Erro ao obter último timestamp: {str(e)}")
            return None

    def load_config(self):
        """Carrega o config.json da pasta atual."""
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                # Garantir que bot_status exista
                if 'bot_status' not in config:
                    config['bot_status'] = 'DESATIVADO'
                    self.save_config(config)
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            st.error(f"Erro ao carregar config.json: {str(e)}. Usando configurações padrão.")
            default_config = {
                "estrategias_selecionadas": ["maior", "menor", "alternativa", "aleatoria"],
                "limite_perdas_consecutivas": 4,
                "limite_ganhos_totais": 10,
                "acao_perdas_consecutivas": "Apenas Avisar Sonoramente",
                "modo_espectador": False,
                "valor_inicial": 0.10,
                "rodadas_aguardar": 5,
                "bot_status": "DESATIVADO"
            }
            self.save_config(default_config)
            return default_config

    def save_config(self, config):
        """Salva o config.json na pasta atual."""
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            st.error(f"Erro ao salvar config.json: {str(e)}")

    def start_bot(self):
        """Inicia o blaze_bot.py em um processo separado."""
        config = self.load_config()
        if config['bot_status'] == 'ATIVADO' or (st.session_state.bot_process is not None and st.session_state.bot_process.poll() is None):
            st.error("Um bot já está em execução. Desative o bot atual antes de iniciar outro.")
            return False
        try:
            st.session_state.bot_process = subprocess.Popen(
                ['python', 'blaze_bot.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE  # Novo terminal no Windows
            )
            st.session_state.bot_running = True
            config['bot_status'] = 'ATIVADO'
            self.save_config(config)
            st.success("Bot iniciado com sucesso!")
            return True
        except Exception as e:
            st.error(f"Erro ao iniciar o bot: {str(e)}")
            st.session_state.bot_running = False
            return False

    def stop_bot(self):
        """Para o processo do blaze_bot.py e volta para configurações."""
        config = self.load_config()
        if st.session_state.bot_process is not None and st.session_state.bot_process.poll() is None:
            try:
                st.session_state.bot_process.terminate()
                st.session_state.bot_process.wait(timeout=5)
                st.session_state.bot_process = None
                st.session_state.bot_running = False
                config['bot_status'] = 'DESATIVADO'
                self.save_config(config)
                st.session_state.show_main_interface = False  # Voltar para configurações
                st.success("Bot parado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao parar o bot: {str(e)}")
        else:
            st.warning("Nenhum bot em execução.")
            config['bot_status'] = 'DESATIVADO'
            self.save_config(config)
            st.session_state.bot_running = False
            st.session_state.show_main_interface = False  # Voltar para configurações

    def exibir_configuracoes(self):
        """Exibe a interface de configurações para editar o config.json."""
        st.title("Configurações do Bot")
        
        config = self.load_config()
        
        estrategias = st.multiselect(
            "Estratégias Selecionadas",
            options=["maior", "menor", "alternativa", "aleatoria"],
            default=config.get("estrategias_selecionadas", ["maior", "menor", "alternativa", "aleatoria"]),
            help="Selecione as estratégias que o bot usará."
        )
        
        limite_perdas = st.number_input(
            "Limite de Perdas Consecutivas",
            min_value=1,
            value=config.get("limite_perdas_consecutivas", 4),
            step=1,
            help="Número máximo de perdas consecutivas antes de tomar uma ação."
        )
        
        limite_ganhos = st.number_input(
            "Limite de Ganhos Totais",
            min_value=1,
            value=config.get("limite_ganhos_totais", 10),
            step=1,
            help="Número máximo de vitórias antes de pausar o bot."
        )
        
        acao_perdas = st.selectbox(
            "Ação Após Perdas Consecutivas",
            options=[
                "Apenas Avisar Sonoramente",
                "Parar e Continuar na Próxima Hora",
                "Aguardar Sequência Vulnerável",
                "Aguardar N Rodadas"
            ],
            index=[
                "Apenas Avisar Sonoramente",
                "Parar e Continuar na Próxima Hora",
                "Aguardar Sequência Vulnerável",
                "Aguardar N Rodadas"
            ].index(config.get("acao_perdas_consecutivas", "Apenas Avisar Sonoramente")),
            help="Ação a tomar quando atingir o limite de perdas consecutivas."
        )
        
        rodadas_aguardar = st.number_input(
            "Rodadas a Aguardar (se aplicável)",
            min_value=1,
            value=config.get("rodadas_aguardar", 5),
            step=1,
            help="Número de rodadas a esperar se a ação for 'Aguardar N Rodadas'."
        )
        
        modo_espectador = st.checkbox(
            "Modo Espectador",
            value=config.get("modo_espectador", False),
            help="Se ativado, o bot não faz apostas reais, apenas simula."
        )
        
        valor_inicial = st.number_input(
            "Valor Inicial da Aposta",
            min_value=0.01,
            value=config.get("valor_inicial", 0.10),
            step=0.01,
            format="%.2f",
            help="Valor inicial de cada aposta."
        )
        
        if st.button("Salvar Configurações"):
            new_config = {
                "estrategias_selecionadas": estrategias,
                "limite_perdas_consecutivas": limite_perdas,
                "limite_ganhos_totais": limite_ganhos,
                "acao_perdas_consecutivas": acao_perdas,
                "modo_espectador": modo_espectador,
                "valor_inicial": valor_inicial,
                "rodadas_aguardar": rodadas_aguardar,
                "bot_status": config.get("bot_status", "DESATIVADO")
            }
            self.save_config(new_config)
            st.session_state.config_saved = True
            st.session_state.show_main_interface = True  # Ir para interface principal
            st.success("Configurações salvas com sucesso!")
            st.rerun()  # Recarregar para mostrar interface principal

    def exibir_interface(self):
        """Exibe a interface principal ou configurações com base no estado."""
        config = self.load_config()
        
        if not st.session_state.show_main_interface:
            self.exibir_configuracoes()
            return
        
        st.title("Bot da Sara")
        
        bot_toggle = st.toggle(
            "Ativar Bot",
            value=st.session_state.bot_running,
            key="bot_toggle"
        )
        
        if bot_toggle and not st.session_state.bot_running:
            self.start_bot()
        elif not bot_toggle and st.session_state.bot_running:
            self.stop_bot()
            st.rerun()  # Forçar rerender para voltar às configurações
        
        placeholder_metrics = st.empty()
        placeholder_graficos = st.empty()
        placeholder_tabela = st.empty()
        
        contador = 0
        while True:
            if not st.session_state.show_main_interface:
                break  # Sair do loop se voltar para configurações
            
            novo_timestamp = self.get_ultimo_timestamp()
            
            if novo_timestamp != self.ultimo_timestamp:
                self.ultimo_timestamp = novo_timestamp
                
                with placeholder_metrics.container():
                    st.markdown("### Métricas do Bot")
                    metricas = self.calcular_metricas()
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Valor Atual", f"R$ {metricas['valor_atual']:.2f}", help="Valor atual da aposta")
                    col2.metric("Ganhos Totais", metricas['ganhos_totais'], help="Total de vitórias")
                    col3.metric("Perdas Totais", metricas['perdas_totais'], help="Total de derrotas")
                    col4.metric("Maior Seq. de Vitórias", self.calcular_maior_sequencia_vitorias(), help="Maior sequência de vitórias consecutivas registrada")
                    col5.metric("Maior Seq. de Perdas", self.calcular_maior_sequencia_perdas(), help="Maior sequência de perdas consecutivas registrada")
                    
                    col6, col7, col8, col9, col10 = st.columns(5)
                    cor_sorteada = self.mapear_cor_para_texto(metricas['ultima_cor']) if metricas['ultima_cor'] is not None else "N/A"
                    dica_atual = self.mapear_cor_para_texto(metricas['ultima_dica']) if metricas['ultima_dica'] is not None else "N/A"
                    col6.metric("Dica Atual", dica_atual, metricas['ultima_origem'] or "", help="Dica atual e sua origem")
                    col7.metric("Cor Sorteada", cor_sorteada, help="Cor do último sorteio")
                    col8.metric("Número Sorteado", metricas['ultimo_roll'] if metricas['ultimo_roll'] is not None else "N/A", help="Número do último sorteio")
                    col9.metric("Resultado", metricas['ultimo_status'] if metricas['ultimo_status'] else "N/A", help="Resultado da última aposta")
                    col10.metric("Modo", "Ativo" if st.session_state.bot_running else "Inativo", help="Modo atual do bot")

                with placeholder_graficos.container():
                    st.markdown("### Gráficos")
                    col_g1, col_g2 = st.columns(2)
                    
                    with col_g1:
                        dados_2880 = self.carregar_ultimos_2880()
                        if not dados_2880.empty:
                            dados_2880['Hora'] = dados_2880['Data/Hora (BRT)'].dt.floor('H')
                            contagem_por_hora = dados_2880.groupby(['Hora', 'Cor']).size().unstack(fill_value=0)
                            contagem_por_hora = contagem_por_hora.reset_index()
                            contagem_por_hora.columns = ['Hora', 'Branco', 'Vermelho', 'Preto']
                            contagem_long = contagem_por_hora.melt(id_vars=['Hora'], 
                                                                value_vars=['Branco', 'Vermelho', 'Preto'],
                                                                var_name='Cor', value_name='Contagem')
                            fig_cores = px.line(contagem_long, x='Hora', y='Contagem', color='Cor',
                                                title='Contagem de Cores (Últimos 2880 Registros)',
                                                labels={'Contagem': 'Contagem'},
                                                markers=True,
                                                text='Contagem',
                                                color_discrete_map={
                                                    'Vermelho': 'red',
                                                    'Preto': 'black',
                                                    'Branco': 'blue'
                                                })
                            fig_cores.update_traces(textposition='top center')
                            fig_cores.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="Contagem",
                                legend_title="Cor",
                                xaxis=dict(tickformat="%H:%M\n%d/%m/%Y", tickangle=45),
                                height=400
                            )
                            st.plotly_chart(fig_cores, use_container_width=True, key=f"fig_cores_{contador}")
                        else:
                            st.info("Nenhum dado disponível para o gráfico de cores.")

                    with col_g2:
                        df_horas = pd.DataFrame(self.carregar_historico_horas())
                        if not df_horas.empty:
                            df_horas['Hora'] = pd.to_datetime(df_horas['Hora'], format='%Y-%m-%d %H:00:00', errors='coerce')
                            df_horas_melted = df_horas.melt(id_vars=['Hora'], value_vars=['Vitórias', 'Derrotas'], 
                                                            var_name='Resultado', value_name='Quantidade')
                            fig_horas = px.bar(df_horas_melted, x='Hora', y='Quantidade', color='Resultado',
                                            title='Histórico de Horas (Vitórias e Derrotas)',
                                            labels={'Quantidade': 'Quantidade', 'Resultado': 'Resultado'},
                                            barmode='group',
                                            color_discrete_map={'Vitórias': 'green', 'Derrotas': 'red'},
                                            text='Quantidade')
                            fig_horas.update_traces(textposition='auto')
                            fig_horas.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="Quantidade",
                                legend_title="Resultado",
                                xaxis=dict(tickformat="%H:%M\n%d/%m/%Y", tickangle=45),
                                height=400
                            )
                            st.plotly_chart(fig_horas, use_container_width=True, key=f"fig_horas_{contador}")
                        else:
                            st.info("Nenhum dado disponível para o gráfico de histórico de horas.")
                
                with placeholder_tabela.container():
                    st.subheader("Histórico de Apostas")
                    df_apostas = self.carregar_historico_apostas()
                    st.dataframe(df_apostas, use_container_width=True)
                
                contador += 1

            time.sleep(POLLING_INTERVAL)

def main():
    """Função principal para iniciar a interface."""
    interface = BlazeInterface()
    config = interface.load_config()
    if config['bot_status'] == 'ATIVADO':
        st.session_state.show_main_interface = True
        st.session_state.bot_running = True
    interface.exibir_interface()

if __name__ == "__main__":
    main()