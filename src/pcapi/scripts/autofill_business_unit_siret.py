from pcapi.connectors.api_entreprises import get_by_offerer
from pcapi.core.finance.models import BusinessUnit
from pcapi.core.offerers.models import Offerer
from pcapi.core.offerers.models import Venue
from pcapi.models.bank_information import BankInformation
from pcapi.models.bank_information import BankInformationStatus
from pcapi.repository import repository
from pcapi.utils import requests


CASE_SINGLE_SIRET = "CASE_SINGLE_SIRET"
CASE_FROM_SIREN_API_FIND_MAIN_SIRET = "CASE_FROM_SIREN_API_FIND_MAIN_SIRET"
CASE_FROM_SIREN_API_ASSOCIATE_MAIN_SIRET = "CASE_FROM_SIREN_API_ASSOCIATE_MAIN_SIRET"
CASE_FROM_SIREN_API_CREATE_VENUE_FOR_SIRET = "CASE_FROM_SIREN_API_CREATE_VENUE_FOR_SIRET"
CASE_EMPTY_OFFERER_BU = "CASE_EMPTY_OFFERER_BU"
NO_SIRET_FOUND = "NO_SIRET_FOUND"
CREATION_CASES_LIST = {
    "CASE_SINGLE_SIRET": CASE_SINGLE_SIRET,
    "CASE_FROM_SIREN_API_FIND_MAIN_SIRET": CASE_FROM_SIREN_API_FIND_MAIN_SIRET,
    "CASE_FROM_SIREN_API_ASSOCIATE_MAIN_SIRET": CASE_FROM_SIREN_API_ASSOCIATE_MAIN_SIRET,
    "CASE_FROM_SIREN_API_CREATE_VENUE_FOR_SIRET": CASE_FROM_SIREN_API_CREATE_VENUE_FOR_SIRET,
    "CASE_EMPTY_OFFERER_BU": CASE_EMPTY_OFFERER_BU,
    "NO_SIRET_FOUND": NO_SIRET_FOUND,
}


def get_bank_information_hash(source):
    if isinstance(source, BankInformation):
        source = source.__dict__
    return f"{source['iban']}:{source['bic']}"


def build_business_unit_details(bank_information, offerer, venue=None):
    business_unit_details = dict(
        business_unit_id=None,
        offerer_id=offerer.id,
        bank_information_id=bank_information.id,
        bic=bank_information.bic,
        iban=bank_information.iban,
        siret=[],
        venues=[],
    )
    if venue:
        business_unit_details["venues"].append(venue)
        if venue.siret:
            business_unit_details["siret"].append(venue.siret)
    return business_unit_details


def have_bank_information(source):
    return source.bankInformation and source.bankInformation.status == BankInformationStatus.ACCEPTED


def get_business_unit_details_for_offerer(offerer):
    business_unit_details = {}
    offerer_bank_information_hash = None
    if have_bank_information(offerer):
        offerer_bank_information_hash = get_bank_information_hash(offerer.bankInformation)
        business_unit_details[offerer_bank_information_hash] = build_business_unit_details(
            offerer.bankInformation, offerer
        )

    offerer_venues = [venue for venue in offerer.managedVenues if not venue.businessUnitId]

    for venue in offerer_venues:
        if have_bank_information(venue):
            bank_information_hash = get_bank_information_hash(venue.bankInformation)
            if bank_information_hash in business_unit_details:
                details = business_unit_details[bank_information_hash]
                details["venues"].append(venue)
            else:
                details = build_business_unit_details(venue.bankInformation, offerer, venue)
        elif offerer_bank_information_hash in business_unit_details:
            details = business_unit_details[offerer_bank_information_hash]
            details["venues"].append(venue)
        else:
            details = None

        if details:
            if venue.siret:
                details["siret"].append(venue.siret)
                details["siret"] = list(set(details["siret"]))
            business_unit_details[get_bank_information_hash(details)] = details
    return business_unit_details


def get_main_venue_siren_api_data(offerer):
    print("get_main_venue_siren_api_data offerer", offerer)
    siren_api_data_for_offerer = get_by_offerer(offerer)
    siren_api_main_venue_data = siren_api_data_for_offerer["unite_legale"]["etablissement_siege"]

    return {
        "name": siren_api_main_venue_data["enseigne_1"],
        "address": siren_api_main_venue_data["geo_l4"],
        "postalCode": siren_api_main_venue_data["code_postal"],
        "city": siren_api_main_venue_data["libelle_commune"],
        "latitude": siren_api_main_venue_data["latitude"],
        "longitude": siren_api_main_venue_data["longitude"],
        "siret": siren_api_main_venue_data["siret"],
    }


def get_offerer_main_venue_from_siren_api_data(offerer, siren_api_data):

    main_venue = Venue.query.filter(
        Venue.managingOffererId == offerer.id,
        Venue.siret == siren_api_data["siret"],
    ).one_or_none()

    # try to find venue from address
    if not main_venue:
        main_venue = Venue.query.filter(
            Venue.managingOffererId == offerer.id,
            Venue.postalCode == siren_api_data["postalCode"],
            Venue.city == siren_api_data["city"],
        ).one_or_none()

    return main_venue


def create_business_unit(bank_information_id, siret, venues):
    business_unit = BusinessUnit(
        siret=siret,
        bankAccountId=bank_information_id,
    )
    repository.save(business_unit)
    for venue in venues:
        venue.businessUnitId = business_unit.id
    repository.save(*venues)

    return business_unit


def create_venue_from_siren_api_data(offerer_id, siren_api_data):
    return Venue(
        managingOffererId=offerer_id,
        name=siren_api_data.name,
        publicName=siren_api_data.name,
        address=siren_api_data.address,
        postalCode=siren_api_data.postalCode,
        city=siren_api_data.city,
        latitude=siren_api_data.latitude,
        longitude=siren_api_data.longitude,
        siret=siren_api_data["siret"],
        audioDisabilityCompliant=False,
        mentalDisabilityCompliant=False,
        motorDisabilityCompliant=False,
        visualDisabilityCompliant=False,
        isPermanent=True,
    )


def create_business_unit_and_main_venue(offerer_id, siren_api_data, bank_information_id, venues):
    created_venue = create_venue_from_siren_api_data(offerer_id, siren_api_data)
    venues.append(created_venue)
    return create_business_unit(bank_information_id, siren_api_data["siret"], venues)


def autofill_business_unit_siret():
    active_offerers = Offerer.query.filter(Offerer.isActive.is_(True))
    offerers_business_units = {}
    unprocessed_business_unit = {}
    for offerer in active_offerers:
        offerer_business_units_details = get_business_unit_details_for_offerer(offerer)

        for bu_details in offerer_business_units_details.values():
            bu_nb_siret = len(bu_details["siret"])
            bu_nb_venues = len(bu_details["venues"])

            # no venues are using these bank_informations,
            # we've nothing to do.
            if bu_nb_venues == 0:
                offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                    **bu_details,
                    "creation_case": CREATION_CASES_LIST["CASE_EMPTY_OFFERER_BU"],
                }
                continue

            # one or more venue and only one SIRET for the same bank_informations
            # we've everything we need to create the business unit
            elif bu_nb_siret == 1:
                business_unit = create_business_unit(
                    bu_details["bank_information_id"],
                    bu_details["siret"][0],
                    bu_details["venues"],
                )
                offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                    **bu_details,
                    "business_unit_id": business_unit.id,
                    "creation_case": CREATION_CASES_LIST["CASE_SINGLE_SIRET"],
                }

            # one or more venue and multiple SIRET for the same bank_informations
            # or
            # one or more venue with the same bank_information but without any SIRET
            # we need to choose what SIRET to use or to create the main venue for this offerer
            else:
                siren_api_data = get_main_venue_siren_api_data(offerer)

                # we found the main siret on our business unit details
                # we've everything we need to create the business unit
                if siren_api_data["siret"] in bu_details["siret"]:
                    business_unit = create_business_unit(
                        bu_details[
                            "bank_information_id"
                        ],  # TODO i need to get the right bank_information if any, the one who's liked to the main venue
                        siren_api_data["siret"],
                        bu_details["venues"],
                    )
                    offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                        **bu_details,
                        "business_unit_id": business_unit.id,
                        "creation_case": CREATION_CASES_LIST["CASE_FROM_SIREN_API_FIND_MAIN_SIRET"],
                    }

                else:
                    main_venue = get_offerer_main_venue_from_siren_api_data(offerer, siren_api_data)
                    business_unit_venue_ids = [venue.id for venue in bu_details["venues"]]

                    if main_venue:

                        # we found a venue matching api data but it's not in the current business unit
                        # otherwise it would have been processed before.
                        if main_venue.siret:
                            unprocessed_business_unit[get_bank_information_hash(bu_details)] = bu_details
                            offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                                **bu_details,
                                "business_unit_id": business_unit.id,
                                "creation_case": CREATION_CASES_LIST["NO_SIRET_FOUND"],
                            }

                        # main venue found on other criteria than siret
                        # set venue.siret then
                        # we've everything we need to create the business unit
                        elif main_venue.id in business_unit_venue_ids:
                            main_venue.siret = siren_api_data["siret"]
                            business_unit = create_business_unit(
                                bu_details["bank_information_id"],
                                siren_api_data["siret"],
                                bu_details["venues"],
                            )
                            offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                                **bu_details,
                                "business_unit_id": business_unit.id,
                                "creation_case": CREATION_CASES_LIST["CASE_FROM_SIREN_API_ASSOCIATE_MAIN_SIRET"],
                            }

                        # the main venue exist but it's not part of this business unit
                        else:
                            unprocessed_business_unit[get_bank_information_hash(bu_details)] = bu_details
                            offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                                **bu_details,
                                "business_unit_id": business_unit.id,
                                "creation_case": CREATION_CASES_LIST["NO_SIRET_FOUND"],
                            }

                    # we're unable to match siren api data with any venue in our database
                    else:
                        # create the venue as buisiness unit referer
                        business_unit = create_business_unit_and_main_venue(
                            offerer.id, siren_api_data, bu_details["bank_information_id"], bu_details["venues"]
                        )
                        offerer_business_units_details[get_bank_information_hash(bu_details)] = {
                            **bu_details,
                            "business_unit_id": business_unit.id,
                            "creation_case": CREATION_CASES_LIST["CASE_FROM_SIREN_API_CREATE_VENUE_FOR_SIRET"],
                        }
        offerers_business_units.update(offerer_business_units_details)

    return offerers_business_units
