# database.py
import sqlite3
import streamlit as st
import pandas as pd

def conectar_banco():
    with sqlite3.connect('financeiro.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cadastro_despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            descricao TEXT NOT NULL, 
            valor REAL NOT NULL, 
            data_inicial TEXT NOT NULL, 
            data_final TEXT NOT NULL,
            categoria TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cadastro_receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            descricao TEXT NOT NULL, 
            data_evento TEXT NOT NULL, 
            hora_evento TEXT NOT NULL, 
            valor REAL NOT NULL,
            categoria TEXT)''')
        conn.commit()
    return sqlite3.connect('financeiro.db')

def insert_data(table_name, data):
    try:
        with sqlite3.connect('financeiro.db') as conn:
            cursor = conn.cursor()
            if table_name == "cadastro_despesas":
                cursor.execute('''INSERT INTO cadastro_despesas (descricao, valor, data_inicial, data_final, categoria) 
                                  VALUES (?, ?, ?, ?, ?)''',
                               (data['descricao'], data['valor'], data['data_inicial'], 
                                data['data_final'], data.get('categoria', 'Outros')))
            elif table_name == "cadastro_receitas":
                cursor.execute('''INSERT INTO cadastro_receitas (descricao, data_evento, hora_evento, valor, categoria) 
                                  VALUES (?, ?, ?, ?, ?)''',
                               (data['descricao'], data['data_evento'], data['hora_evento'], 
                                data['valor'], data.get('categoria', 'Outros')))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False

def fetch_data(table_name, columns="*"):
    with sqlite3.connect('financeiro.db') as conn:
        df = pd.read_sql_query(f"SELECT {columns} FROM {table_name}", conn)
    return df.to_dict('records')

def update_data(table_name, record_id, data):
    try:
        with sqlite3.connect('financeiro.db') as conn:
            cursor = conn.cursor()
            if table_name == "cadastro_despesas":
                cursor.execute('''UPDATE cadastro_despesas 
                              SET descricao=?, valor=?, data_inicial=?, data_final=?, categoria=? 
                              WHERE id=?''',
                              (data['descricao'], data['valor'], 
                               data['data_inicial'], data['data_final'],
                               data.get('categoria', 'Outros'), record_id))
            else:
                cursor.execute('''UPDATE cadastro_receitas 
                              SET descricao=?, data_evento=?, hora_evento=?, valor=?, categoria=? 
                              WHERE id=?''',
                              (data['descricao'], data['data_evento'], 
                               data['hora_evento'], data['valor'],
                               data.get('categoria', 'Outros'), record_id))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_data(table_name, record_id):
    try:
        with sqlite3.connect('financeiro.db') as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {table_name} WHERE id=?', (record_id,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False