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

# Mapeamento de Dividendos Médios/Projetados por ação (Evita distorções de dividendos extraordinários)
# Valores estimados baseados em históricos recorrentes. Você pode ajustar estes valores conforme seu estudo!
dividendos_projetados_acoes = {
    "VALE3": 4.50,
    "BBAS3": 4.60,
    "BBSE3": 3.20,
    "BBDC4": 1.20,
    "TAEE11": 3.10,
    "ISAE4": 1.90,
    "CXSE3": 1.10,
    "PETR4": 4.00
}

# =====================================================================
# MOTOR CORE DE PROCESSAMENTO E VALUATION (MÉTODO BARSI)
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_radar_barsi():
    dados_radar = []
    
    # Previsibilidade de anúncios das Ações (Setores BEST)
    meses_historicos_acoes = {
        "VALE3": "Março/Agosto", "BBAS3": "Fevereiro/Maio/Agosto/Novembro", "BBSE3": "Fevereiro/Agosto",
        "BBDC4": "Mensal (Fim do Mês)", "TAEE11": "Maio/Agosto/Novembro", "ISAE4": "Fevereiro/Agosto",
        "CXSE3": "Maio/Novembro", "PETR4": "Trimestral"
    }
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        ticker_obj = yf.Ticker(ticker_sa)
        
        # Coleta do preço mais recente de fechamento
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            preco_atual = hist['Close'].iloc[-1]
            
            # Cálculo de Proventos com base na categoria do ativo
            if tipo == "Ação":
                # Busca o dividendo médio/projetado histórico para evitar a armadilha do DY passado
                div_anual_estimado = dividendos_projetados_acoes.get(nome_limpo, 0.0)
                if div_anual_estimado == 0.0: # Caso falte no dicionário, puxa o histórico de 12 meses
                    dividendos = ticker_obj.dividends
                    if not dividendos.empty:
                        dividendos.index = dividendos.index.tz_localize(None)
                        limite_12m = datetime.now() - timedelta(days=365)
                        div_anual_estimado = dividendos[dividendos.index > limite_12m].sum()
                
                # Regra do Preço Teto de Barsi (Garantir no mínimo 6% de Retorno)
                preco_teto = div_anual_estimado / 0.06
                proxima_datacom = meses_historicos_acoes.get(nome_limpo, "Consultar RI")
                
            else:
                # Regra para FIIs: Como o rendimento é mensal, calculamos com base na constância recente
                dividendos = ticker_obj.dividends
                if not dividendos.empty:
                    # Pega a soma dos últimos 12 meses para os FIIs
                    dividendos.index = dividendos.index.tz_localize(None)
                    limite_12m = datetime.now() - timedelta(days=365)
                    div_anual_estimado = dividendos[dividendos.index > limite_12m].sum()
                else:
                    div_anual_estimado = 0.0
                
                # Preço teto adaptado para FIIs (Exigência de mercado geralmente maior, ex: 8% ao ano)
                preco_teto = div_anual_estimado / 0.08
                proxima_datacom = "Mensal (Base de cada FII)"

            # Cálculos de Métricas Previdenciárias
            dy_projetado = (div_anual_estimado / preco_atual) * 100 if preco_atual > 0 else 0
            margem_seguranca = ((preco_teto / preco_atual) - 1) * 100 if preco_atual > 0 else 0
            
            # Indicador de Meta: Quantas ações/cotas são necessárias para gerar R$ 100 por mês (R$ 1.200/ano)?
            acoes_para_meta = 1200 / div_anual_estimado if div_anual_estimado > 0 else 0
            custo_meta_100 = acoes_para_meta * preco_atual

            dados_radar.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço Atual": round(preco_atual, 2),
                "Preço Teto": round(preco_teto, 2),
                "Margem de Segurança %": round(margem_seguranca, 2),
                "DY Projetado/Estimado %": round(dy_projetado, 2),
                "Próxima Data-Com": proxima_datacom,
                "Custo para R$ 100/mês": round(custo_meta_100, 2)
            })
            
    df = pd.DataFrame(dados_radar)
    # Regra de Ouro: Ordena sempre pela maior Margem de Segurança disponível
    return df.sort_values(by="Margem de Segurança %", ascending=False)

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
    
    col_v1, col_v2, col_v3 = str_app.columns(3)
    
    # Classificação por Regras Práticas do Value Investing
    df_zona_aporte = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] > 10]
    df_zona_neutra = df_radar_barsi[(df_radar_barsi["Margem de Segurança %"] >= 0) & (df_radar_barsi["Margem de Segurança %"] <= 10)]
    df_zona_esticada = df_radar_barsi[df_radar_barsi["Margem de Segurança %"] < 0]
    
    # 1. Zona de Aporte (Margem de segurança expressiva, acima de 10%)
    with col_v1:
        str_app.success(f"🟢 ZONA DE APORTE ({len(df_zona_aporte)} ativos)")
        str_app.caption("Ativos muito abaixo do Preço Teto. Hora de acumular quantidade de ações!")
        for _, linha in df_zona_aporte.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço Atual:** R$ {linha['Preço Atual']:.2f} | 🎯 **Preço Teto:** R$ {linha['Preço Teto']:.2f}")
            str_app.markdown(f"🛡️ **Margem de Segurança:** `{linha['Margem de Segurança %']}%`")
            str_app.markdown(f"💸 **DY Estimado:** {linha['DY Projetado/Estimado %']:.2f}% | 📅 **Meses Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown(f"🧱 **Custo para R$ 100/mês de renda:** R$ {linha['Custo para R$ 100/mês']:.2f}")
            str_app.markdown("---")
            
    # 2. Zona Neutra (Próximo ao preço justo, margem entre 0% e 10%)
    with col_v2:
        str_app.warning(f"🟡 ZONA NEUTRA ({len(df_zona_neutra)} ativos)")
        str_app.caption("Ativos precificados perto do teto. Comprar apenas se faltar opções na Zona Verde.")
        for _, linha in df_zona_neutra.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço Atual:** R$ {linha['Preço Atual']:.2f} | 🎯 **Preço Teto:** R$ {linha['Preço Teto']:.2f}")
            str_app.markdown(f"🛡️ **Margem de Segurança:** `{linha['Margem de Segurança %']}%`")
            str_app.markdown(f"💸 **DY Estimado:** {linha['DY Projetado/Estimado %']:.2f}% | 📅 **Meses Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown("---")
            
    # 3. Zona Esticada (Margem negativa, acima do preço teto)
    with col_v3:
        str_app.error(f"🔴 ZONA ESTICADA ({len(df_zona_esticada)} ativos)")
        str_app.caption("Ativos acima do preço teto. O dividendo esperado não garante os 6% mínimos. Aguardar correção.")
        for _, linha in df_zona_esticada.iterrows():
            str_app.markdown(f"### **{linha['Ativo']}** ({linha['Tipo']})")
            str_app.markdown(f"💰 **Preço Atual:** R$ {linha['Preço Atual']:.2f} | 🎯 **Preço Teto:** R$ {linha['Preço Teto']:.2f}")
            str_app.markdown(f"🚨 **Margem de Segurança:** `{linha['Margem de Segurança %']}%`")
            str_app.markdown(f"💸 **DY Estimado:** {linha['DY Projetado/Estimado %']:.2f}% | 📅 **Meses Data-Com:** {linha['Próxima Data-Com']}")
            str_app.markdown("---")

# ---- ABA 2: LISTAGEM EM TABELA COMPLETA ----
with aba_ranking:
    str_app.markdown("### 📋 Painel Comparativo Geral (Ordenado por Margem de Segurança)")
    str_app.dataframe(df_radar_barsi, use_container_width=True)

# ---- ABA 3: FILOSOFIA DE INVESTIMENTOS ----
with aba_noticias:
    str_app.markdown("### 📜 Os Pilares do Método Barsi de Geração de Renda")
    str_app.info(
        "1. **O foco é na quantidade de ações**, não no patrimônio líquido flutuante.\n"
        "2. **Não compre a qualquer preço**: O preço teto garante que seu dinheiro compre mais renda por real aplicado.\n"
        "3. **Priorize os setores BEST**: Bancos, Energia, Saneamento, Telecomunicações e Seguros.\n"
        "4. **Reinvista os dividendos**: Use a renda gerada pela própria carteira para comprar mais ações dos ativos que estiverem na Zona Verde."
    )
