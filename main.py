# =====================================================================
# MOTOR DE CÁLCULO: MÉDIA DE 5 ANOS AUTOMATIZADA
# =====================================================================
@str_app.cache_data(ttl=3600)
def processar_radar_barsi():
    dados = []
    for ticker_sa in lista_acoes:
        nome = ticker_sa.replace(".SA", "")
        ticker_obj = yf.Ticker(ticker_sa)
        
        # Coleta de preço atual
        preco = float(ticker_obj.history(period="1d")['Close'].iloc[-1])
        
        # Coleta de dividendos históricos
        divs = ticker_obj.dividends
        div_estimado = 0.0
        fonte = "Sem histórico disponível"
        
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
        
        # Cálculo do Preço Teto (Método Barsi: 6% de retorno)
        preco_teto = div_estimado / 0.06
        margem = ((preco_teto / preco) - 1) * 100
        
        dados.append({
            "Ativo": nome, 
            "Preço": preco, 
            "Preço Teto": preco_teto,
            "Margem %": margem, 
            "Média 5 Anos (R$)": div_estimado, 
            "Fonte": fonte
        })
    return pd.DataFrame(dados)
