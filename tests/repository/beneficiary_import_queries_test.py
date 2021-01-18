from datetime import datetime

import pytest

from pcapi.model_creators.generic_creators import create_beneficiary_import
from pcapi.model_creators.generic_creators import create_user
from pcapi.models import ImportStatus
from pcapi.repository import repository
from pcapi.repository.beneficiary_import_queries import find_applications_ids_to_retry
from pcapi.repository.beneficiary_import_queries import is_already_imported


class IsAlreadyImportedTest:
    @pytest.mark.usefixtures("db_session")
    def test_returns_true_when_a_beneficiary_import_exist_with_status_created(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(
            user=beneficiary, status=ImportStatus.CREATED, application_id=123
        )

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(123)

        # then
        assert result is True

    @pytest.mark.usefixtures("db_session")
    def test_returns_true_when_a_beneficiary_import_exist_with_status_duplicate(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(
            user=beneficiary, status=ImportStatus.DUPLICATE, application_id=123
        )

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(123)

        # then
        assert result is True

    @pytest.mark.usefixtures("db_session")
    def test_returns_true_when_a_beneficiary_import_exist_with_status_rejected(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(
            user=beneficiary, status=ImportStatus.REJECTED, application_id=123
        )

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(123)

        # then
        assert result is True

    @pytest.mark.usefixtures("db_session")
    def test_returns_true_when_a_beneficiary_import_exist_with_status_error(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(user=beneficiary, status=ImportStatus.ERROR, application_id=123)

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(123)

        # then
        assert result is True

    @pytest.mark.usefixtures("db_session")
    def test_returns_false_when_a_beneficiary_import_exist_with_status_retry(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(user=beneficiary, status=ImportStatus.RETRY, application_id=123)

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(123)

        # then
        assert result is False

    @pytest.mark.usefixtures("db_session")
    def test_returns_false_when_no_beneficiary_import_exist_for_this_id(self, app):
        # given
        now = datetime.utcnow()
        beneficiary = create_user(date_created=now)
        beneficiary_import = create_beneficiary_import(
            user=beneficiary, status=ImportStatus.CREATED, application_id=123
        )

        repository.save(beneficiary_import)

        # when
        result = is_already_imported(456)

        # then
        assert result is False


class FindApplicationsIdsToRetryTest:
    @pytest.mark.usefixtures("db_session")
    def test_returns_applications_ids_with_current_status_retry(self, app):
        # given
        beneficiary = create_user()
        imports = [
            create_beneficiary_import(status=ImportStatus.RETRY, application_id=456),
            create_beneficiary_import(status=ImportStatus.RETRY, application_id=123),
            create_beneficiary_import(user=beneficiary, status=ImportStatus.CREATED, application_id=789),
        ]

        repository.save(*imports)

        # when
        ids = find_applications_ids_to_retry()

        # then
        assert ids == [123, 456]

    @pytest.mark.usefixtures("db_session")
    def test_returns_an_empty_list_if_no_retry_imports_exist(self, app):
        # given
        beneficiary = create_user()
        imports = [
            create_beneficiary_import(status=ImportStatus.DUPLICATE, application_id=456),
            create_beneficiary_import(status=ImportStatus.ERROR, application_id=123),
            create_beneficiary_import(user=beneficiary, status=ImportStatus.CREATED, application_id=789),
        ]

        repository.save(*imports)

        # when
        ids = find_applications_ids_to_retry()

        # then
        assert not ids
