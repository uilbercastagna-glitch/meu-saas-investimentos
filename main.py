import streamlit as str_app  # Interface web do SaaS
import yfinance as yf        # Coleta de dados da B3
import pandas as pd          # Manipulação de tabelas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Ajuste preciso de fuso horário brasileiro

# =====================================================================
# CONFIGURAÇÕES DA PÁGINA DO SAAS (FUSO HORÁRIO DE BRASÍLIA AJUSTADO)
# =====================================================================
str_app.set_page_config(page_title="SaaS Carteira Previdenciária", page_icon="📊", layout="wide")

# Captura o horário exato de Brasília independente do servidor do Streamlit estar lá fora
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

# Mapeamento de Dividendos Médios/Projetados por ação (Foco em recorrência)
dividendos_projetados_acoes = {
    "VALE3": 4.50, "BBAS3": 4.60, "BBSE3": 3.20, "BBDC4": 1.20,
    "TAEE11": 3.10, "ISAE4": 1.90, "CXSE3": 1.10, "PETR4": 4.00
}

# =====================================================================
# MOTOR CORE DE PROCESSAMENTO E VALUATION (MÉTODO BARSI + BOLA DE NEVE)
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
            
            # Coleta do preço mais recente de fechamento de forma segura
            hist = ticker_obj.history(period="5d")
            if hist.empty:
                continue
                
            preco_atual = hist['Close'].iloc[-1]
            
            # Cálculo de Proventos com base na categoria do ativo
            if tipo == "Ação":
                div_anual_estimado = dividendos_projetados_acoes.get(nome_limpo, 0.0)
                if div_anual_estimado == 0.0:
                    dividendos = ticker_obj.dividends
                    if not dividendos.empty:
                        dividendos.index = dividendos.index.tz_localize(None)
                        limite_12m = datetime.now() - timedelta(days=365)
                        div_anual_estimado = dividendos[dividendos.index > limite_12m].sum()
                
                # Preço Teto Barsi Clássico (Mínimo de 6% de rendimento)
                preco_teto = div_anual_estimado / 0.06
                proxima_datacom = meses_historicos_acoes.get(nome_limpo, "Consultar RI")
                
            else:
                # Regra customizada para FIIs (Piso de 8% ao ano para segurança)
                dividendos = ticker_obj.dividends
                if not dividendos.empty:
                    dividendos.index = dividendos.index.tz_localize(None)
                    limite_12m = datetime.now() - timedelta(days=365)
                    div_anual_estimado = dividendos[dividendos.index > limite_12m].sum()
                else:
                    div_anual_estimado = 0.0
                
                preco_teto = div_anual_estimado / 0.08
                proxima_datacom = "Mensal (Base do FII)"

            # Cálculos de Métricas Previdenciárias
            dy_projetado = (div_anual_estimado / preco_atual) * 100 if preco_atual > 0 else 0
            margem_seguranca = ((preco_teto / preco_atual) - 1) * 100 if preco_atual > 0 else 0
            
            # Custo para gerar R$ 100/mês (R$ 1.200/ano)
            acoes_para_meta = 1200 / div_anual_estimado if div_anual_estimado > 0 else 0
            custo_meta_100 = acoes_para_meta * preco_atual

            # GATILHO DA BOLA DE NEVE: Quantas ações para comprar 1 nova por ano sozinha
            if div_anual_estimado > 0:
                acoes_bola_neve = preco_atual / div_anual_estimado
                custo_bola_neve = acoes_bola_neve * preco_atual
            else:
                acoes_bola_neve = 0
                custo_bola_neve = 0

            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo
