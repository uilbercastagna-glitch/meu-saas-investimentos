# 1. IMPORTS SEMPRE NO TOPO DO ARQUIVO
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard Barsi", page_icon="📈", layout="wide")

# 3. DEFINIÇÃO DOS ATIVOS
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]

# 4. MOTOR DE CÁLCULO (Agora utilizando 'st' e 5 anos)
@st.cache_data(ttl=3600)
def processar_radar_barsi():
    dados = []
    for ticker_sa in lista_acoes:
        nome = ticker_sa.replace(".SA", "")
        ticker_obj = yf.Ticker(ticker_sa)
        
        # Coleta de preço atual
        hist = ticker_obj.history(period="1d")
        if hist.empty: continue
        preco = float(hist['Close'].iloc[-1])
        
        # Coleta de dividendos históricos
        divs = ticker_obj.dividends
        div_estimado = 0.0
        fonte = "Sem histórico"
        
        if not divs.empty:
            divs.index = divs.index.tz_localize(None)
            # Filtra últimos 5 anos
            limite_5y = datetime.now() - timedelta(days=5*365)
            divs_5y = divs[divs.index > limite_5y]
            
            # Agrupa por ano e tira a média anual dos últimos 5 anos
            media_5y = divs_5y.groupby(divs_5y.index.year).sum().mean()
            
            if media_5y > 0:
                div_estimado = float(media_5y)
                fonte = "Média Histórica (5 Anos)"
        
        # Cálculo Preço Teto
        preco_teto = div_estimado / 0.06
        margem = ((preco_teto / preco) - 1) * 100
        
        dados.append({
            "Ativo": nome, 
            "Preço": round(preco, 2), 
            "Preço Teto": round(preco_teto, 2),
            "Margem %": round(margem, 2), 
            "Div. Médio 5y (R$)": round(div_estimado, 2), 
            "Fonte": fonte
        })
    return pd.DataFrame(dados)

# 5. INTERFACE
st.title("📊 Agente de Análise Barsi (Automático)")
df_resultado = processar_radar_barsi()

aporte = st.number_input("Capital para aportar (R$)", value=4000.0, step=100.0)

if not df_resultado.empty:
    campea = df_resultado.sort_values("Margem %", ascending=False).iloc[0]
    
    st.subheader(f"🏆 Ação Recomendada: {campea['Ativo']}")
    qtd = int(aporte // campea['Preço'])
    renda = qtd * campea['Div. Médio 5y (R$)']

    c1, c2, c3 = st.columns(3)
    c1.metric("Quantidade a comprar", f"{qtd} ações")
    c2.metric("Renda Anual Projetada", f"R$ {renda:.2f}")
    c3.metric("Fonte", campea['Fonte'])

    st.table(df_resultado.sort_values("Margem %", ascending=False))
