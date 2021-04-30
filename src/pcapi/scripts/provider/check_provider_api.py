from datetime import datetime
import time

from flask import current_app as app

from pcapi.infrastructure.repository.stock_provider.provider_api import ProviderAPI
from pcapi.local_providers.provider_api import synchronize_provider_api


@app.manager.option("-u", "--url", help="Endpoint url")
@app.manager.option("-s", "--siret", help="A working siret")
@app.manager.option("-t", "--token", help="(Optionnal) Basic authentication token")
def check_provider_api(url, siret, token):
    provider_api = ProviderAPI(
        api_url=url,
        name="TestApi",
        authentication_token=token,
    )

    assert provider_api.is_siret_registered(siret), "L'appel avec uniquement le siret dans l'url doit fonctionner"

    stocks = provider_api.stocks(siret, limit=1)
    # assert stocks.get("total") != None, "Le total est manquant."
    # assert int(stocks.get("total")) > 0, "Le total n'est pas strictement supérieur à 0."

    assert "stocks" in stocks, 'La clé "stocks" est manquante.'
    assert len(stocks.get("stocks")) > 0, "Le nombre de stock est nul"
    stock = stocks["stocks"][0]
    assert isinstance(stock, dict), "Chaque stock devrait être un objet (dictionnaire)."
    assert "ref" in stock, 'Chaque stock devrait avoir une clé "ref".'
    assert "available" in stock, 'Chaque stock devrait avoir une clé "available".'

    two_stocks = provider_api.stocks(siret, limit=2)
    assert (
        len(stocks.get("stocks")) == 1 and len(two_stocks.get("stocks")) == 2
    ), "Le limit doit limiter le nombre de résultat"

    next_stock = provider_api.stocks(siret, limit=1, last_processed_reference=stocks.get("stocks")[0]["ref"])
    assert (
        next_stock.get("stocks")[0]["ref"] == two_stocks.get("stocks")[1]["ref"]
    ), "Le after doit correctement décaller les résultats"
    # assert int(stocks.get("total")) == int(next_stock.get("total")), "Le after ne doit pas impacter le total"

    no_stocks = provider_api.stocks(
        siret, limit=1, modified_since=datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
    )
    modified_since_is_implemented = len(stocks.get("stocks")) > len(no_stocks.get("stocks"))

    stock_count = 0
    batch_count = 0
    start_time = time.time()
    for raw_stocks in synchronize_provider_api._get_stocks_by_batch(
        siret, provider_api, None  # datetime.utcnow() - timedelta(days=1)
    ):
        stock_count += len(raw_stocks)
        batch_count += 1
        print(f"Iteration: {stock_count} stocks, {batch_count} batches")
    duration = time.time() - start_time
    average_duration = duration / batch_count

    print(
        f"""
C'est ok !

Le différentiel est implémenté : {modified_since_is_implemented}

Le format des stocks ressemble à {stock}

Récupérer {stock_count} offres en {batch_count} fois
a duré {duration} secondes.

Cela fait {average_duration}s par requête.
"""
    )
