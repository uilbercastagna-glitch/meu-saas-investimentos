import streamlit as str_app  
import yfinance as yf        
import pandas as pd          
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  

# =====================================================================
# CONFIGURAÇÕES DA PÁGINA DO SAAS
# =====================================================================
str_app.set_page_config(page_title="SaaS Carteira Previdenciária", page_icon="📊", layout="wide")

fuso_brasilia = ZoneInfo("America/Sao_Paulo")
horario_brasilia = datetime.now(fuso_brasilia)

str_app.title("📊 Agente de Análise Previdenciária — Método Barsi")
str_app.subheader("Foco em Acumulação de Ativos e Geração de Renda Passiva")
str_app.caption(f"Painel Atualizado (Horário de Brasília): {horario_brasilia.strftime('%d/%m/%Y %H:%M')}")

# =====================================================================
# DEFINIÇÃO DOS ATIVOS DA CARTEIRA
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]
lista_fiis = ["MXRF11.SA", "BTLG11.SA", "CPTS11.SA", "KNSC11.SA", "RBRR11.SA", "VILG11.SA", "DEVA11.SA", "BTAL11.SA", "BRCO11.SA", "VISC11.SA", "SNAG11.SA"]
todos_ativos = lista_acoes + lista_fiis

dividendos_projetados_acoes = {
    "VALE3": 4.50, "BBAS3": 4.60, "BBSE3": 3.20, "BBDC4": 1.20,
    "TAEE11": 3.10, "ISAE4": 1.90, "CXSE3": 1.10, "PETR4": 4.00
}

# =====================================================================
# MOTOR CORE DE PROCESSAMENTO E VALUATION
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_radar_barsi():
    dados_radar = []
    
    meses_historicos_acoes = {
        "VALE3": "Março/Agosto", "BBAS3": "Fev/Mai/Ago/Nov", "BBSE3": "Fevereiro/Agosto",
        "BBDC4": "Mensal (Fim do Mês)", "TAEE11": "Maio/Agosto/Novembro", "ISAE4": "Fevereiro/Agosto",
        "CXSE3": "Maio/Novembro", "PETR4": "Trimestral"
    }
    
    for ticker_sa in todos_ativos:
        try:
            nome_limpo = ticker_sa.replace(".SA", "")
            tipo = "Ação" if ticker_sa in lista_acoes else "FII"
            ticker_obj = yf.Ticker(ticker_sa)
            
            hist = ticker_obj.history(period="5d")
            if hist.empty:
                continue
                
            preco_atual = float(hist['Close'].iloc[-1])
            
            if tipo == "Ação":
                div_anual_estimado = float(dividendos_projetados_acoes.get(nome_limpo, 0.0))
                if div_anual_estimado == 0.0:
                    dividendos = ticker_obj.dividends
                    if not dividendos.empty:
                        dividendos.index = dividendos.index.tz_localize(None)
                        limite_12m = datetime.now() - timedelta(days=365)
                        div_anual_estimado = float(dividendos[dividendos.index > limite_12m].sum())
                
                preco_teto = div_anual_estimado / 0.06
                proxima_datacom = meses_historicos_acoes.get(nome_limpo, "Consultar RI")
                
            else:
                dividendos = ticker_obj.dividends
                if not dividendos.empty:
                    dividendos.index = dividendos.index.tz_localize(None)
                    limite_12m = datetime.now() - timedelta(days=365)
                    div_anual_estimado = float(dividendos[dividendos.index > limite_12m].sum())
                else:
                    div_anual_estimado = 0.0
                
                preco_teto = div_anual_estimado / 0.08
                proxima_datacom = "Mensal (Base do FII)"

            dy_projetado = (div_anual_estimado / preco_atual) * 100 if preco_atual > 0 else 0
            margem_seguranca = ((preco_teto / preco_atual) - 1) * 100 if preco_atual > 0 else 0
            
            acoes_para_meta = 1200 / div_anual_estimado if div_anual_estimado > 0 else 0
            custo_meta_100 = acoes_para_meta * preco_atual

            if div_anual_estimado > 0:
                acoes_bola_neve = preco_atual / div_anual_estimado
                custo_bola_neve = acoes_bola_neve * preco_atual
            else:
                acoes_bola_neve = 0
                custo_bola_neve = 0

            # Dicionário devidamente formatado e fechado
            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Preço Teto": round(preco_teto, 2),
                "Margem de Segurança %": round(margem_seguranca, 2),
                "DY Projetado %": round(dy_projetado, 2),
                "Próxima Data-Com": proxima_datacom,
                "Custo para R$ 100/mês": round(custo_meta_100, 2),
                "Ações p/ Bola de Neve": int(acoes_bola_neve),
                "Custo Autossuficiência": round(custo_bola_neve, 2)
            })
        except Exception:
            continue
            
    df = pd.DataFrame(dados_radar)
    if not df.empty:
        return df.sort_values(by="Margem de Segurança %", ascending=False)
    return df

df_radar_barsi = processar_radar_barsi()

# =====================================================================
# INTEGRAÇÃO VISUAL DAS ABAS
# =====================================================================
# Chamada completa da função ".tabs([])" restaurada
aba_radar, aba_ranking, aba_noticias = str_app.tabs([
    "🎯 Radar de Preço Teto Barsi", 
    "📈 Tabela Geral de Valuation", 
    "📰 Filosofia de Investimentos"
])

# ---- ABA 1: RADAR SEPARADO POR MARGEM DE SEGURANÇA ----
with aba_radar:
    str_app.markdown("### 🎯 Roteiro de Aportes Mensais baseado na Margem de Segurança")
    
    if df_radar_barsi.empty:
        str_app.error("Aguardando resposta do servidor do Yahoo Finance. Atualize a página em instantes.")
    else:
        col_v1, col_v2, col_v3 = str_app.columns(3)
        
        df_zona_aporte = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] > 10]
        df_zona_neutra = df_radar_barsi[(df_radar_barsi["Margem de Segurança %"] >= 0) & (df_radar_barsi["Margem de Segurança %"] <= 10)]
        df_zona_esticada = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] < 0]
        
        with col_v1:
            str_app.success(f"🟢 ZONA DE APORTE ({len(df_zona_aporte)})")
            for _, linha in df_zona_aporte.iterrows():
                str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
                str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 🎯 **Teto:** R$ {linha['Preço Teto']:.2f}")
                str_app.markdown(f"🛡️ **Margem:** `{linha['Margem de
