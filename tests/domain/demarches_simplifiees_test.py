from datetime import datetime
from unittest.mock import Mock

from domain.demarches_simplifiees import get_all_application_ids_for_procedure


class GetAllApplicationIdsForProcedureTest:
    def setup_method(self):
        self.PROCEDURE_ID = '123456789'
        self.TOKEN = 'AZERTY123/@.,!é'
        self.mock_get_all_applications_for_procedure = Mock()

    def test_returns_applications_from_all_pages(self):
        # Given
        self.mock_get_all_applications_for_procedure.side_effect = [
            {
                "dossiers": [
                    {"id": 2,
                     "updated_at": "2019-02-04T16:51:18.293Z",
                     "state": "closed"},
                    {"id": 3,
                     "updated_at": "2019-02-03T16:51:18.293Z",
                     "state": "initiated"}
                ],
                'pagination': {
                    'page': 1,
                    'resultats_par_page': 2,
                    'nombre_de_page': 2
                }
            },
            {
                "dossiers": [
                    {"id": 4,
                     "updated_at": "2019-02-04T16:51:18.293Z",
                     "state": "closed"},
                    {"id": 5,
                     "updated_at": "2019-02-03T16:51:18.293Z",
                     "state": "closed"}
                ],
                'pagination': {
                    'page': 1,
                    'resultats_par_page': 2,
                    'nombre_de_page': 2
                }
            }
        ]

        # When
        application_ids = get_all_application_ids_for_procedure(
            self.PROCEDURE_ID, self.TOKEN, datetime(2019, 1, 1),
            get_all_applications=self.mock_get_all_applications_for_procedure
        )

        # Then
        assert sorted(application_ids) == [2, 4, 5]

    def test_returns_applications_with_state_closed_only(self):
        # Given
        self.mock_get_all_applications_for_procedure.side_effect = [{
            "dossiers": [
                {"id": 2,
                 "updated_at": "2019-02-04T16:51:18.293Z",
                 "state": "closed"},
                {"id": 3,
                 "updated_at": "2019-02-03T16:51:18.293Z",
                 "state": "initiated"}
            ],
            'pagination': {
                'page': 1,
                'resultats_par_page': 100,
                'nombre_de_page': 1
            }
        }]

        # When
        application_ids = get_all_application_ids_for_procedure(
            self.PROCEDURE_ID, self.TOKEN, datetime(2019, 1, 1),
            get_all_applications=self.mock_get_all_applications_for_procedure
        )

        # Then
        assert application_ids == [2]

    def test_returns_applications_updated_after_last_update_in_database_only(self):
        # Given
        self.mock_get_all_applications_for_procedure.side_effect = [{
            "dossiers": [
                {"id": 2,
                 "updated_at": "2019-02-04T16:51:18.293Z",
                 "state": "closed"},
                {"id": 3,
                 "updated_at": "2018-12-17T16:51:18.293Z",
                 "state": "closed"}
            ],
            'pagination': {
                'page': 1,
                'resultats_par_page': 100,
                'nombre_de_page': 1
            }
        }]

        # When
        application_ids = get_all_application_ids_for_procedure(
            self.PROCEDURE_ID, self.TOKEN, datetime(2019, 1, 1),
            get_all_applications=self.mock_get_all_applications_for_procedure
        )

        # Then
        assert application_ids == [2]

    def test_returns_list_of_ids_ordered_by_updated_at_asc(self):
        # Given
        self.mock_get_all_applications_for_procedure.side_effect = [{
            "dossiers": [
                {"id": 1,
                 "updated_at": "2019-02-04T16:51:18.293Z",
                 "state": "closed"},
                {"id": 2,
                 "updated_at": "2018-12-17T16:51:18.293Z",
                 "state": "closed"},
                {"id": 3,
                 "updated_at": "2018-11-17T16:51:18.293Z",
                 "state": "closed"},
                {"id": 4,
                 "updated_at": "2019-02-17T16:51:18.293Z",
                 "state": "closed"}
            ],
            'pagination': {
                'page': 1,
                'resultats_par_page': 100,
                'nombre_de_page': 1
            }
        }]

        # When
        application_ids = get_all_application_ids_for_procedure(
            self.PROCEDURE_ID, self.TOKEN, datetime(2018, 1, 1),
            get_all_applications=self.mock_get_all_applications_for_procedure
        )

        # Then
        assert application_ids == [3, 2, 1, 4]
