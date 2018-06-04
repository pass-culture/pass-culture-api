OCCASION_INCLUDES = [
    {
        "key": "occurences",
        "sub_joins": ['offer']
    },
    "mediations"
]

OFFERS_INCLUDES = [
    {
        "key": "eventOccurence",
        "sub_joins": [
            {
                "key": "event",
                "sub_joins": ['mediations']
            },
            "venue"
        ]
    },
    "occurencesAtVenue",
    "offerer",
    {
        "key": "thing",
        "sub_joins": [
            "mediations",
            "venue"
        ]
    },
    {
        "key": "recommendationOffers",
        "sub_joins": [
            {
                "key": "mediation"
            }
        ]
    },
    "venue"
]

RECOMMENDATIONS_INCLUDES = [
    {
        "key": "mediatedOccurences",
        "sub_joins": [
            {
                "key": "offer",
                "sub_joins": [
                    {
                        "key": "eventOccurence",
                        "sub_joins": ["event", "venue"],
                    },
                    "thing",
                    "venue"
                ]
            }
        ]
    },
    {
        "key": "mediation",
        "sub_joins": [
            "event",
            "thing"
        ]
    },
    "bookings",
    {
        "key": "recommendationBookings",
        "resolve": (lambda element, filters: element['booking']),
        "sub_joins": [
            {
                "key": "booking"
            }
        ]
    }
]

RECOMMENDATION_OFFER_INCLUDES =  [
    {
        "key": "eventOccurence",
        "sub_joins": ["event", "venue"]
    }
]

BOOKINGS_INCLUDES = [
    {
        "key": "recommendation",
        "sub_joins": RECOMMENDATIONS_INCLUDES
    },
    {
        "key": "offer",
        "sub_joins": OFFERS_INCLUDES
    }
]

OFFERERS_INCLUDES = [
    "venue"
]

USERS_INCLUDES = [
    {
        "key": 'offerers',
        "sub_joins": OFFERERS_INCLUDES
    },
    '-password'
]

includes = {
    'bookings': BOOKINGS_INCLUDES,
    'occasions': OCCASION_INCLUDES,
    'offerers': OFFERERS_INCLUDES,
    'offers': OFFERS_INCLUDES,
    'recommendations': RECOMMENDATIONS_INCLUDES,
    'users': USERS_INCLUDES
}
