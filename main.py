import streamlit as str_app
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# =====================================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================================
str_app.set_page_config(page_title="Dashboard Barsi Profissional", page_icon="📈", layout="wide")

# =====================================================================
# DEFINIÇÃO DOS ATIVOS
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]

# =====================================================================
# SIDEBAR: PAINEL DE CONTROLE DE PREMISSAS (Prioridade 1)
# =====================================================================
str_app.sidebar.header("⚙️ Matriz de Dividendos Manual")
str_app.sidebar.info("Estes valores definem a 'Prioridade 1' de cálculo.")

premissas_manuais = {}
valores_padrao = {
    "VALE3": 4.50, "BBAS3": 4.60, "BBSE3": 3.20, "BBDC4": 1.20,
    "TAEE11": 3.10, "ISAE4": 1.90, "CXSE3": 1.10, "PETR4": 4.00
}

for ticker in lista_acoes:
    nome = ticker.replace(".SA", "")
    premissas_manuais[nome] = str_app.sidebar.number_input(
        f"Projeção {nome} (R$/ação)", 
        value=valores_padrao.get(nome, 0.0), 
        step=0.05, format="%.2f"
    )

# =====================================================================
# MOTOR DE CÁLCULO
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_radar_barsi(premissas):
    dados = []
    for ticker_sa in lista_acoes:
        nome = ticker_sa.replace(".SA", "")
        ticker_obj = yf.Ticker(ticker_sa)
        preco = float(ticker_obj.history(period="1d")['Close'].iloc[-1])
        
        # Lógica de Hierarquia
        div_estimado = premissas[nome]
        fonte = "Matriz Manual (Usuário)"
        
        if div_estimado <= 0:
            divs = ticker_obj.dividends
            if not divs.empty:
                divs.index = divs.index.tz_localize(None)
                # Tenta Média 3 Anos
                limite_3y = datetime.now() - timedelta(days=3*365)
                media_3y = divs[divs.index > limite_3y].groupby(divs.index.year).sum().mean()
                if media_3y > 0:
                    div_estimado = float(media_3y)
                    fonte = "Média 3 Anos (Histórico)"
                else:
                    # TTM
                    div_estimado = float(divs[divs.index > (datetime.now() - timedelta(days=365))].sum())
                    fonte = "TTM 12 Meses (Yahoo)"
        
        preco_teto = div_estimado / 0.06
        margem = ((preco_teto / preco) - 1) * 100
        
        dados.append({
            "Ativo": nome, "Preço": preco, "Preço Teto": preco_teto,
            "Margem %": margem, "Div. Projetado": div_estimado, "Fonte": fonte
        })
    return pd.DataFrame(dados)

# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
str_app.title("📊 Agente de Análise Barsi")
df = processar_radar_barsi(premissas_manuais)

aporte = str_app.number_input("Capital para aportar (R$)", value=4000.0, step=100.0)
campea = df.sort_values("Margem %", ascending=False).iloc[0]

str_app.markdown(f"### 🏆 Ação Recomendada: {campea['Ativo']}")
qtd = int(aporte // campea['Preço'])
renda = qtd * campea['Div. Projetado']

col1, col2, col3 = str_app.columns(3)
col1.metric("Quantidade", f"{qtd} ações")
col2.metric("Renda Anual Projetada", f"R$ {renda:.2f}")
col3.metric("Fonte da Projeção", campea['Fonte'])

str_app.table(df.sort_values("Margem %", ascending=False))
