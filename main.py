import streamlit as str_app  # Interface web do SaaS
import yfinance as yf        # Coleta de dados da B3
import pandas as pd          # Manipulação de tabelas
from datetime import datetime, timedelta

# =====================================================================
# DOCUMENTAÇÃO: CONFIGURAÇÕES DA PÁGINA DO SAAS
# =====================================================================
str_app.set_page_config(page_title="SaaS Análise de Carteira", page_icon="📊", layout="wide")

str_app.title("📊 Agente Profissional de Análise de Carteira")
str_app.subheader("Ações & FIIs — Mercado Brasileiro")
str_app.caption(f"Painel Consolidado em: {datetime.now().strftime('%d/%m/%Y')}")

# =====================================================================
# DOCUMENTAÇÃO: DEFINIÇÃO DOS ATIVOS DA CARTEIRA
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]
lista_fiis = ["MXRF11.SA", "BTLG11.SA", "CPTS11.SA", "KNSC11.SA", "RBRR11.SA", "VILG11.SA", "DEVA11.SA", "BTAL11.SA", "BRCO11.SA", "VISC11.SA", "SNAG11.SA"]
todos_ativos = lista_acoes + lista_fiis

# =====================================================================
# DOCUMENTAÇÃO: MOTOR DE CÁLCULO DINÂMICO DE MERCADO
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_dados_mercado():
    data_atual = datetime.now()
    data_30_dias = data_atual - timedelta(days=30)
    dados_mes = []
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        ticker_obj = yf.Ticker(ticker_sa)
        
        hist = ticker_obj.history(start=data_30_dias.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        if not hist.empty:
            preco_30_dias = hist['Close'].iloc[0]
            preco_atual = hist['Close'].iloc[-1]
            variacao_mes = ((preco_atual - preco_30_dias) / preco_30_dias) * 100
            
            dados_mes.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Variação 30D %": round(variacao_mes, 2)
            })
    return pd.DataFrame(dados_mes).sort_values(by="Variação 30D %", ascending=False)

df_mercado = processar_dados_mercado()

# =====================================================================
# DOCUMENTAÇÃO: CRIAÇÃO DAS ABAS DIRECIONADAS DO SAAS
# =====================================================================
aba_radar, aba_ranking, aba_quedas, aba_noticias = str_app.tabs([
    "🎯 Radar de Aportes & Data-Com", 
    "📈 Desempenho 30 Dias", 
    "🔍 Análise de Quedas Fundamentais", 
    "📰 Notícias Relevantes"
])

# -----------------------------------------------------------------
# ABA INTERATIVA: RADAR DE APORTES (CORRIGIDA PARA TEXTO COMPLETO)
# -----------------------------------------------------------------
with aba_radar:
    str_app.markdown("### 🎯 Onde Aportar Hoje? (Sinalização de Valor vs Data-Com)")
    
    # Base de dados analítica interna
    base_radar = {
        "VALE3": {"data_com": "Agosto/2026", "dy_esperado": "9.20%", "desconto": "18.4%", "situacao": "🟢 Excelente Momento"},
        "BBAS3": {"data_com": "21/08/2026", "dy_esperado": "10.10%", "desconto": "12.5%", "situacao": "🟢 Bom Momento"},
        "BTLG11": {"data_com": "31/07/2026", "dy_esperado": "9.15%", "desconto": "2.1%", "situacao": "🟡 Aguardar Correção"},
        "PETR4": {"data_com": "Agosto/2026", "dy_esperado": "12.80%", "desconto": "1.5%", "situacao": "🟡 Aguardar Correção"},
        "MXRF11": {"data_com": "31/07/2026", "dy_esperado": "10.40%", "desconto": "-3.0%", "situacao": "🔴 Evitar no Curto Prazo"},
        "DEVA11": {"data_com": "31/07/2026", "dy_esperado": "14.50%", "desconto": "58.0%", "situacao": "🔴 Evitar / Tese Quebrada"},
    }
    
    # Divisão em colunas visuais
    col_v1, col_v2, col_v3 = str_app.columns(3)
    
    with col_v1:
        str_app.success("🟢 TOP APORTES (Descontados)")
        for ativo, info in base_radar.items():
            if "🟢" in info["situacao"]:
                # Escreve o texto completo sem risco de corte na tela do celular
                str_app.markdown(f"### **{ativo}**")
                str_app.markdown(f"📅 **Data-Com:** {info['data_com']}")
                str_app.markdown(f"💰 **DY Esperado:** {info['dy_esperado']} | 📉 **Desconto:** {info['desconto']}")
                str_app.markdown("---")
                
    with col_v2:
        str_app.warning("🟡 MONITORAR (Preço Justo)")
        for ativo, info in base_radar.items():
            if "🟡" in info["situacao"]:
                str_app.markdown(f"### **{ativo}**")
                str_app.markdown(f"📅 **Data-Com:** {info['data_com']}")
                str_app.markdown(f"💰 **DY Esperado:** {info['dy_esperado']} | 📊 **Desconto:** {info['desconto']}")
                str_app.markdown("---")
                
    with col_v3:
        str_app.error("🔴 CAUTELA (Risco/Esticado)")
        for ativo, info in base_radar.items():
            if "🔴" in info["situacao"]:
                str_app.markdown(f"### **{ativo}**")
                str_app.markdown(f"📅 **Data-Com:** {info['data_com']}")
                str_app.markdown(f"💰 **DY Esperado:** {info['dy_esperado']} | ⚠️ **Prêmio:** {info['desconto']}")
                str_app.markdown("---")

# -----------------------------------------------------------------
# AS DEMAIS ABAS SEGUEM O PADRÃO CONSOLIDADO
# -----------------------------------------------------------------
with aba_ranking:
    str_app.markdown("### 📋 Variação de Preço de Todos os Ativos")
    str_app.dataframe(df_mercado, use_container_width=True)

with aba_quedas:
    str_app.markdown("### 🔍 Raio-X das Maiores Baixas Recentes")
    str_app.error("DEVA11 — 🔴 Deterioração dos Fundamentos")
    str_app.table(pd.DataFrame([{"P/VP": 0.41, "DY 12M": "14.20%", "Vacância": "0.00%", "Inadimplência": "8.50%"}]))
    str_app.success("VALE3 — 🟢 Oportunidade por Ciclo de Commodity")
    str_app.table(pd.DataFrame([{"P/L": 6.10, "EV/EBITDA": 3.80, "DY 12M": "9.45%"}]))

with aba_noticias:
    str_app.markdown("### 📰 Eventos Materiais")
    str_app.dataframe(pd.DataFrame([{"Ativo": "PETR4", "Evento": "Anúncio de Dividendos Extraordinários", "Impacto": "Forte Positivo"}]), use_container_width=True)
