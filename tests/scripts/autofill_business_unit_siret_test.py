from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from pcapi.core.finance.models import BusinessUnit
from pcapi.core.offerers.factories import OffererFactory
from pcapi.core.offerers.models import Offerer
from pcapi.core.offerers.models import Venue
from pcapi.core.offers.factories import BankInformationFactory
from pcapi.core.offers.factories import VenueFactory
from pcapi.core.testing import assert_num_queries
from pcapi.models.bank_information import BankInformation
from pcapi.scripts.autofill_business_unit_siret import CREATION_CASES_LIST
from pcapi.scripts.autofill_business_unit_siret import autofill_business_unit_siret


def get_api_response(
    siren, venue_data={"siret": None, "name": None, "address": None, "postalCode": None, "city": None}
):
    main_venue_api_data = {
        "code_postal": "46500",
        "enseigne_1": "DEFAULT_ENSEIGNE_1",
        "geo_adresse": "DEFAULT_GEO_ADDRESSE",
        "geo_l4": "DEFAULT_GEO_L4",
        "geo_l5": None,
        "code_postal": "DEFAULT_POSTAL_CODE",
        "latitude": "DEFAULT_LATITUDE",
        "libelle_commune": "DEFAULT_LIBELLE_COMMUNE",
        "longitude": "DEFAULT_LONGITUDE",
        "numero_voie": "DEFAULT_LATITUDE",
        "siren": siren,
        "siret": "DEFAULT_SIRET",
        "type_voie": "PL",
    }
    if "siret" in venue_data:
        main_venue_api_data["siret"] = venue_data["siret"]
    if "name" in venue_data:
        main_venue_api_data["enseigne_1"] = venue_data["name"]
    if "address" in venue_data:
        main_venue_api_data["geo_l4"] = venue_data["address"]
    if "postalCode" in venue_data:
        main_venue_api_data["code_postal"] = venue_data["postalCode"]
    if "city" in venue_data:
        main_venue_api_data["libelle_commune"] = venue_data["city"]

    return {
        "unite_legale": {
            "etablissement_siege": main_venue_api_data,
            "etablissements": [],
            "etat_administratif": "A",
            "id": 226257595,
            "identifiant_association": None,
            "nic_siege": "00068",
            "nom": None,
            "nom_usage": None,
            "nombre_periodes": "7",
            "nomenclature_activite_principale": "NAFRev2",
            "numero_tva_intra": "FR35214601288",
            "prenom_1": None,
            "prenom_2": None,
            "prenom_3": None,
            "prenom_4": None,
            "prenom_usuel": None,
            "pseudonyme": None,
            "sexe": None,
            "sigle": None,
            "siren": "214601288",
            "statut_diffusion": "O",
            "tranche_effectifs": "21",
            "unite_purgee": None,
            "updated_at": "2021-08-03T02:01:36.835+02:00",
        }
    }


def create_venues_with_no_siret(nb_venues, offerer, bank_information=None):
    venues = VenueFactory.create_batch(
        nb_venues,
        managingOfferer=offerer,
        siret=None,
        comment="Can i have money without having a proper company please ?",
    )

    if bank_information:
        [
            BankInformationFactory(
                venue=venue,
                bic=bank_information.bic,
                iban=bank_information.iban,
            )
            for venue in venues
        ]

    return venues


class AutoFillBusinessUnitSiretTest:
    @pytest.mark.usefixtures("db_session")
    def test_case_reused_venue_with_siret_bank_information(self):
        offerer = OffererFactory()
        BankInformationFactory(offerer=offerer)
        venue = VenueFactory(managingOfferer=offerer)

        venue_bank_information = BankInformationFactory(venue=venue)
        venues = create_venues_with_no_siret(2, offerer, venue_bank_information)

        autofill_business_unit_siret()

        business_units = BusinessUnit.query.all()
        assert len(business_units) == 1

        business_unit = business_units[0]
        assert business_unit.siret == venue.siret
        assert business_unit.bankAccountId == venue_bank_information.id
        assert venue.businessUnitId == business_unit.id
        assert venues[0].businessUnitId == business_unit.id
        assert venues[1].businessUnitId == business_unit.id

    @pytest.mark.usefixtures("db_session")
    def test_case_offer_bank_information_used_multiple_venues_one_siret(self):
        offerer = OffererFactory()
        bank_information = BankInformationFactory(offerer=offerer)
        venue = VenueFactory(managingOfferer=offerer)
        venues = create_venues_with_no_siret(2, offerer)
        venues = venues + create_venues_with_no_siret(2, offerer, bank_information)

        autofill_business_unit_siret()

        business_units = BusinessUnit.query.all()
        assert len(business_units) == 1

        business_unit = business_units[0]
        assert business_unit.siret == venue.siret
        assert business_unit.bankAccountId == bank_information.id

        assert venue.businessUnitId == business_unit.id
        assert venues[0].businessUnitId == business_unit.id
        assert venues[1].businessUnitId == business_unit.id
        assert venues[2].businessUnitId == business_unit.id
        assert venues[3].businessUnitId == business_unit.id

    @patch("pcapi.connectors.api_entreprises.requests.get")
    @pytest.mark.usefixtures("db_session")
    def test_case_from_api_associate_main_siret_address_match(self, mock_api_entreprise):
        offerer = OffererFactory()
        BankInformationFactory(offerer=offerer)

        main_venue_data = {
            "name": "main venue name",
            "address": "main venue address",
            "postalCode": "74001",
            "city": "Donno town",
        }
        venue = VenueFactory(
            **main_venue_data,
            managingOfferer=offerer,
            siret=None,
            comment="Can i have money without having a proper company please ?",
        )
        venue_bank_information = BankInformationFactory(venue=venue)
        venues = create_venues_with_no_siret(2, offerer, venue_bank_information)

        siren_api_main_venue_siret = f"{offerer.siren}99999"

        mock_api_entreprise.return_value = MagicMock(
            status_code=200,
            text="",
            json=MagicMock(
                return_value=get_api_response(
                    offerer.siren,
                    venue_data={
                        **main_venue_data,
                        "siret": siren_api_main_venue_siret,
                    },
                )
            ),
        )
        autofill_business_unit_siret()

        assert venue.siret == siren_api_main_venue_siret

        business_units = BusinessUnit.query.all()
        assert len(business_units) == 1

        business_unit = business_units[0]
        assert business_unit.siret == venue.siret
        assert business_unit.bankAccountId == venue_bank_information.id
        assert venue.businessUnitId == business_unit.id
        assert venues[0].businessUnitId == business_unit.id
        assert venues[1].businessUnitId == business_unit.id

    @patch("pcapi.connectors.api_entreprises.requests.get")
    @pytest.mark.usefixtures("db_session")
    def test_case_from_api_associate_main_siret_siret_match(self, mock_api_entreprise):
        offerer = OffererFactory()
        BankInformationFactory(offerer=offerer)

        venue = VenueFactory(managingOfferer=offerer)
        venue_bank_information = BankInformationFactory(venue=venue)
        other_venue_with_siret = VenueFactory(managingOfferer=offerer)
        other_venue_bank_information = BankInformationFactory(
            venue=other_venue_with_siret, bic=venue_bank_information.bic, iban=venue_bank_information.iban
        )
        venues = create_venues_with_no_siret(2, offerer, venue_bank_information)

        siren_api_main_venue_siret = venue.siret

        mock_api_entreprise.return_value = MagicMock(
            status_code=200,
            text="",
            json=MagicMock(
                return_value=get_api_response(
                    offerer.siren,
                    venue_data={
                        "siret": siren_api_main_venue_siret,
                    },
                )
            ),
        )
        script_return = autofill_business_unit_siret()
        [print("script_return", to_dump) for to_dump in script_return]
        [print("script_return", script_return[to_dump]) for to_dump in script_return]

        business_units = BusinessUnit.query.all()
        assert len(business_units) == 1

        business_unit = business_units[0]
        assert business_unit.siret == venue.siret
        assert business_unit.bankAccountId == venue_bank_information.id
        assert venue.businessUnitId == business_unit.id
        assert venues[0].businessUnitId == business_unit.id
        assert venues[1].businessUnitId == business_unit.id
