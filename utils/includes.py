OFFERER_INCLUDES = [
    {
        "key": "managedVenues",
        "includes": [
            "nOffers",
            "iban",
            "bic"
        ]
    },
    "nOffers",
    "isValidated",
    "bic",
    "iban",
    "-validationToken"
]

NOT_VALIDATED_OFFERER_INCLUDES = [
    "name",
    "siren",
    "-address",
    "-city",
    "-dateCreated",
    "-dateModifiedAtLastProvider",
    "-firstThumbDominantColor",
    "-id",
    "-idAtProviders",
    "-isActive",
    "-lastProviderId",
    "-postalCode",
    "-thumbCount",
    "-validationToken"
]

EVENT_INCLUDES = [
    {
        "key": "occurrences",
        "includes": [
            {
                "key": "stock",
                "includes": [
                    {
                        "key": "offerer",
                        "includes": OFFERER_INCLUDES
                    }
                ]
            },
            'venue'
        ]
    },
    {
        "key": "mediations",
        "includes": ["thumbUrl"]
    },
    "offers",
    "-type",
    "offerType",
    "thumbUrl"
]

OFFER_INCLUDES = [
    'isFinished',
    'isFullyBooked',
    {
        "key": "activeMediation",
        "includes": ["thumbUrl"]
    },
    {
        "key": "mediations",
        "includes": ["thumbUrl"]
    },
    "stockAlertMessage",
    "isEditable",
    "isEvent",
    "isDigital",
    "isThing",
    "stockAlertMessage",
    {
        "key": "product",
        "includes": [
            'offerType',
            '-type'
        ]
    },
    {
        "key": "stocks",
        "includes": ['bookings']
    },
    {
        "key": "venue",
        "includes": [
            {
                "key": "managingOfferer",
                "includes": [
                    "nOffers",
                    "isValidated",
                    "bic",
                    "iban"
                ]
            },
            "isValidated",
            "bic",
            "iban"
        ]
    }
]

FAVORITE_INCLUDES = [
    "-userId",
    {
        "key": "mediation",
        "includes": ["thumbUrl"]
    },
    {
        "key": "offer",
        "includes": [
            "dateRange",
            "favorites",
            "isEvent",
            "isFinished",
            "isThing",
            "isFullyBooked",
            "offerType",
            {
                "key": "product",
                "includes": ["thumbUrl", "offerType"]
            },
            "stocks",
            "venue",
        ]
    },
    "thumbUrl"
]

RECOMMENDATION_INCLUDES = [
    "discoveryIdentifier",
    {
        "key": "mediation",
        "includes": ["thumbUrl"]
    },
    {
        "key": "offer",
        "includes": [
            "dateRange",
            'favorites',
            "isEvent",
            'isFinished',
            'isFullyBooked',
            "isThing",
            "offerType",
            {
                "key": "product",
                "includes": ["thumbUrl", "offerType"]
            },
            "stocks",
            {
                "key": "venue",
                "includes": ["managingOfferer"]
            },
        ]
    },
    "thumbUrl"
]

USER_INCLUDES = [
    '-culturalSurveyId',
    '-password',
    '-resetPasswordToken',
    '-resetPasswordTokenValidityLimit',
    '-validationToken',
    'expenses',
    'hasPhysicalVenues',
    'hasOffers',
    'wallet_balance',
    'wallet_is_activated'
]

WEBAPP_GET_BOOKING_INCLUDES = [
    "completedUrl",
    "isUserCancellable",
    {
        "key": "recommendation",
        "includes": [
            "discoveryIdentifier",
            {
                "key": "offer",
                "includes": [
                    "favorites",
                    "isFinished",
                    "isFullyBooked",
                    "offerType",
                    {
                        "key": "product",
                        "includes": ["thumbUrl"]
                    },
                    "stocks",
                    "venue",
                ]
            },
            {
                "key": "mediation",
                "includes": ["thumbUrl"]
            },
            "thumbUrl"
        ]
    },
    "stock",
    "thumbUrl"
]

WEBAPP_PATCH_POST_BOOKING_INCLUDES = [
    "completedUrl",
    "isUserCancellable",
    {
        "key": "recommendation",
        "includes": [
            "discoveryIdentifier",
            {
                "key": "offer",
                "includes": [
                    "dateRange",
                    "favorites",
                    "isEvent",
                    "isFinished",
                    "isFullyBooked",
                    "isThing",
                    "offerType",
                    {
                        "key": "product",
                        "includes": ["thumbUrl"]
                    },
                    "stocks",
                    "venue",
                ]
            },
            {
                "key": "mediation",
                "includes": ["thumbUrl"]
            },
            "thumbUrl"
        ]
    },
    "stock",
    "thumbUrl",
    {
        "key": "user",
        "includes": USER_INCLUDES
    }
]

PRO_BOOKING_INCLUDES = [
    {
        "key": "stock",
        "includes":
            [
                {
                    "key": "resolvedOffer",
                    "includes": [
                        'isFinished',
                        'isFullyBooked',
                        {
                            "key": "product",
                            "includes": ["offerType", "thumbUrl"]
                        },
                    ]
                }
            ]
    },
    {
        "key": 'user',
        "includes": [
            '-id',
            '-canBookFreeOffers',
            '-clearTextPassword',
            '-culturalSurveyId',
            '-dateCreated',
            '-dateOfBirth',
            '-departementCode',
            '-isAdmin',
            '-needsToFillCulturalSurvey',
            '-offerers',
            '-password',
            '-phoneNumber',
            '-postalCode',
            '-publicName',
            '-resetPasswordToken',
            '-resetPasswordTokenValidityLimit',
            '-validationToken'
        ]
    }
]

VENUE_INCLUDES = [
    'isValidated',
    'bic',
    'iban',
    "-validationToken",
    {
        "key": "managingOfferer"
    },
    {
        "key": 'venueProviders',
        "includes": ["provider"]
    },
]

VENUE_PROVIDER_INCLUDES = [
    "provider",
    "nOffers"
]

OFFERER_FOR_PENDING_VALIDATION_INCLUDES = [
    "validationToken",
    "-firstThumbDominantColor",
    "-thumbCount",
    "-idAtProviders",
    {
        "key": "UserOfferers",
        "includes": [{
            "key": "user",
            "includes": [
                '-resetPasswordTokenValidityLimit',
                '-resetPasswordToken',
                '-clearTextPassword',
                '-password',
                '-dateOfBirth',
                '-id',
            ]
        }]
    },
    {
        "key": "managedVenues",
        "includes": [
            '-publicName',
            '-thumbCount',
            '-idAtProviders',
            '-isVirtual',
            '-lastProviderId',
            '-latitude',
            '-longitude',
            '-dateModifiedAtLastProvider',
            '-firstThumbDominantColor'
        ]
    }
]

MEDIATION_INCLUDES = [
    "thumbUrl"
]

FEATURE_INCLUDES = [
    'nameKey'
]
