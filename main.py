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
str_app.caption(f"Painel Atualizado em Tempo Real: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# =====================================================================
# DOCUMENTAÇÃO: DEFINIÇÃO DOS ATIVOS DA CARTEIRA
# =====================================================================
lista_acoes = ["VALE3.SA", "BBAS3.SA", "BBSE3.SA", "BBDC4.SA", "TAEE11.SA", "ISAE4.SA", "CXSE3.SA", "PETR4.SA"]
lista_fiis = ["MXRF11.SA", "BTLG11.SA", "CPTS11.SA", "KNSC11.SA", "RBRR11.SA", "VILG11.SA", "DEVA11.SA", "BTAL11.SA", "BRCO11.SA", "VISC11.SA", "SNAG11.SA"]
todos_ativos = lista_acoes + lista_fiis

# =====================================================================
# DOCUMENTAÇÃO: MOTOR CORE DE PROCESSAMENTO E VALUATION
# =====================================================================
@str_app.cache_data(ttl=3600)  # Mantém os dados guardados por 1 hora
def processar_radar_completo():
    data_atual = datetime.now()
    data_30_dias = data_atual - timedelta(days=30)
    dados_radar = []
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        ticker_obj = yf.Ticker(ticker_sa)
        
        # Puxa o preço de hoje e de 30 dias atrás
        hist = ticker_obj.history(start=data_30_dias.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        if not hist.empty:
            preco_30_dias = hist['Close'].iloc[0]
            preco_atual = hist['Close'].iloc[-1]
            variacao_mes = ((preco_atual - preco_30_dias) / preco_30_dias) * 100
            
            # Puxa os dividendos dos últimos 12 meses direto do Yahoo Finance
            dividendos = ticker_obj.dividends
            dy_calculado = 0.0
            data_com_estimada = "Consultar RI"
            
            if not dividendos.empty:
                # Filtra os dividendos pagos nos últimos 365 dias
                ultimos_12m = dividendos[dividendos.index > (datetime.now() - timedelta(days=365))]
                total_proventos = ultimos_12m.sum()
                if preco_atual > 0:
                    dy_calculado = (total_proventos / preco_atual) * 100
                
                # Pega a última data com registrada no sistema para referência histórica
                data_com_estimada = dividendos.index[-1].strftime('%d/%m/%Y')

            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Variação 30D %": round(variacao_mes, 2),
                "DY 12M %": round(dy_calculado, 2),
                "Última Data-Com": data_com_estimada
            })
            
    df = pd.DataFrame(dados_radar)
    # Ordena: Maiores quedas primeiro (gerando o ranking de oportunidade/desconto)
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

# ---- ABA 1: RADAR DINÂMICO COMPLETAMENTE AUTOMATIZADO ----
with aba_radar:
    str_app.markdown("### 🎯 Ranking de Oportunidades (Baseado em Desconto 30D e Dividendos)")
    str_app.caption("Ativos no topo da lista são os que mais caíram no mês, abrindo potencial margem de segurança.")
    
    col_v1, col_v2, col_v3 = str_app.columns(3)
    
    # Divide a lista completa igualmente entre as 3 colunas visuais baseadas no ranking
    total_linhas = len(df_radar_completo)
    terco = total_linhas // 3
    
    # 1. Terço superior (Ativos que mais caíram = Oportunidade)
    with col_v1:
        str_app.success("🟢 ZONA DE APORTE (Mais Descontados)")
        df_zona_aporte = df_radar_completo.iloc[0:terco]
        for _, linha in df_zona_aporte.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 📉 **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY Líquido 12M:** {linha['DY 12M %']:.2f}% | 📅 **Última Data-Com:** {linha['Última Data-Com']}")
            str_app.markdown("---")
            
    # 2. Terço do meio (Ativos estáveis = Monitorar)
    with col_v2:
        str_app.warning("🟡 ZONA NEUTRA (Preço Justo)")
        df_zona_neutra = df_radar_completo.iloc[terco:terco*2]
        for _, linha in df_zona_neutra.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 📊 **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY Líquido 12M:** {linha['DY 12M %']:.2f}% | 📅 **Última Data-Com:** {linha['Última Data-Com']}")
            str_app.markdown("---")
            
    # 3. Terço inferior (Ativos que muito subiram = Aguardar correção)
    with col_v3:
        str_app.error("🔴 ZONA ESTICADA (Aguardar Correção)")
        df_zona_esticada = df_radar_completo.iloc[terco*2:]
        for _, linha in df_zona_esticada.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | ⚠️ **Variação 30D:** {linha['Variação 30D %']:+.2f}%")
            str_app.markdown(f"💸 **DY Líquido 12M:** {linha['DY 12M %']:.2f}% | 📅 **Última Data-Com:** {linha['Última Data-Com']}")
            str_app.markdown("---")

# ---- ABA 2: LISTAGEM EM TABELA COMPLETA ----
with aba_ranking:
    str_app.markdown("### 📋 Tabela Geral Comparativa (Ordenada do mais Descontado ao mais Esticado)")
    str_app.dataframe(df_radar_completo, use_container_width=True)

# ---- ABA 3: MERCADO E FATOS RELEVANTES ----
with aba_noticias:
    str_app.markdown("### 📰 Acompanhamento de Fatos Relevantes")
    str_app.info("Esta aba pode ser integrada a feeds de notícias automáticos nas próximas atualizações.")
