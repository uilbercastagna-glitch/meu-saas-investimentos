import streamlit as str_app  # Interface web do SaaS
import yfinance as yf        # Coleta de dados da B3
import pandas as pd          # Manipulação de tabelas
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURAÇÕES DA PÁGINA DO SAAS
# =====================================================================
str_app.set_page_config(page_title="SaaS Carteira Previdenciária", page_icon="📊", layout="wide")

str_app.title("📊 Agente de Análise Previdenciária — Método Barsi")
str_app.subheader("Foco em Acumulação de Ativos e Geração de Renda Passiva")
str_app.caption(f"Painel Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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
# MOTOR CORE DE PROCESSAMENTO E VALUATION (MÉTODO BARSI)
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

            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Preço Teto": round(preco_teto, 2),
                "Margem de Segurança %": round(margem_seguranca, 2),
                "DY Projetado %": round(dy_projetado, 2),
                "Próxima Data-Com": proxima_datacom,
                "Custo para R$ 100/mês": round(custo_meta_100, 2)
            })
        except Exception:
            # Proteção contra falhas em ativos individuais da API externa
            continue
            
    df = pd.DataFrame(dados_radar)
    if not df.empty:
        return df.sort_values(by="Margem de Segurança %", ascending=False)
    return df

df_radar_barsi = processar_radar_barsi()

# =====================================================================
# INTEGRAÇÃO VISUAL DAS ABAS
# =====================================================================
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
        
        # Filtros de margem baseados em regras reais de margem de segurança
        df_zona_aporte = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] > 10]
        df_zona_neutra = df_radar_barsi[(df_radar_barsi["Margem de Segurança %"] >= 0) & (df_radar_barsi["Margem de Segurança %"] <= 10)]
        df_zona_esticada = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] < 0]
        
        # 1. Zona de Aporte (Margem acima de 10%)
        with col_v1:
            str_app.success(f"🟢 ZONA DE APORTE ({len(df_zona_aporte)})")
            for _, linha in df_zona_aporte.iterrows():
                str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
                str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 🎯 **Teto:** R$ {linha['Preço Teto']:.2f}")
                str_app.markdown(f"🛡️ **Margem:** `{linha['Margem de Segurança %']}%`")
                str_app.markdown(f"💸 **DY:** {linha['DY Projetado %']:.2f}% | 📅 **Data-Com:** {linha['Próxima Data-Com']}")
                str_app.markdown(f"🧱 **Custo p/ R$ 100/mês:** R$ {linha['Custo para R$ 100/mês']:.2f}")
                str_app.markdown("---")
                
        # 2. Zona Neutra (Margem de 0% a 10%)
        with col_v2:
            str_app.warning(f"🟡 ZONA NEUTRA ({len(df_zona_neutra)})")
            for _, linha in df_zona_neutra.iterrows():
                str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
                str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 🎯 **Teto:** R$ {linha['Preço Teto']:.2f}")
                str_app.markdown(f"🛡️ **Margem:** `{linha['Margem de Segurança %']}%`")
                str_app.markdown(f"💸 **DY:** {linha['DY Projetado %']:.2f}% | 📅 **Data-Com:** {linha['Próxima Data-Com']}")
                str_app.markdown("---")
                
        # 3. Zona Esticada (Margem negativa - Acima do Preço Teto)
        with col_v3:
            str_app.error(f"🔴 ZONA ESTICADA ({len(df_zona_esticada)})")
            for _, linha in df_zona_esticada.iterrows():
                str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
                str_app.markdown(f"💰 **Preço:** R$ {linha['Preço Atual']:.2f} | 🎯 **Teto:** R$ {linha['Preço Teto']:.2f}")
                str_app.markdown(f"🚨 **Margem:** `{linha['Margem de Segurança %']}%`")
                str_app.markdown(f"💸 **DY:** {linha['DY Projetado %']:.2f}% | 📅 **Data-Com:** {linha['Próxima Data-Com']}")
                str_app.markdown("---")

# ---- ABA 2: LISTAGEM EM TABELA COMPLETA ----
with aba_ranking:
    str_app.markdown("### 📋 Painel Comparativo Geral")
    if not df_radar_barsi.empty:
        str_app.dataframe(df_radar_barsi, use_container_width=True)

# ---- ABA 3: FILOSOFIA DE INVESTIMENTOS ----
with aba_noticias:
    str_app.markdown("### 📜 Os Pilares do Método Barsi")
    str_app.info(
        "1. **Foco em quantidade de ações**, não no patrimônio flutuante.\n"
        "2. **Preço Teto Importa**: Garante comprar mais renda por real aplicado.\n"
        "3. **Setores BEST**: Bancos, Energia, Saneamento, Telecom e Seguros.\n"
        "4. **Reinvestimento**: Use dividendos para comprar mais ativos baratos."
    )
