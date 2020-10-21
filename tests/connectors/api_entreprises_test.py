from unittest.mock import patch, \
    MagicMock

import pytest

from pcapi.connectors.api_entreprises import ApiEntrepriseException, \
    get_by_offerer
from pcapi.model_creators.generic_creators import create_offerer


class GetByOffererTest:
    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_raises_ApiEntrepriseException_when_sirene_api_does_not_respond(self, requests_get):
        # Given
        requests_get.return_value = MagicMock(status_code=400)

        offerer = create_offerer(siren='732075312')

        # When
        with pytest.raises(ApiEntrepriseException) as error:
            get_by_offerer(offerer)

        # Then
        assert 'Error getting API entreprise DATA for SIREN' in str(error.value)

    @patch('pcapi.connectors.api_entreprises.json_logger.error')
    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_tracks_when_no_result_for_siren(self, requests_get, json_logger_error):
        # Given
        requests_get.return_value = MagicMock(status_code=400)
        siren = '732075312'
        offerer = create_offerer(siren=siren)

        # When
        with pytest.raises(ApiEntrepriseException):
            get_by_offerer(offerer)

        # Then
        json_logger_error.assert_called_once()
        json_logger_error.assert_called_with("Error getting API entreprise data",
                                             extra={'siren': siren, 'service': 'ApiEntreprise'})

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_call_sirene_with_offerer_siren(self, requests_get):
        # Given
        offerer = create_offerer(siren='732075312')
        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
            },
            "etablissements": []
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        get_by_offerer(offerer)

        # Then
        requests_get.assert_called_once_with("https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/732075312",
                                             verify=False)

    @patch('pcapi.connectors.api_entreprises.requests.get')
    @patch('pcapi.connectors.api_entreprises.json_logger.info')
    def test_tracks_calls_to_api_entreprise(self, requests_get, json_logger_info):
        # Given
        siren = '732075312'
        offerer = create_offerer(siren=siren)
        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
            },
            "etablissements": []
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        get_by_offerer(offerer)

        # Then
        json_logger_info.assert_called_once()
        json_logger_info.assert_called_with("Loading offerer by siren with entreprise API",
                                            extra={'siren': siren, 'service': 'ApiEntreprise'})

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_returns_unite_legale_informations_with_etablissement_siege(self, requests_get):
        # Given
        offerer = create_offerer(siren='732075312')

        mocked_api_response = MagicMock(status_code=200)
        requests_get.return_value = mocked_api_response

        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
            },
            "etablissements": []
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        response = get_by_offerer(offerer)

        # Then
        assert response == json_response

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_returns_unite_legale_informations_without_etablissements_list(self, requests_get):
        # Given
        offerer = create_offerer(siren='732075312')

        mocked_api_response = MagicMock(status_code=200)
        requests_get.return_value = mocked_api_response

        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
                "etablissement_siege": "true",
            },
            "etablissements": [
                {
                    "siren": "395251440",
                    "siret": "39525144000032",
                    "etablissement_siege": "true",
                    "enseigne_1": "UGC CAFE",
                }
            ]
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        response = get_by_offerer(offerer)

        # Then
        assert "etablissements" not in response["unite_legale"]

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_returns_unite_legale_informations_with_empty_other_etablissements_sirets_when_no_other_etablissements(self,
                                                                                                                   requests_get):
        # Given
        offerer = create_offerer(siren='732075312')

        mocked_api_response = MagicMock(status_code=200)
        requests_get.return_value = mocked_api_response

        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
                "etablissement_siege": "true",
            },
            "etablissements": [
                {
                    "siren": "395251440",
                    "siret": "39525144000032",
                    "etablissement_siege": "true",
                    "enseigne_1": "UGC CAFE",
                }
            ]
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        response = get_by_offerer(offerer)

        # Then
        assert response["other_etablissements_sirets"] == []

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_returns_other_etablissements_sirets_with_all_etablissement_siret(self, requests_get):
        # Given
        offerer = create_offerer(siren='732075312')

        mocked_api_response = MagicMock(status_code=200)
        requests_get.return_value = mocked_api_response

        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
                "etablissement_siege": "true",
            },
            "etablissements": [
                {
                    "siren": "395251440",
                    "siret": "39525144000032",
                    "etablissement_siege": "false",
                    "enseigne_1": "UGC CAFE",
                },
                {
                    "siren": "395251440",
                    "siret": "39525144000065",
                    "etablissement_siege": "false",
                    "enseigne_1": "UGC CINE CITE BERCY - UGC CAFE",
                }
            ]
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        response = get_by_offerer(offerer)

        # Then
        assert set(response["other_etablissements_sirets"]) == {"39525144000032", "39525144000065"}

    @patch('pcapi.connectors.api_entreprises.requests.get')
    def test_returns_other_etablissements_sirets_without_etablissement_siege_siret(self, requests_get):
        # Given
        offerer = create_offerer(siren='732075312')

        mocked_api_response = MagicMock(status_code=200)
        requests_get.return_value = mocked_api_response

        json_response = {"unite_legale": {
            "siren": "395251440",
            "denomination": "UGC CINE CITE ILE DE FRANCE",
            "etablissement_siege": {
                "siren": "395251440",
                "siret": "39525144000016",
                "etablissement_siege": "true",
            },
            "etablissements": [
                {
                    "siren": "395251440",
                    "siret": "39525144000032",
                    "etablissement_siege": "false",
                    "enseigne_1": "UGC CAFE",
                },
                {
                    "siren": "395251440",
                    "siret": "39525144000016",
                    "etablissement_siege": "true",
                },
            ]
        }}
        mocked_api_response = MagicMock(status_code=200, text='')
        mocked_api_response.json = MagicMock(return_value=json_response)
        requests_get.return_value = mocked_api_response

        # When
        response = get_by_offerer(offerer)

        # Then
        assert set(response["other_etablissements_sirets"]) == {"39525144000032"}
