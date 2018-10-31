from datetime import datetime, time, timedelta
from utils.date import today, strftime

EVENT_OR_THING_MOCK_NAMES = [
    "Anaconda",
    "Borneo",
    "D--",
    "Funky",
    "Sun",
    "Topaz"
]

EVENT_OCCURRENCE_BEGINNING_DATETIMES = [
    strftime(today),
    strftime(today + timedelta(days=2)),
    strftime(today + timedelta(days=15))
]

PLACES = [
    {
        "address": "148 ROUTE DE BONDY",
        "city": "Aulnay-sous-bois",
        "latitude": 48.9204903,
        "longitude": 2.4877456,
        "postalCode": "93600",
    }
]
