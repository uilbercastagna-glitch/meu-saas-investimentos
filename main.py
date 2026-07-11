import streamlit as str_app  # Interface web do SaaS
import yfinance as yf        # Coleta de dados da B3
import pandas as pd          # Manipulação de tabelas
from datetime import datetime, timedelta
import calendar

# =====================================================================
# DOCUMENTAÇÃO: CONFIGURAÇÕES DA PÁGINA DO SAAS
# =====================================================================
str_app.set_page_config(page_title="SaaS Análise de Carteira", page_icon="📊", layout="wide")

str_app.title("📊 Agente Profissional de Análise de Carteira")
str_app.subheader("Ações & FIIs — Mercado Brasileiro")
str_app.caption(f"Painel Atualizado em Tempo Real: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# =====================================================================
# DOCUMENTAÇÃO: DEFINIÇÃO DOS ATIVOS DA CARTEIRA
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]
lista_fiis = ["MXRF11.SA", "BTLG11.SA", "CPTS11.SA", "KNSC11.SA", "RBRR11.SA", "VILG11.SA", "DEVA11.SA", "BTAL11.SA", "BRCO11.SA", "VISC11.SA", "SNAG11.SA"]
todos_ativos = lista_acoes + lista_fiis

# =====================================================================
# DOCUMENTAÇÃO: FUNÇÃO AUXILIAR - CÁLCULO DO ÚLTIMO DIA ÚTIL DO MÊS
# =====================================================================
def obter_ultimo_dia_util_mes_atual():
    hoje = datetime.now()
    ano = hoje.year
    mes = hoje.month
    
    # Pega o último dia do mês corrente
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_final = datetime(ano, mes, ultimo_dia)
    
    # Retrocede se cair em fim de semana (Sábado=5, Domingo=6)
    if data_final.weekday() == 5:  # Sábado
        data_final -= timedelta(days=1)
    elif data_final.weekday() == 6:  # Domingo
        data_final -= timedelta(days=2)
        
    return data_final.strftime('%d/%m/%Y')

# =====================================================================
# DOCUMENTAÇÃO: MOTOR CORE DE PROCESSAMENTO E VALUATION
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_radar_completo():
    data_atual = datetime.now()
    data_30_dias = data_atual - timedelta(days=30)
    dados_radar = []
    
    # Mapeamento histórico de meses de anúncios das suas ações (Previsibilidade)
    meses_historicos_acoes = {
        "VALE3": "Agosto/2026", "BBAS3": "Agosto/2026", "BBSE3": "Agosto/2026",
        "BBDC4": "Mensal (Fim do Mês)", "TAEE11": "Agosto/2026", "ISAE4": "Fevereiro/Agosto",
        "CXSE3": "Novembro/2026", "PETR4": "Agosto/2026"
    }
    
    ultimo_dia_util = obter_ultimo_dia_util_mes_atual()
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        ticker_obj = yf.Ticker(ticker_sa)
        
        hist = ticker_obj.history(start=data_30_dias.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        if not hist.empty:
            preco_30_dias = hist['Close'].iloc[0]
            preco_atual = hist['Close'].iloc[-1]
            variacao_mes = ((preco_atual - preco_30_dias) / preco_30_dias) * 100
            
            # Cálculo do DY histórico acumulado de 12 meses
            dividendos = ticker_obj.dividends
            dy_calculado = 0.0
            
            if not dividendos.empty:
                dividendos.index = dividendos.index.tz_localize(None)
                limite_12m = datetime.now() - timedelta(days=365)
                ultimos_12m = dividendos[dividendos.index > limite_12m]
                total_proventos = ultimos_12m.sum()
                if preco_atual > 0:
                    dy_calculado = (total_proventos / preco_atual) * 100

            # REGRA DE NEGÓCIO DA PRÓXIMA DATA-COM:
            if tipo == "FII":
                # Como FIIs pagam mensalmente, a projeção é sempre o fechamento do mês atual
                proxima_datacom = ultimo_dia_util
            else:
                # Busca do nosso mapa de ações previsíveis
                proxima_datacom = meses_historicos_acoes.get(nome_limpo, "Consultar RI")

            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Variação 30D %": round(variacao_mes, 2),
                "DY 12M %": round(dy_calculado, 2),
                "Próxima Data-Com": proxima_datacom
            })
            
    df = pd.DataFrame(dados_radar)
    return df.sort_values(by="Variação 30D %", ascending=True)

df_radar_completo = processar_radar_completo()

# =====================================================================
# DOCUMENTAÇÃO: INTEGRAÇÃO VISUAL DAS ABAS
# =====================================================================
aba_radar, aba_ranking, aba_noticias = str_app.tabs([
    "🎯 Radar Dinâmico de Aportes", 
    "📈 Visão Geral de Preços", 
    "📰 Notícias e Fatos Relevantes"
])

# ---- ABA 1: RADAR DINÂMICO COM PRÓXIMA DATA-COM ----
with aba_radar:
    str_app.markdown("### 🎯 Ranking de Oportunidades (Roteiro de Aportes + Próximas Datas)")
    
    col_v1, col_v2, col_v3 = str_app.columns(3)
    total_linhas = len(df_radar_completo)
    terco = total_linhas // 3
    
    # 1. Zona de Aporte
    with col_v1:
        str_app.success("🟢 ZONA DE APORTE (Mais Descontados)")
        df_zona_aporte = df_radar_completo.iloc[0:terco]
        for _, linha in df_zona_aporte.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 📉 **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY 12M:** {linha['DY 12M %']:.2f}% | 📅 **Próxima Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown("---")
            
    # 2. Zona Neutra
    with col_v2:
        str_app.warning("🟡 ZONA NEUTRA (Preço Justo)")
        df_zona_neutra = df_radar_completo.iloc[terco:terco*2]
        for _, linha in df_zona_neutra.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 📊 **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY 12M:** {linha['DY 12M %']:.2f}% | 📅 **Próxima Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown("---")
            
    # 3. Zona Esticada
    with col_v3:
        str_app.error("🔴 ZONA ESTICADA (Aguardar Correção)")
        df_zona_esticada = df_radar_completo.iloc[terco*2:]
        for _, linha in df_zona_esticada.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | ⚠️ **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY 12M:** {linha['DY 12M %']:.2f}% | 📅 **Próxima Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown("---")

# ---- ABA 2: LISTAGEM EM TABELA COMPLETA ----
with aba_ranking:
    str_app.markdown("### 📋 Tabela Geral Comparativa (Ordenada por Desconto)")
    str_app.dataframe(df_radar_completo, use_container_width=True)

# ---- ABA 3: MERCADO E FATOS RELEVANTES ----
with aba_noticias:
    str_app.markdown("### 📰 Acompanhamento de Fatos Relevantes")
    str_app.info("Aba pronta para receber integrações futuras de notícias.")
