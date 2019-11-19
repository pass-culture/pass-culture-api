import pytest

from domain.departments import get_departement_codes_from_user
from unittest.mock import patch
from tests.test_utils import create_user


class GetDepartementCodesFromUser:
    def test_departments_mapping_with_known_department_code(self):
        # given
        user = create_user(departement_code='973')

        # when
        with patch('domain.departments.DEPARTEMENT_CODE_VISIBILITY', {'08': ['02', '08'], '97': ['971', '97']}):
            departement_codes = get_departement_codes_from_user(user)

        # then
        assert set(departement_codes) == set(['971', '97'])

    def test_departments_mapping_with_unknown_department_code(self):
        # given
        user = create_user(departement_code='32')

        # when
        with patch('domain.departments.DEPARTEMENT_CODE_VISIBILITY', {'08': ['02', '08'], '97': ['971', '97']}):
            departement_codes = get_departement_codes_from_user(user)

        # then
        assert departement_codes == ['32']
