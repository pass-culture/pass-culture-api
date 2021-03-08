from datetime import datetime
import time

from flask import current_app as app

from pcapi.infrastructure.repository.stock_provider.provider_api import ProviderAPI
from pcapi.local_providers.fnac import synchronize_fnac_stocks


@app.manager.option("-u", "--url", help="Endpoint url")
@app.manager.option("-s", "--siret", help="A working siren")
@app.manager.option("-t", "--token", help="(Optionnal) Basic authentication token")
def check_provider_api(url: str, siret: str, token: str) -> None:
    provider_api = ProviderAPI(
        api_url=url,
        name="TestApi",
        authentication_token=token,
    )

    assert provider_api.is_siret_registered(siret), "L'appel avec uniquement le siret dans l'url doit fonctionner"

    stocks = provider_api.stocks(siret, limit=1)
    assert stocks.get("total") != None, "Le total doit être envoyé"
    assert int(stocks.get("total")) > 0, "Le total doit être supérieur à 0 pour pouvoir tester"
    assert int(stocks.get("offset")) == 0, "L'offset doit être envoyé"

    stock = stocks.get("stocks")[0]
    assert stock != None, "Stocks should be under stocks key"
    assert "ref" in stock, "Stocks should have a ref"
    assert "available" in stock, "Stocks shouuld have an available"
    assert "price" in stock, "Stocks shouuld have a price"

    two_stocks = provider_api.stocks(siret, limit=2)
    assert (
        len(stocks.get("stocks")) == 1 and len(two_stocks.get("stocks")) == 2
    ), "Le limit doit limiter le nombre de résultat"

    next_stock = provider_api.stocks(siret, limit=1, last_processed_reference=stocks.get("stocks")[0]["ref"])
    assert (
        next_stock.get("stocks")[0]["ref"] == two_stocks.get("stocks")[1]["ref"]
    ), "Le after doit correctement décaller les résultats"
    assert int(stocks.get("total")) == int(next_stock.get("total")), "Le after ne doit pas changer le total"
    assert int(next_stock.get("offset")) == 1, "Le after doit correctement décaller le offset"

    no_stocks = provider_api.stocks(
        siret, limit=1, modified_since=datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ")
    )
    modified_since_is_implemented = int(stocks.get("total")) > int(no_stocks.get("total"))

    stock_count = 0
    batch_count = 0
    start_time = time.time()
    for raw_stocks in synchronize_fnac_stocks._get_stocks_by_batch(siret, provider_api, None):
        stock_count += len(raw_stocks)
        batch_count += 1
    duration = time.time() - start_time
    average_duration = duration / batch_count

    print(
        f"""
C'est ok !

Le différentiel est implémenté : {modified_since_is_implemented}

Le format des stocks ressemble à {stock}

Fetcher {stock_count} offres en {batch_count} fois
a duré {duration} secondes.

Cela fait {average_duration}s par requête.
"""
    )
