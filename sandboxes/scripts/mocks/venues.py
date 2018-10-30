""" venue """
from sandboxes.scripts.mocks.offerers import NINETY_THREE_OFFERER_MOCK

VENUE_MOCKS = []

NINETY_THREE_VENUE_MOCK = {
    "address": "35 RUE DE PARIS",
    "bookingEmail": "fake@email.com",
    "comment": "Pas de siret car je suis un mock.",
    "city": "Bobigny",
    "departementCode": "93",
    "latitude": 48.89639,
    "longitude": 2.429692,
    "key": 'd33ee240-dc59-11e8-a29f-0242ac130000',
    "name": "NINETY THREE VENUE",
    "offererName": NINETY_THREE_OFFERER_MOCK['name'],
    "postalCode": "93000",
}

VIRTUAL_NINETY_THREE_VENUE_MOCK = {
    "isVirtual": True,
    "key": 'd33ee240-dc59-11e8-a29f-0242ac130001',
    "name": "Offre en ligne",
    "offererName": NINETY_THREE_OFFERER_MOCK['name']
}

VENUE_MOCKS += [
    NINETY_THREE_VENUE_MOCK,
    VIRTUAL_NINETY_THREE_VENUE_MOCK,
]

SCRATCH_MOCKS = [
    {
        "address": "1 BD POISSONNIERE",
        "bookingEmail": "fake@email.com",
        "city": "Paris",
        "departementCode": "75",
        "latitude": 48.870665,
        "longitude": 2.3478,
        "key": 'd33ee240-dc59-11e8-a29f-0242ac130002',
        "name": "LE GRAND REX PARIS",
        "offererName": "LE GRAND REX PARIS",
        "postalCode": "75002",
        "siret": "50763357600016"
    },
    {
        "isVirtual": True,
        "key": 'd33ee240-dc59-11e8-a29f-0242ac130003',
        "name": "Offre en ligne",
        "offererName": "LE GRAND REX PARIS"
    },
    {
        "address": "6 rue Grolee",
        "bookingEmail": "fake2@email.com",
        "city": "Lyon",
        "departementCode": "69",
        "latitude": 45.762606,
        "longitude": 4.836694,
        "key": 'd33ee240-dc59-11e8-a29f-0242ac130004',
        "name": "THEATRE DE L ODEON",
        "offererName": "THEATRE DE L ODEON",
        "postalCode": "69002",
        "siret": "75050570300025"
    },
    {
        "isVirtual": True,
        "key": 'd33ee240-dc59-11e8-a29f-0242ac130005',
        "name": "Offre en ligne",
        "offererName": "THEATRE DE L ODEON"
    },
    {
        "isVirtual": True,
        "key": 'd33ee240-dc59-11e8-a29f-0242ac130006',
        "name": "Offre en ligne",
        "offererName": "THEATRE DU SOLEIL"
    }
]

VENUE_MOCKS += SCRATCH_MOCKS
