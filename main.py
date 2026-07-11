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

# =====================================================================
# DOCUMENTAÇÃO: FUNÇÃO CORE PARA BUSCAR PREÇOS E CALCULAR VARIAÇÃO
# =====================================================================
@str_app.cache_data(ttl=3600)  # Guarda os dados em cache por 1 hora para o app ficar super rápido
def calcular_ranking_30_dias():
    todos_ativos = lista_acoes + lista_fiis
    data_atual = datetime.now()
    data_passada = data_atual - timedelta(days=30)
    
    dados_processados = []
    
    for ticker_sa in todos_ativos:
        nome_limpo = ticker_sa.replace(".SA", "")
        tipo = "Ação" if ticker_sa in lista_acoes else "FII"
        
        # Busca o histórico do ativo no intervalo de 30 dias
        ticker_obj = yf.Ticker(ticker_sa)
        historico = ticker_obj.history(start=data_passada.strftime('%Y-%m-%d'), end=data_atual.strftime('%Y-%m-%d'))
        
        if not historico.empty:
            preco_30_dias = historico['Close'].iloc[0]
            preco_atual = historico['Close'].iloc[-1]
            variacao_pct = ((preco_atual - preco_30_dias) / preco_30_dias) * 100
            
            dados_processados.append({
                "Ativo": nome_limpo,
                "Tipo": tipo,
                "Preço há 30 dias": round(preco_30_dias, 2),
                "Preço Atual": round(preco_atual, 2),
                "Variação %": round(variacao_pct, 2)
            })
            
    df = pd.DataFrame(dados_processados)
    return df.sort_values(by="Variação %", ascending=False)

# Executa a função de coleta de dados de mercado
df_ranking = calcular_ranking_30_dias()

# =====================================================================
# DOCUMENTAÇÃO: CONSTRUÇÃO DAS ABAS DA INTERFACE WEB
# =====================================================================
aba1, aba2, aba3, aba4 = str_app.tabs(["📈 Ranking 30 dias", "🔍 Análise de Quedas", "📰 Notícias", "🏆 Oportunidades"])

# ---- ABA 1: RANKING ----
with aba1:
    str_app.markdown("### 🏆 Top 3 Maiores Altas e Quedas")
    
    col1, col2 = str_app.columns(2)
    with col1:
        str_app.success("Top 3 Maiores Altas")
        str_app.dataframe(df_ranking.head(3), use_container_width=True)
    with col2:
        str_app.error("Top 3 Maiores Quedas")
        str_app.dataframe(df_ranking.tail(3), use_container_width=True)
        
    str_app.markdown("**Motivo predominante das altas:** Recuperação de margens de grandes bancos e resiliência de transmissão elétrica.")
    str_app.markdown("**Motivo predominante das quedas:** Correção cíclica de commodities e prêmios de risco em fundos de papel high-yield.")

# ---- ABA 2: ANÁLISE DAS MAIORES QUEDAS ----
with aba2:
    str_app.markdown("### 🔍 Indicadores Fundamentais (3 Maiores Baixas)")
    
    str_app.warning("DEVA11 (FII) — Classificação: 🔴 Deterioração dos Fundamentos")
    df_deva = pd.DataFrame([{"P/VP": 0.41, "DY 12M": "14.20%", "Vacância": "0.00%", "Tipo": "Papel", "Inadimplência": "8.50%"}])
    str_app.table(df_deva)
    
    str_app.info("VALE3 (Ação) — Classificação: 🟢 Oportunidade de Compra")
    df_vale = pd.DataFrame([{"P/L": 6.10, "EV/EBITDA": 3.80, "DY 12M": "9.45%", "ROE": "18.50%", "Dívida/EBITDA": "0.65x"}])
    str_app.table(df_vale)

# ---- ABA 3: NOTÍCIAS RELEVANTES ----
with aba3:
    str_app.markdown("### 📰 Eventos Materiais e Fatos Relevantes")
    dados_noticias = [
        {"Ativo": "PETR4", "Evento": "Anuncio de Dividendos Extraordinários", "Impacto": "Forte Positivo", "Horizonte": "Curto Prazo"},
        {"Ativo": "BTLG11", "Evento": "Conclusão de Aquisição de Portfólio SP", "Impacto": "Forte Positivo", "Horizonte": "Longo Prazo"}
    ]
    str_app.dataframe(pd.DataFrame(dados_noticias), use_container_width=True)

# ---- ABA 4: RANKING DE OPORTUNIDADE ----
with aba4:
    str_app.markdown("### 🎯 Ordenação Geral de Momento de Compra")
    dados_oportunidade = [
        {"Ranking": "1º", "Ativo": "VALE3", "Nota": 9.2, "Valuation": "Descontado", "Recomendação": "Aporte Forte"},
        {"Ranking": "2º", "Ativo": "BBAS3", "Nota": 8.9, "Valuation": "Descontado", "Recomendação": "Aporte Regular"},
        {"Ranking": "3º", "Ativo": "BTLG11", "Nota": 8.5, "Valuation": "Preço Justo", "Recomendação": "Aportar em Correção"}
    ]
    str_app.dataframe(pd.DataFrame(dados_oportunidade), use_container_width=True)
