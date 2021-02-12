import copy


BENEFICIARY_INCLUDES = [
    "-culturalSurveyId",
    "-culturalSurveyFilledDate",
    "-hasSeenTutorials",
    "-lastConnectionDate",
    "-password",
    "-resetPasswordToken",
    "-resetPasswordTokenValidityLimit",
    "-validationToken",
    "expenses",
    "wallet_balance",
    "wallet_is_activated",
    "wallet_date_created",
    "deposit_expiration_date",
    "needsToSeeTutorials",
]

OFFERER_INCLUDES = [
    {"key": "managedVenues", "includes": ["-validationToken", "nOffers", "iban", "bic"]},
    "nOffers",
    "isValidated",
    "userHasAccess",
    "bic",
    "iban",
    "demarchesSimplifieesApplicationId",
    "-validationToken",
]

OFFER_INCLUDES = [
    "isDigital",
    "isEditable",
    "isEvent",
    "hasBookingLimitDatetimesPassed",
    "isBookable",
    "isThing",
    "lastProvider",
    "offerType",
    "thumbUrl",
    {"key": "activeMediation", "includes": ["thumbUrl"]},
    {"key": "mediations", "includes": ["thumbUrl"]},
    {"key": "product", "includes": ["-type"]},
    {
        "key": "stocks",
        "includes": [
            "bookingsQuantity",
            "isBookable",
            "isEventDeletable",
            "isEventExpired",
            "remainingQuantity",
        ],
    },
    {
        "key": "venue",
        "includes": [
            {"key": "managingOfferer", "includes": ["-validationToken", "isValidated", "bic", "iban"]},
            "-validationToken",
            "isValidated",
            "bic",
            "iban",
        ],
    },
]


USER_INCLUDES = [
    "-culturalSurveyId",
    "-culturalSurveyFilledDate",
    "-hasSeenTutorials",
    "-isActive",
    "-password",
    "-resetPasswordToken",
    "-resetPasswordTokenValidityLimit",
    "-suspensionReason",
    "-validationToken",
    "hasPhysicalVenues",
    "hasOffers",
]

WEBAPP_GET_BOOKING_INCLUDES = [
    "completedUrl",
    "isEventExpired",
    {
        "key": "stock",
        "includes": [
            "isBookable",
            "isEventExpired",
            "remainingQuantity",
            {
                "key": "offer",
                "includes": [
                    "thumbUrl",
                    "hasBookingLimitDatetimesPassed",
                    "isBookable",
                    "isDigital",
                    "isEvent",
                    "offerType",
                    {"key": "stocks", "includes": ["isBookable", "isEventExpired", "remainingQuantity"]},
                    {"key": "venue", "includes": ["-validationToken"]},
                ],
            },
        ],
    },
    {"key": "mediation", "includes": ["thumbUrl"]},
]

WEBAPP_GET_BOOKING_WITH_QR_CODE_INCLUDES = copy.deepcopy(WEBAPP_GET_BOOKING_INCLUDES)
WEBAPP_GET_BOOKING_WITH_QR_CODE_INCLUDES.append("qrCode")

VENUE_INCLUDES = [
    "isValidated",
    "bic",
    "iban",
    "demarchesSimplifieesApplicationId",
    "-validationToken",
    {"key": "managingOfferer", "includes": ["-validationToken", "bic", "iban"]},
]

VENUE_PROVIDER_INCLUDES = ["provider", "nOffers", "-_sa_polymorphic_on"]

FEATURE_INCLUDES = ["nameKey"]

USER_OFFERER_INCLUDES = ["-validationToken"]
