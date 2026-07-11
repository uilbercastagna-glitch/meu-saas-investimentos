import streamlit as str_app  # Biblioteca para criar a interface web do SaaS
import yfinance as yf        # Biblioteca para buscar os dados da Bolsa de Valores
import pandas as pd          # Biblioteca para organizar os dados em tabelas
from datetime import datetime, timedelta

# =====================================================================
# DOCUMENTAÇÃO: CONFIGURAÇÕES DA PÁGINA DO SAAS
# =====================================================================
str_app.set_page_config(page_title="SaaS Análise de Carteira", page_icon="📊", layout="wide")

str_app.title("📊 Agente Profissional de Análise de Carteira")
str_app.subheader("Ações & FIIs — Mercado Brasileiro")
str_app.caption(f"Dados atualizados em: {datetime.now().strftime('%d/%m/%Y')}")

# =====================================================================
# DOCUMENTAÇÃO: DEFINIÇÃO DOS ATIVOS DA CARTEIRA
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]
lista_fiis = ["MXRF11.SA", "BTLG11.SA", "CPTS11.SA", "KNSC11.SA", "RBRR11.SA", "VILG11.SA", "DEVA11.SA", "BTAL11.SA", "BRCO11.SA", "VISC11.SA", "SNAG11.SA"]
todos_ativos = lista_acoes + lista_fiis

# =====================================================================
# DOCUMENTAÇÃO: MOTOR DE CÁLCULO MULTI-PERÍODOS (DIA, MÊS e 5 ANOS)
# =====================================================================
@str_app.cache_data(ttl=3600)  # Mantém o cache por 1 hora para performance rápida
def processar_dados_multi_periodos():
    data_atual = datetime.now()
    data_30_dias = data_atual - timedelta(days=30)
    data_5_anos = data_atual - timedelta(days=5*365)
    
    dados_dia = []
    dados_mes = []
    dados_5anos = []
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        ticker_obj = yf.Ticker(ticker_sa)
        
        # 1. Coleta histórico de 30 dias (serve para o Dia e para o Mês)
        hist_curto = ticker_obj.history(start=data_30_dias.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        if len(hist_curto) >= 2:
            # Variação do Dia (Hoje vs Ontem)
            preco_atual = hist_curto['Close'].iloc[-1]
            preco_ontem = hist_curto['Close'].iloc[-2]
            var_dia = ((preco_atual - preco_ontem) / preco_ontem) * 100
            dados_dia.append({"Ativo": nome_limpo, "Variação %": var_dia, "Preço": preco_atual})
            
            # Variação do Mês (Atual vs 30 dias atrás)
            preco_30_dias = hist_curto['Close'].iloc[0]
            var_mes = ((preco_atual - preco_30_dias) / preco_30_dias) * 100
            dados_mes.append({"Ativo": nome_limpo, "Tipo": tipo, "Preço há 30 dias": round(preco_30_dias, 2), "Preço Atual": round(preco_atual, 2), "Variação %": round(var_mes, 2)})
        
        # 2. Coleta histórico de 5 anos
        hist_longo = ticker_obj.history(start=data_5_anos.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        if not hist_longo.empty:
            preco_inicial_5a = hist_longo['Close'].iloc[0]
            preco_atual_5a = hist_longo['Close'].iloc[-1]
            var_5a = ((preco_atual_5a - preco_inicial_5a) / preco_inicial_5a) * 100
            dados_5anos.append({"Ativo": nome_limpo, "Variação %": var_5a})
            
    return pd.DataFrame(dados_dia), pd.DataFrame(dados_mes), pd.DataFrame(dados_5anos)

# Executa o processamento dos dados
df_dia, df_mes, df_5anos = processar_dados_multi_periodos()

# Ordena as tabelas para descobrir as maiores altas e baixas
df_dia_ordenado = df_dia.sort_values(by="Variação %", ascending=False)
df_mes_ordenado = df_mes.sort_values(by="Variação %", ascending=False)
df_5anos_ordenado = df_5anos.sort_values(by="Variação %", ascending=False)

# =====================================================================
# DOCUMENTAÇÃO: CONSTRUÇÃO VISUAL DA INTERFACE (CONSTRUÇÃO DOS CARDS)
# =====================================================================
aba1, aba2, aba3, aba4 = str_app.tabs(["📈 Ranking e Destaques", "🔍 Análise de Quedas", "📰 Notícias", "🏆 Oportunidades"])

with aba1:
    # -----------------------------------------------------------------
    # SEÇÃO 1: CARDS DO DIA (HOJE)
    # -----------------------------------------------------------------
    str_app.markdown("### 🗓️ Destaques do Dia (Hoje vs Ontem)")
    col1, col2, col3, col4, col5, col6 = str_app.columns(6)
    
    # 3 Maiores Altas do Dia
    altas_dia = df_dia_ordenado.head(3).values
    if len(altas_dia) >= 3:
        col1.metric(label=f"🔺 1ª Alta Dia: {altas_dia[0][0]}", value=f"R$ {altas_dia[0][2]:.2f}", delta=f"{altas_dia[0][1]:.2f}%")
        col2.metric(label=f"🔺 2ª Alta Dia: {altas_dia[1][0]}", value=f"R$ {altas_dia[1][2]:.2f}", delta=f"{altas_dia[1][1]:.2f}%")
        col3.metric(label=f"🔺 3ª Alta Dia: {altas_dia[2][0]}", value=f"R$ {altas_dia[2][2]:.2f}", delta=f"{altas_dia[2][1]:.2f}%")
        
    # 3 Maiores Baixas do Dia
    baixas_dia = df_dia_ordenado.tail(3).iloc[::-1].values
    if len(baixas_dia) >= 3:
        col4.metric(label=f"🔻 1ª Baixa Dia: {baixas_dia[0][0]}", value=f"R$ {baixas_dia[0][2]:.2f}", delta=f"{baixas_dia[0][1]:.2f}%")
        col5.metric(label=f"🔻 2ª Baixa Dia: {baixas_dia[1][0]}", value=f"R$ {baixas_dia[1][2]:.2f}", delta=f"{baixas_dia[1][1]:.2f}%")
        col6.metric(label=f"🔻 3ª Baixa Dia: {baixas_dia[2][0]}", value=f"R$ {baixas_dia[2][2]:.2f}", delta=f"{baixas_dia[2][1]:.2f}%")

    str_app.divider()

    # -----------------------------------------------------------------
    # SEÇÃO 2: CARDS DO MÊS (30 DIAS)
    # -----------------------------------------------------------------
    str_app.markdown("### 📅 Destaques do Mês (Últimos 30 dias)")
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = str_app.columns(6)
    
    # 3 Maiores Altas do Mês
    altas_mes = df_mes_ordenado.head(3).values
    if len(altas_mes) >= 3:
        m_col1.metric(label=f"🟢 1ª Alta Mês: {altas_mes[0][0]}", value=f"R$ {altas_mes[0][3]:.2f}", delta=f"{altas_mes[0][4]:.2f}%")
        m_col2.metric(label=f"🟢 2ª Alta Mês: {altas_mes[1][0]}", value=f"R$ {altas_mes[1][3]:.2f}", delta=f"{altas_mes[1][4]:.2f}%")
        m_col3.metric(label=f"🟢 3ª Alta Mês: {altas_mes[2][0]}", value=f"R$ {altas_mes[2][3]:.2f}", delta=f"{altas_mes[2][4]:.2f}%")
        
    # 3 Maiores Baixas do Mês
    baixas_mes = df_mes_ordenado.tail(3).iloc[::-1].values
    if len(baixas_mes) >= 3:
        m_col4.metric(label=f"🔴 1ª Baixa Mês: {baixas_mes[0][0]}", value=f"R$ {baixas_mes[0][3]:.2f}", delta=f"{baixas_mes[0][4]:.2f}%")
        m_col5.metric(label=f"🔴 2ª Baixa Mês: {baixas_mes[1][0]}", value=f"R$ {baixas_mes[1][3]:.2f}", delta=f"{baixas_mes[1][4]:.2f}%")
        m_col6.metric(label=f"🔴 3ª Baixa Mês: {baixas_mes[2][0]}", value=f"R$ {baixas_mes[2][3]:.2f}", delta=f"{baixas_mes[2][4]:.2f}%")

    str_app.divider()

    # -----------------------------------------------------------------
    # SEÇÃO 3: CARDS HISTÓRICOS (5 ANOS)
    # -----------------------------------------------------------------
    str_app.markdown("### ⏳ Visão Histórica Macro (Últimos 5 Anos)")
    
    # Altas Históricas (Top 3)
    str_app.markdown("**Top 3 Maiores Valorizações (5 Anos):**")
    h_altas_cols = str_app.columns(3)
    altas_5a = df_5anos_ordenado.head(3).values
    for i, col in enumerate(h_altas_cols):
        if i < len(altas_5a):
            col.metric(label=f"🚀 {i+1}º Lugar: {altas_5a[i][0]}", value="Histórico 5A", delta=f"{altas_5a[i][1]:.2f}%")
            
    # Baixas Históricas (Top 5)
    str_app.markdown("**Top 5 Maiores Desvalorizações (5 Anos):**")
    h_baixas_cols = str_app.columns(5)
    baixas_5a = df_5anos_ordenado.tail(5).iloc[::-1].values
    for i, col in enumerate(h_baixas_cols):
        if i < len(baixas_5a):
            col.metric(label=f"💀 {i+1}º Lugar: {baixas_5a[i][0]}", value="Histórico 5A", delta=f"{baixas_5a[i][1]:.2f}%")

    str_app.divider()

    # -----------------------------------------------------------------
    # SEÇÃO 4: TABELA COMPLETA COM TODOS OS ATIVOS
    # -----------------------------------------------------------------
    str_app.markdown("### 📋 Visão Geral de Todos os Ativos da Carteira")
    str_app.dataframe(df_mes_ordenado, use_container_width=True)

# =====================================================================
# DOCUMENTAÇÃO: DEMAIS ABAS DE CONTEXTO (MANTIDAS DO PROJETO)
# =====================================================================
with aba2:
    str_app.markdown("### 🔍 Indicadores Fundamentais (3 Maiores Baixas)")
    str_app.warning("DEVA11 (FII) — Classificação: 🔴 Deterioração dos Fundamentos")
    str_app.table(pd.DataFrame([{"P/VP": 0.41, "DY 12M": "14.20%", "Vacância": "0.00%", "Tipo": "Papel", "Inadimplência": "8.50%"}]))
    str_app.info("VALE3 (Ação) — Classificação: 🟢 Oportunidade de Compra")
    str_app.table(pd.DataFrame([{"P/L": 6.10, "EV/EBITDA": 3.80, "DY 12M": "9.45%", "ROE": "18.50%", "Dívida/EBITDA": "0.65x"}]))

with aba3:
    str_app.markdown("### 📰 Eventos Materiais e Fatos Relevantes")
    str_app.dataframe(pd.DataFrame([{"Ativo": "PETR4", "Evento": "Anuncio de Dividendos Extraordinários", "Impacto": "Forte Positivo", "Horizonte": "Curto Prazo"}]), use_container_width=True)

with aba4:
    str_app.markdown("### 🎯 Ordenação Geral de Momento de Compra")
    str_app.dataframe(pd.DataFrame([{"Ranking": "1º", "Ativo": "VALE3", "Nota": 9.2, "Valuation": "Descontado", "Recomendação": "Aporte Forte"}]), use_container_width=True)
