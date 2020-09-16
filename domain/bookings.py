from datetime import timedelta
from typing import Iterator

from models.stock_sql_entity import StockSQLEntity

BOOKING_CANCELLATION_DELAY = timedelta(hours=72)
CSV_HEADER = [
    "Raison sociale du lieu",
    "Nom de l'offre",
    "Nom utilisateur",
    "Prénom utilisateur",
    "E-mail utilisateur",
    "Date de la réservation",
    "Quantité",
    "Tarif pass Culture",
    "Statut",
]


def filter_bookings_to_compute_remaining_stock(stock: StockSQLEntity) -> Iterator:
    return filter(lambda b: not b.isCancelled
                            and not b.isUsed
                            or (b.isUsed
                                and b.dateUsed
                                and b.dateUsed >= stock.dateModified),
                  stock.bookings)


