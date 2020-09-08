from datetime import datetime
from unittest.mock import patch, call

from models import UserSQLEntity, ImportStatus, BeneficiaryImport
from repository import repository
from scripts.id_check.fix_jouve_applications import fix_beneficiaries_with_wrong_date_of_birth, \
    fix_eligible_beneficiaries_who_were_refused, fix_failed_jobs
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_user, create_beneficiary_import


class FixFailedJobsTest:
    @patch('scripts.id_check.fix_jouve_applications.beneficiary_job')
    def test_should_add_application_ids_to_redis_queue(self,
                                                       beneficiary_job,
                                                       app):
        # when
        fix_failed_jobs(application_ids=[123, 456, 789])

        # then
        assert beneficiary_job.call_args_list == [
            call(application_id=123),
            call(application_id=456),
            call(application_id=789),
        ]


class FixBeneficiariesWithWrongDateOfBirthTest:
    @clean_database
    def test_should_fix_date_of_birth_of_users_imported_from_jouve_where_date_of_import_is_before_date_limit(self, app):
        # given
        beneficiary_jouve1_date_created = datetime(2020, 9, 3)
        beneficiary_jouve1 = create_user(date_created=beneficiary_jouve1_date_created,
                                         date_of_birth=datetime(2002, 12, 1),
                                         email="john.doe@example.net")
        beneficiary_import_jouve1 = create_beneficiary_import(user=beneficiary_jouve1,
                                                              date=beneficiary_jouve1_date_created,
                                                              source='jouve',
                                                              application_id=123)
        beneficiary_jouve2_date_created = datetime(2020, 9, 9)
        beneficiary_jouve2 = create_user(date_created=beneficiary_jouve2_date_created,
                                         date_of_birth=datetime(2002, 5, 1),
                                         email="tony.stark@example.net")
        beneficiary_import_jouve2 = create_beneficiary_import(user=beneficiary_jouve2,
                                                              date=beneficiary_jouve2_date_created,
                                                              source='jouve',
                                                              application_id=789)
        beneficiary_dms = create_user(date_created=datetime.utcnow(),
                                      email="captain.america@example.net")
        beneficiary_import_dms = create_beneficiary_import(user=beneficiary_dms,
                                                           source='demarches_simplifiees',
                                                           application_id=456)
        repository.save(beneficiary_import_jouve1, beneficiary_import_jouve2, beneficiary_import_dms)

        # when
        fix_beneficiaries_with_wrong_date_of_birth(date_limit=datetime(2020, 9, 8))

        # then
        beneficiary_jouve_to_have_been_updated = UserSQLEntity.query.filter_by(email=beneficiary_jouve1.email).first()
        beneficiary_jouve_to_not_have_been_updated = UserSQLEntity.query.filter_by(
            email=beneficiary_jouve2.email).first()
        beneficiary_dms_to_not_have_been_updated = UserSQLEntity.query.filter_by(email=beneficiary_dms.email).first()
        assert beneficiary_jouve_to_have_been_updated.dateOfBirth == datetime(2002, 1, 12)
        assert beneficiary_jouve_to_not_have_been_updated.dateOfBirth == beneficiary_jouve2.dateOfBirth
        assert beneficiary_dms_to_not_have_been_updated.dateOfBirth == beneficiary_dms.dateOfBirth


class FixEligibleBeneficiariesWhoWereRefusedTest:
    @clean_database
    @patch('scripts.id_check.fix_jouve_applications.beneficiary_job')
    def test_should_delete_rows_when_beneficiaries_are_initially_eligible_and_were_added_before_date_limit(self,
                                                                                                           beneficiary_job,
                                                                                                           app):
        # given
        beneficiary_import_jouve1 = create_beneficiary_import(date=datetime(2020, 9, 3),
                                                              status=ImportStatus.REJECTED,
                                                              source='jouve',
                                                              application_id=123)
        beneficiary_import_jouve2 = create_beneficiary_import(date=(datetime(2020, 9, 9)),
                                                              status=ImportStatus.REJECTED,
                                                              source='jouve',
                                                              application_id=789)
        beneficiary_import_dms = create_beneficiary_import(source='demarches_simplifiees',
                                                           application_id=456)
        repository.save(beneficiary_import_jouve1, beneficiary_import_jouve2, beneficiary_import_dms)

        # when
        fix_eligible_beneficiaries_who_were_refused(date_limit=datetime(2020, 9, 8))

        # then
        beneficiaries_import_from_jouve = BeneficiaryImport.query.filter(BeneficiaryImport.source == 'jouve').all()
        assert len(beneficiaries_import_from_jouve) == 1
        assert beneficiary_import_jouve1 not in beneficiaries_import_from_jouve
        assert beneficiary_import_jouve2 in beneficiaries_import_from_jouve

    @clean_database
    @patch('scripts.id_check.fix_jouve_applications.beneficiary_job')
    def test_add_application_ids_from_jouve_to_redis_when_beneficiary_imports_were_deleted(self, beneficiary_job, app):
        # given
        beneficiary_import_jouve1 = create_beneficiary_import(date=datetime(2020, 9, 3),
                                                              status=ImportStatus.REJECTED,
                                                              source='jouve',
                                                              application_id=123)
        beneficiary_import_jouve2 = create_beneficiary_import(date=(datetime(2020, 9, 9)),
                                                              status=ImportStatus.REJECTED,
                                                              source='jouve',
                                                              application_id=789)
        beneficiary_import_dms = create_beneficiary_import(source='demarches_simplifiees',
                                                           application_id=456)
        repository.save(beneficiary_import_jouve1, beneficiary_import_jouve2, beneficiary_import_dms)

        # when
        fix_eligible_beneficiaries_who_were_refused(date_limit=datetime(2020, 9, 8))

        # then
        beneficiaries_import_from_jouve = BeneficiaryImport.query.filter(BeneficiaryImport.source == 'jouve').all()
        assert len(beneficiaries_import_from_jouve) == 1
        assert beneficiary_import_jouve1 not in beneficiaries_import_from_jouve
        assert beneficiary_import_jouve2 in beneficiaries_import_from_jouve
        assert beneficiary_job.call_args_list == [call(application_id=123)]
