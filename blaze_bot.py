import requests
import datetime
import json
import time
import pytz
import sqlite3
import numpy as np
import random
import os

#conta Sara

# Configurações globais
import os

# Configurações globais
NOME_SITE = "blaze"
DB_NAME = 'blaze_history.db'
FINANCEIRO_DB = os.path.join(os.path.dirname(__file__), 'financeiro.db')
BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')
URL_BASE = 'https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1'
URL_HISTORY = 'https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/history/1'
URL_APOSTA = 'https://blaze.bet.br/api/singleplayer-originals/originals/roulette_bets'

HEADERS_COLETA = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'referer': 'https://blaze.bet.br/pt/games/double?modal=double_history-v2_index&roomId=2',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# Headers para aposta (do Código 2)
HEADERS_APOSTA = {

    'accept': 'application/json, text/plain, */*',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjIwMjUyOSwiaXNSZWZyZXNoVG9rZW4iOmZhbHNlLCJibG9ja3MiOltdLCJ1dWlkIjoiNDc2OWZmMjYtMzkzOC00YTg2LWEwY2ItMDJjZTQ5NTc5YTYxIiwiaWF0IjoxNzQ4MjAwMDc0LCJleHAiOjE3NTMzODQwNzR9.p4CEUoeuOW1Eri1bJPyT9qvaWjp3XlZIEZPBtrJBdf8',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://blaze.bet.br',
    'priority': 'u=1, i',
    'referer': 'https://blaze.bet.br/ap/games/double',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'x-client-version': '3086938f4',
    'x-session-id': '5rV43PpaNk',

}

# Cookies para aposta (do Código 2)
COOKIES_APOSTA = {
    'AMP_MKTG_c9c53a1635': 'JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE',
    '_gid': 'GA1.3.2134175161.1744671391',
    '_ga': 'GA1.1.89495140.1744671391',
    '_gat': '1',
    'kwai_uuid': 'b446cceab52c84c62826d60cc6f4dc63',
    '__zlcmid': '1RAnXagyEa3Xjvh',
    'accept_policy_regulation': '1',
    '_gcl_au': '1.1.562150456.1744671392.1251269690.1744671400.1744671399',
    'AMP_c9c53a1635': 'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhMWUzOTYwYi02YWE2LTQxZDEtYjk0Zi00MjYwOTMyNzcxNTclMjIlMkMlMjJ1c2VySWQlMjIlM0E1MjY1NiUyQyUyMnNlc3Npb25JZCUyMiUzQTE3NDQ2NzEzOTA4NzklMkMlMjJvcHRPdXQlMjIlM0FmYWxzZSUyQyUyMmxhc3RFdmVudFRpbWUlMjIlM0ExNzQ0NjcxMzkwOTg3JTJDJTIybGFzdEV2ZW50SWQlMjIlM0EwJTdE',
    '_ga_WS0MD548L3': 'GS1.1.1744671391.1.1.1744671440.0.0.0',
}

# Estratégias de aposta
ESTRATEGIA_MAIOR_OCORRENCIA = {
    20: [19], 30: [21], 40: [25, 23, 24], 50: [26, 28], 60: [29, 31, 32], 70: [35, 33],
    80: [35], 90: [35, 39], 100: [37], 110: [38, 40], 130: [44, 43], 140: [47], 150: [45],
    160: [52], 180: [48, 51, 52], 190: [52], 200: [47], 210: [52], 220: [54], 250: [56, 57],
    260: [60], 270: [60], 280: [62, 57, 61], 290: [62, 64, 56], 300: [59], 310: [59],
    320: [61, 64], 330: [62], 350: [62], 370: [64], 380: [64, 66, 68], 390: [64, 67, 68, 69],
    400: [65, 64], 410: [67]
}

ESTRATEGIA_MENOR_OCORRENCIA = {
    20: [16, 17], 30: [22, 20], 40: [26, 25, 23], 50: [26], 60: [31], 70: [33], 80: [32, 34],
    90: [34, 37], 100: [32], 150: [40], 160: [44], 170: [43, 44, 46], 180: [43, 47],
    190: [50, 51], 200: [50, 51], 220: [48], 250: [52], 270: [53, 59], 280: [60], 290: [53],
    300: [64], 310: [64, 61], 320: [59], 330: [60, 61], 340: [63], 360: [59, 61], 370: [69],
    380: [61], 390: [63, 65], 400: [63], 410: [63, 69, 71], 430: [68, 69, 71], 440: [64, 70],
    450: [68], 470: [71], 480: [70, 71, 72], 490: [72], 500: [70, 72]
}

class BlazeCollectorAndBot:
    def __init__(self):
        """Inicializa o bot com configurações carregadas do config.json."""
        # Caminho para o config.json
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar config.json: {str(e)}. Usando configurações padrão.")
            config = {
                "estrategias_selecionadas": ["maior", "menor", "alternativa"],
                "limite_perdas_consecutivas": 3,
                "limite_ganhos_totais": 1,
                "acao_perdas_consecutivas": "Apenas Avisar Sonoramente",
                "modo_espectador": False,
                "valor_inicial": 3.20,
                "rodadas_aguardar": 5
            }

        self.data_atual = datetime.datetime.now(BRASILIA_TZ).replace(tzinfo=None)
        self.server_seeds_existentes = set()
        self.dados_recentes = []
        self.setup_database()
        
        # Carregar configurações
        self.estrategias_selecionadas = config.get("estrategias_selecionadas", ["maior", "menor", "alternativa"])
        self.limite_perdas_consecutivas = config.get("limite_perdas_consecutivas", 4)
        self.limite_ganhos_totais = config.get("limite_ganhos_totais", 10)
        self.acao_perdas_consecutivas = config.get("acao_perdas_consecutivas", "Apenas Avisar Sonoramente")
        self.modo_espectador = False  # Desativado para apostas reais
        self.valor_inicial = config.get("valor_inicial", 3.20)
        self.rodadas_aguardar = config.get("rodadas_aguardar", 5)
        
        # Variáveis de aposta
        self.valor_atual = self.carregar_valor_inicial()
        self.ultima_entrada_com_dica = self.valor_inicial
        self.ultima_rodada_horario = None
        self.modo_busca_rapida = True
        self.janela_maxima = 500
        self.fila_de_espera = []
        self.saldo = 1000.0
        
        # Variáveis para controle por hora
        self.hora_atual = self.data_atual.replace(minute=0, second=0, microsecond=0)
        self.vitorias_na_hora = 0
        self.derrotas_na_hora = 0
        self.ganhos_consecutivos = 0
        self.perdas_consecutivas = 0
        self.max_perdas_consecutivas = 0
        self.ganhos_totais = 0
        self.perdas_totais = 0
        self.historico_horas = self.carregar_historico_horas()
        
        # Estatísticas da hora atual
        self.hora_atual_stats = {
            'Hora': self.hora_atual.strftime('%Y-%m-%d %H:00'),
            'Vitórias': 0,
            'Maior Seq. de Perdas': 0
        }
        
        # Controle de rodadas aguardadas
        self.rodadas_aguardadas = 0
        self.pausado = False
        self.aguardando_sequencia_vulneravel = False

    def setup_database(self):
        """Configura os bancos de dados necessários e ajusta a estrutura das tabelas."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blaze_history (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                Site TEXT,
                ID TEXT,
                "Data/Hora (BRT)" TEXT,
                Cor INTEGER,
                Roll INTEGER,
                "Server_Seed" TEXT UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_apostas_blaze (
                "Data/Hora (BRT)" TEXT,
                Cor INTEGER,
                Roll INTEGER,
                "Server_Seed" TEXT,
                Status TEXT,
                Entrada REAL,
                Dica INTEGER,
                Origem_Dica TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_horas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Hora TEXT UNIQUE,
                Vitorias INTEGER,
                Max_Perdas_Consecutivas INTEGER
            )
        ''')

        try:
            cursor.execute('ALTER TABLE historico_horas ADD COLUMN Derrotas INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

        cursor.execute("SELECT \"Server_Seed\" FROM blaze_history")
        self.server_seeds_existentes = {row[0] for row in cursor.fetchall()}
        conn.commit()
        conn.close()

        conn = sqlite3.connect(FINANCEIRO_DB)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cadastro_receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                data_evento TEXT,
                hora_evento TEXT,
                valor REAL
            )
        ''')
        conn.commit()
        conn.close()

    def carregar_valor_inicial(self):
        """Carrega o valor inicial da última aposta registrada."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''SELECT Entrada FROM historico_apostas_blaze 
                            WHERE Status IS NOT NULL AND Status != 'Iniciando' 
                            ORDER BY "Data/Hora (BRT)" DESC LIMIT 1''')
            resultado = cursor.fetchone()
            conn.close()
            return float(resultado[0]) if resultado and resultado[0] else self.valor_inicial
        except Exception:
            return self.valor_inicial

    def carregar_historico_horas(self):
        """Carrega o histórico de horas do banco de dados, calculando vitórias e derrotas."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT "Data/Hora (BRT)", Status 
                FROM historico_apostas_blaze 
                WHERE Status IN ('Ganhou', 'Perdeu')
            ''')
            dados = cursor.fetchall()
            
            historico = {}
            for data_hora, status in dados:
                dt = datetime.datetime.strptime(data_hora, '%d/%m/%Y %H:%M:%S')
                hora = dt.replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:00')
                if hora not in historico:
                    historico[hora] = {'Vitórias': 0, 'Derrotas': 0, 'Maior Seq. de Perdas': 0}
                if status == "Ganhou":
                    historico[hora]['Vitórias'] += 1
                elif status == "Perdeu":
                    historico[hora]['Derrotas'] += 1
            
            cursor.execute('''
                SELECT "Data/Hora (BRT)", Status 
                FROM historico_apostas_blaze 
                WHERE Status IN ('Ganhou', 'Perdeu')
                ORDER BY "Data/Hora (BRT)" ASC
            ''')
            dados = cursor.fetchall()
            conn.close()
            
            current_hour = None
            current_perdas = 0
            max_perdas_por_hora = {}
            for data_hora, status in dados:
                dt = datetime.datetime.strptime(data_hora, '%d/%m/%Y %H:%M:%S')
                hora = dt.replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:00')
                if hora != current_hour:
                    if current_hour:
                        max_perdas_por_hora[current_hour] = max(max_perdas_por_hora.get(current_hour, 0), current_perdas)
                    current_hour = hora
                    current_perdas = 0
                if status == "Perdeu":
                    current_perdas += 1
                else:
                    max_perdas_por_hora[hora] = max(max_perdas_por_hora.get(hora, 0), current_perdas)
                    current_perdas = 0
            if current_hour:
                max_perdas_por_hora[current_hour] = max(max_perdas_por_hora.get(current_hour, 0), current_perdas)
            
            historico_lista = []
            for hora, stats in historico.items():
                stats['Hora'] = hora
                stats['Maior Seq. de Perdas'] = max_perdas_por_hora.get(hora, 0)
                historico_lista.append(stats)
            
            return historico_lista
        except Exception as e:
            print(f"Erro ao carregar histórico: {str(e)}")
            return []

    def salvar_historico_horas(self, hora, vitorias, derrotas, max_perdas):
        """Salva ou atualiza as estatísticas de uma hora específica."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO historico_horas (Hora, Vitorias, Derrotas, Max_Perdas_Consecutivas)
            VALUES (?, ?, ?, ?)
        ''', (hora, vitorias, derrotas, max_perdas))
        conn.commit()
        conn.close()

    def fazer_requisicao(self, url, timeout=4):
        """Faz uma requisição HTTP com tratamento de erros para coleta."""
        try:
            response = requests.get(url, headers=HEADERS_COLETA, timeout=timeout)
            response.raise_for_status()
            return json.loads(response.text)
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Erro na requisição de coleta: {str(e)}. Tentando novamente em 4 segundos...")
            time.sleep(4)
            return None

    def fazer_aposta(self, amount, color):
        """Faz uma aposta real no site da Blaze."""
        json_data = {
            'amount': f"{amount:.2f}",
            'currency_type': 'BRL',
            'color': color,
            'free_bet': False,
            'room_id': 1,
            'username': 'Sara Sampaio',
            'rank': 'gold',
            'wallet_id': 3653021,
        }
        
        print(f"Tentando fazer aposta: amount={json_data['amount']}, color={json_data['color']}")
        while True:
            try:
                response = requests.post(
                    URL_APOSTA,
                    cookies=COOKIES_APOSTA,
                    headers=HEADERS_APOSTA,
                    json=json_data,
                    timeout=10
                )
                response.raise_for_status()
                print(f"Aposta realizada com sucesso: {response.json()}")
                return True
            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"Erro ao fazer aposta: {str(e)}. Tentando novamente em 3 segundos...")
                time.sleep(3)

    def processar_registros(self, dados):
        """Processa os dados recebidos da API."""
        novos_registros = []
        for item in dados['records'] if 'records' in dados else [dados]:
            if item['server_seed'] not in self.server_seeds_existentes:
                data_utc = datetime.datetime.strptime(item['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                data_utc = pytz.UTC.localize(data_utc)
                data_brt = data_utc.astimezone(BRASILIA_TZ)
                
                novo_registro = {
                    'Site': NOME_SITE,
                    'ID': item['id'],
                    'Data/Hora (BRT)': data_brt.strftime('%d/%m/%Y %H:%M:%S'),
                    'Cor': item['color'],
                    'Roll': item['roll'],
                    'Server_Seed': item['server_seed']
                }
                novos_registros.append(novo_registro)
        return novos_registros

    def inserir_registros(self, registros):
        """Insere novos registros no banco de dados."""
        if not registros:
            return 0
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        novos = 0
        
        for registro in registros:
            try:
                cursor.execute('''
                    INSERT INTO blaze_history (Site, ID, "Data/Hora (BRT)", Cor, Roll, "Server_Seed")
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    registro['Site'], registro['ID'], registro['Data/Hora (BRT)'],
                    registro['Cor'], registro['Roll'], registro['Server_Seed']
                ))
                novos += 1
                self.server_seeds_existentes.add(registro['Server_Seed'])
            except sqlite3.IntegrityError:
                pass
                
        conn.commit()
        conn.close()
        return novos

    def coletar_dados_iniciais(self):
        """Coleta dados históricos iniciais da API."""
        print("Iniciando coleta de dados históricos...")
        pagina = 1
        while True:
            url = f'{URL_HISTORY}?page={pagina}'
            dados = self.fazer_requisicao(url)
            if not dados or not dados['records']:
                break
                
            novos_registros = self.processar_registros(dados)
            qtd_novos = self.inserir_registros(novos_registros)
            
            print(f"Página {pagina} coletada: {qtd_novos} novos registros salvos.")
            if qtd_novos == 0:
                break
                
            time.sleep(4)
            pagina += 1

    def carregar_dados_banco(self, limite=500):
        """Carrega os últimos dados do banco para análise."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT Cor FROM blaze_history ORDER BY row_id DESC LIMIT ?", (limite,))
            dados = cursor.fetchall()
            conn.close()
            return np.array([int(row[0]) for row in dados if row[0] is not None], dtype=np.int8)
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            return np.array([])

    def verificar_sequencia_vulneravel(self, cores):
        """Verifica se há uma sequência vulnerável nas últimas cores."""
        if len(cores) < 4:
            return False
        color1, color2, color3, color4 = cores[-4:]
        return (color1 == 1 and color2 == 1 and color3 == 1 and color4 == 2) or \
               (color1 == 2 and color2 == 2 and color3 == 2 and color4 == 1)

    def gerar_dica_alternativa(self, cores):
        """Gera uma dica alternativa baseada em padrões simples."""
        if len(cores) < 3:
            return None, None
        color1, color2, color3 = cores[-3:]
        padroes = {
            (1, 1, 1): (2, "VVV"), (2, 2, 2): (1, "PPP"),
            (1, 1, 2): (1, "VVP"), (2, 2, 1): (2, "PPV"),
            (1, 2, 2): (2, "VPP"), (2, 1, 1): (1, "PVV"),
            (1, 2, 1): (1, "VPV"), (2, 1, 2): (2, "PVP"),
            (0, None, None): (2, "Branco Terceiro"),
            (None, 0, None): (1, "Branco Penúltimo"),
            (None, None, 0): (1, "Branco Último")
        }
        for padrao, (dica, origem) in padroes.items():
            if (color1 == padrao[0] and (padrao[1] is None or color2 == padrao[1]) and 
                (padrao[2] is None or color3 == padrao[2])):
                return dica, f"Alternativa - {origem}"
        return None, None

    def gerar_dica_aleatoria(self):
        """Gera uma dica aleatória escolhendo entre vermelho (1) e preto (2)."""
        return random.choice([1, 2]), "Aleatória"

    def gerar_dica(self):
        """Gera uma dica de aposta com base nas estratégias selecionadas."""
        cores = self.carregar_dados_banco(self.janela_maxima)
        if len(cores) < 20:
            return None, None if not self.fila_de_espera else (self.fila_de_espera.pop(0), "Fila de Espera")

        if self.verificar_sequencia_vulneravel(cores):
            ultimos_50 = self.carregar_dados_banco(50)
            vermelhos = np.count_nonzero(ultimos_50 == 1)
            pretos = np.count_nonzero(ultimos_50 == 2)
            dica = 1 if vermelhos < pretos else 2
            return dica, "Sequência Vulnerável - Menor Frequência"

        dicas_encontradas = []
        estrategias = []
        if "maior" in self.estrategias_selecionadas:
            estrategias.append((ESTRATEGIA_MAIOR_OCORRENCIA, "Maior Ocorrência"))
        if "menor" in self.estrategias_selecionadas:
            estrategias.append((ESTRATEGIA_MENOR_OCORRENCIA, "Menor Ocorrência"))

        for estrategia, nome in estrategias:
            for janela, diferencas in estrategia.items():
                if janela > len(cores):
                    continue
                janela_cores = cores[-janela:]
                vermelhos = np.count_nonzero(janela_cores == 1)
                pretos = np.count_nonzero(janela_cores == 2)
                diferenca = abs(vermelhos - pretos)
                if diferenca in diferencas:
                    dica = 1 if (vermelhos > pretos if nome == "Maior Ocorrência" else vermelhos < pretos) else 2
                    dicas_encontradas.append((dica, f"{nome} | Janela: {janela}"))

        if dicas_encontradas:
            for i, (dica, origem) in enumerate(dicas_encontradas):
                if i > 0:
                    self.fila_de_espera.append(dica)
            return dicas_encontradas[0]
        
        if "aleatoria" in self.estrategias_selecionadas:
            return self.gerar_dica_aleatoria() if not self.fila_de_espera else (self.fila_de_espera.pop(0), "Fila de Espera")
        if "alternativa" in self.estrategias_selecionadas:
            return self.gerar_dica_alternativa(cores) if not self.fila_de_espera else (self.fila_de_espera.pop(0), "Fila de Espera")
        return None, None

    def salvar_aposta(self, registro, status, entrada, dica, origem_dica):
        """Salva uma aposta no banco de dados."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_apostas_blaze ("Data/Hora (BRT)", Cor, Roll, "Server_Seed", Status, Entrada, Dica, Origem_Dica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (registro['Data/Hora (BRT)'], registro['Cor'], registro['Roll'], registro['Server_Seed'],
              status, entrada, dica, origem_dica))
        conn.commit()
        conn.close()

    def registrar_vitoria(self, data_hora):
        """Registra uma vitória no banco financeiro."""
        data = data_hora.strftime('%Y-%m-%d')
        hora = data_hora.strftime('%H:%M:%S')
        conn = sqlite3.connect(FINANCEIRO_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cadastro_receitas (descricao, data_evento, hora_evento, valor)
            VALUES (?, ?, ?, ?)
        ''', ('rodada_blaze_double', data, hora, self.valor_inicial))
        conn.commit()
        conn.close()
        self.saldo += self.valor_inicial

    def atualizar_hora(self, horario_brt):
        """Atualiza as estatísticas ao mudar de hora."""
        nova_hora = horario_brt.replace(minute=0, second=0, microsecond=0)
        if nova_hora != self.hora_atual:
            self.salvar_historico_horas(
                self.hora_atual_stats['Hora'],
                self.hora_atual_stats['Vitórias'],
                self.derrotas_na_hora,
                self.hora_atual_stats['Maior Seq. de Perdas']
            )
            self.historico_horas.append(self.hora_atual_stats.copy())
            self.hora_atual = nova_hora
            self.hora_atual_stats = {
                'Hora': self.hora_atual.strftime('%Y-%m-%d %H:00'),
                'Vitórias': 0,
                'Maior Seq. de Perdas': 0
            }
            self.perdas_consecutivas = 0
            self.derrotas_na_hora = 0
            if self.pausado and self.acao_perdas_consecutivas == "Parar e Continuar na Próxima Hora":
                self.pausado = False
                print("Nova hora iniciada. Retomando apostas.")

    def executar(self):
        """Executa o bot em tempo real."""
        self.coletar_dados_iniciais()
        print("Iniciando monitoramento em tempo real...")
        
        while True:
            dados = self.fazer_requisicao(URL_BASE)
            if dados and len(dados) > 0:
                novos_registros = self.processar_registros(dados[0])
                if novos_registros:
                    self.inserir_registros(novos_registros)
                    registro = novos_registros[0]
                    horario_brt = datetime.datetime.strptime(registro['Data/Hora (BRT)'], '%d/%m/%Y %H:%M:%S')
                    
                    if not self.ultima_rodada_horario or horario_brt > self.ultima_rodada_horario:
                        self.ultima_rodada_horario = horario_brt
                        self.atualizar_hora(horario_brt)
                        novo_dado = registro.copy()
                        
                        cores = self.carregar_dados_banco(50)
                        if self.verificar_sequencia_vulneravel(cores):
                            if self.aguardando_sequencia_vulneravel:
                                self.aguardando_sequencia_vulneravel = False
                                self.pausado = False
                                print("Sequência vulnerável detectada! Retomando apostas.")

                        if self.ganhos_totais < self.limite_ganhos_totais and not self.pausado:
                            if len(self.dados_recentes) < 1:
                                status = None
                                entrada = None
                                dica, origem = None, None
                            elif len(self.dados_recentes) == 1:
                                status = "Iniciando"
                                entrada = self.valor_atual
                                dica, origem = self.gerar_dica()
                                if dica:
                                    print(f"Dica gerada: color={dica}, origem={origem}. Aguardando 5 segundos antes de apostar...")
                                    time.sleep(5)  # Aguarda 5 segundos
                                    self.fazer_aposta(entrada, dica)  # Faz a aposta real
                            else:
                                dica_anterior = self.dados_recentes[-1].get("Dica")
                                cor_atual = novo_dado['Cor']
                                if dica_anterior and cor_atual == dica_anterior:
                                    status = "Ganhou"
                                    self.vitorias_na_hora += 1
                                    self.hora_atual_stats['Vitórias'] += 1
                                    self.ganhos_totais += 1
                                    self.ganhos_consecutivos += 1
                                    self.perdas_consecutivas = 0
                                    self.valor_atual = self.valor_inicial
                                    self.registrar_vitoria(horario_brt)
                                else:
                                    status = "Perdeu" if dica_anterior else None
                                    if dica_anterior:
                                        self.derrotas_na_hora += 1
                                        self.perdas_totais += 1
                                        self.perdas_consecutivas += 1
                                        self.max_perdas_consecutivas = max(self.max_perdas_consecutivas, self.perdas_consecutivas)
                                        self.ganhos_consecutivos = 0
                                        self.valor_atual *= 2
                                        self.hora_atual_stats['Maior Seq. de Perdas'] = max(
                                            self.hora_atual_stats['Maior Seq. de Perdas'],
                                            self.perdas_consecutivas
                                        )
                                        if self.perdas_consecutivas >= self.limite_perdas_consecutivas:
                                            if self.acao_perdas_consecutivas == "Parar e Continuar na Próxima Hora":
                                                self.pausado = True
                                                print("Limite de perdas consecutivas atingido! Pausando até a próxima hora.")
                                            elif self.acao_perdas_consecutivas == "Apenas Avisar Sonoramente":
                                                print("Limite de perdas consecutivas atingido! Continuando...")
                                            elif self.acao_perdas_consecutivas == "Aguardar Sequência Vulnerável":
                                                self.pausado = True
                                                self.aguardando_sequencia_vulneravel = True
                                                print("Limite de perdas consecutivas atingido! Aguardando sequência vulnerável...")
                                            elif self.acao_perdas_consecutivas == "Aguardar N Rodadas":
                                                self.pausado = True
                                                self.rodadas_aguardadas = 0
                                                print(f"Limite de perdas consecutivas atingido! Aguardando {self.rodadas_aguardar} rodadas.")
                                entrada = self.valor_atual
                                dica, origem = self.gerar_dica()
                                if dica:
                                    print(f"Dica gerada: color={dica}, origem={origem}. Aguardando 5 segundos antes de apostar...")
                                    time.sleep(5)  # Aguarda 5 segundos
                                    self.fazer_aposta(entrada, dica)  # Faz a aposta real
                            
                            novo_dado.update({"Status": status, "Entrada": entrada, "Dica": dica, "Origem_Dica": origem})
                            self.salvar_aposta(registro, status, entrada, dica, origem)
                            self.dados_recentes.append(novo_dado)
                        
                        else:
                            if self.acao_perdas_consecutivas == "Aguardar N Rodadas" and self.pausado:
                                self.rodadas_aguardadas += 1
                                print(f"Rodada {self.rodadas_aguardadas}/{self.rodadas_aguardar} aguardada.")
                                if self.rodadas_aguardadas >= self.rodadas_aguardar:
                                    self.pausado = False
                                    self.rodadas_aguardadas = 0
                                    print("Período de espera concluído. Retomando apostas.")
                            else:
                                print("Meta de ganhos atingida ou bot pausado. Continuando a coletar dados.")
                        
            time.sleep(4)

if __name__ == "__main__":
    bot = BlazeCollectorAndBot()
    bot.executar()