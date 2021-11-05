from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import pytest
from sib_api_v3_sdk import RemoveContactFromList
from sib_api_v3_sdk import RequestContactImport

from pcapi import settings
import pcapi.core.bookings.factories as bookings_factories
from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.core.users.external.user_automations import (
    users_beneficiary_credit_expiration_within_next_3_months_automation,
)
from pcapi.core.users.external.user_automations import get_inactive_user_since_thirty_days
from pcapi.core.users.external.user_automations import get_users_beneficiary_credit_expiration_within_next_3_months
from pcapi.core.users.external.user_automations import get_users_by_month_created_one_year_before
from pcapi.core.users.external.user_automations import get_users_ex_beneficiary
from pcapi.core.users.external.user_automations import get_users_who_will_turn_eighteen_in_one_month
from pcapi.core.users.external.user_automations import user_ex_beneficiary_automation
from pcapi.core.users.external.user_automations import user_turned_eighteen_automation
from pcapi.core.users.external.user_automations import users_inactive_since_30_days_automation
from pcapi.core.users.external.user_automations import users_one_year_with_pass_automation
import pcapi.core.users.factories as users_factories
from pcapi.core.users.models import UserRole
from pcapi.models import User


@pytest.mark.usefixtures("db_session")
class UserAutomationsTest:
    def _create_users_around_18(self):
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        users_factories.UserFactory(
            email="marc+test@example.net",
            dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-29),
            roles=[UserRole.BENEFICIARY],
        )
        users_factories.UserFactory(
            email="fabien+test@example.net",
            dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-30),
            roles=[UserRole.BENEFICIARY],
        )
        users_factories.UserFactory(
            email="daniel+test@example.net",
            dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-31),
            roles=[UserRole.BENEFICIARY],
        )
        users_factories.UserFactory(
            email="bernard+test@example.net", dateOfBirth=today - relativedelta(years=20), roles=[UserRole.BENEFICIARY]
        )
        users_factories.UserFactory(
            email="pro+test@example.net",
            dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-30),
            roles=[UserRole.PRO],
        )
        users_factories.UserFactory(
            email="gerard+test@example.net",
            dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-30),
            roles=[UserRole.UNDERAGE_BENEFICIARY],
        )

    @freeze_time("2021-08-01 10:00:00")
    def test_get_users_who_will_turn_eighteen_in_one_month(self):
        self._create_users_around_18()

        result = get_users_who_will_turn_eighteen_in_one_month()
        assert sorted([user.email for user in result]) == ["fabien+test@example.net", "gerard+test@example.net"]
        assert len(User.query.all()) == 6

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_user_turned_eighteen_automation(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        self._create_users_around_18()

        result = user_turned_eighteen_automation()

        mock_remove_contact_from_list.assert_called_once_with(
            settings.SENDINBLUE_AUTOMATION_YOUNG_18_IN_1_MONTH_LIST_ID,
            RemoveContactFromList(emails=None, ids=None, all=True),
        )

        mock_import_contacts.assert_called_once_with(
            RequestContactImport(
                file_url=None,
                file_body="EMAIL\nfabien+test@example.net\ngerard+test@example.net\n",
                list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_18_IN_1_MONTH_LIST_ID],
                notify_url=None,
                new_list=None,
                email_blacklist=False,
                sms_blacklist=False,
                update_existing_contacts=True,
                empty_contacts_attributes=False,
            )
        )

        mock_get_process.assert_called()

        assert result is True

    @pytest.mark.skip(reason="Need manual check, order of email addresses in file_body can't be predictable")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_user_turned_eighteen_automation_1500(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        today = datetime.combine(datetime.today(), datetime.min.time())

        for i in range(1, 1501):
            users_factories.UserFactory(
                email=f"fabien+test+{i}@example.net",
                dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=-30),
                roles=[UserRole.BENEFICIARY],
            )
            users_factories.UserFactory(
                email=f"daniel+test+{i}@example.net",
                dateOfBirth=today - relativedelta(years=ELIGIBILITY_AGE_18, days=3),
                roles=[UserRole.BENEFICIARY],
            )

        result = user_turned_eighteen_automation()

        mock_remove_contact_from_list.assert_called_once_with(
            settings.SENDINBLUE_AUTOMATION_YOUNG_18_IN_1_MONTH_LIST_ID,
            RemoveContactFromList(emails=None, ids=None, all=True),
        )

        mock_import_contacts.assert_called_once_with(
            RequestContactImport(
                file_url=None,
                file_body="EMAIL\n" + "".join([f"fabien+test+{i}@example.net\n" for i in range(1, 1501)]),
                list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_18_IN_1_MONTH_LIST_ID],
                notify_url=None,
                new_list=None,
                email_blacklist=False,
                sms_blacklist=False,
                update_existing_contacts=True,
                empty_contacts_attributes=False,
            )
        )

        mock_get_process.assert_called()

        assert result is True

    def _create_users_with_deposits(self):
        with freeze_time("2020-11-15 15:00:00"):
            user0 = users_factories.UserFactory(
                email="beneficiary0+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=17, days=5),
                roles=[UserRole.UNDERAGE_BENEFICIARY],
            )
            assert user0.deposit is None

        with freeze_time("2020-10-31 15:00:00"):
            user1 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary1+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=1),
            )
            assert user1.deposit.expirationDate == datetime(2022, 10, 31, 15, 0, 0)

        with freeze_time("2020-11-01 15:00:00"):
            user2 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary2+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=2),
            )
            assert user2.deposit.expirationDate == datetime(2022, 11, 1, 15, 0, 0)
            bookings_factories.UsedIndividualBookingFactory(individualBooking__user=user2, quantity=1, amount=10)
            assert user2.real_wallet_balance > 0

        with freeze_time("2020-12-01 15:00:00"):
            user3 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary3+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=3),
            )
            assert user3.deposit.expirationDate == datetime(2022, 12, 1, 15, 0, 0)

        with freeze_time("2021-01-30 15:00:00"):
            user4 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary4+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=4),
            )
            assert user4.deposit.expirationDate == datetime(2023, 1, 30, 15, 0, 0)

        with freeze_time("2021-01-31 15:00:00"):
            user5 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary5+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=5),
            )
            assert user5.deposit.expirationDate == datetime(2023, 1, 31, 15, 0, 0)

        with freeze_time("2021-03-10 15:00:00"):
            user6 = users_factories.BeneficiaryGrant18Factory(
                email="beneficiary6+test@example.net",
                dateOfBirth=datetime.combine(datetime.today(), datetime.min.time()) - relativedelta(years=18, months=5),
            )
            assert user6.deposit.expirationDate == datetime(2023, 3, 10, 15, 0, 0)

        with freeze_time("2021-05-01 17:00:00"):
            # user6 becomes ex-beneficiary
            bookings_factories.UsedIndividualBookingFactory(
                individualBooking__user=user6, quantity=1, amount=int(user6.real_wallet_balance)
            )
            assert user6.real_wallet_balance == 0

        return [user0, user1, user2, user3, user4, user5, user6]

    def test_get_users_beneficiary_three_months_before_credit_expiration(self):
        users = self._create_users_with_deposits()

        with freeze_time("2022-10-31 16:00:00"):
            results = get_users_beneficiary_credit_expiration_within_next_3_months()
            assert sorted([user.email for user in results]) == [user.email for user in users[1:4]]

        with freeze_time("2022-11-01 14:00:00"):
            results = get_users_beneficiary_credit_expiration_within_next_3_months()
            assert sorted([user.email for user in results]) == [user.email for user in users[2:5]]

        with freeze_time("2022-11-02 12:00:00"):
            results = get_users_beneficiary_credit_expiration_within_next_3_months()
            assert sorted([user.email for user in results]) == [user.email for user in users[3:6]]

        with freeze_time("2023-01-15 08:00:00"):
            results = get_users_beneficiary_credit_expiration_within_next_3_months()
            assert sorted([user.email for user in results]) == [user.email for user in users[4:7]]

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_users_beneficiary_credit_expiration_within_next_3_months_automation(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        users = self._create_users_with_deposits()

        with freeze_time("2022-11-01 16:00:00"):
            result = users_beneficiary_credit_expiration_within_next_3_months_automation()

        mock_remove_contact_from_list.assert_called_once_with(
            settings.SENDINBLUE_AUTOMATION_YOUNG_EXPIRATION_M3_ID,
            RemoveContactFromList(emails=None, ids=None, all=True),
        )

        mock_import_contacts.assert_called_once_with(
            RequestContactImport(
                file_url=None,
                file_body=f"EMAIL\n{users[2].email}\n{users[3].email}\n{users[4].email}\n",
                list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_EXPIRATION_M3_ID],
                notify_url=None,
                new_list=None,
                email_blacklist=False,
                sms_blacklist=False,
                update_existing_contacts=True,
                empty_contacts_attributes=False,
            )
        )

        mock_get_process.assert_called()

        assert result is True

    def test_get_users_ex_beneficiary(self):
        users = self._create_users_with_deposits()

        with freeze_time("2022-12-01 16:00:00"):
            results = get_users_ex_beneficiary()
            assert sorted([user.email for user in results]) == [user.email for user in users[1:3] + [users[6]]]

        with freeze_time("2022-12-02 16:00:00"):
            results = get_users_ex_beneficiary()
            assert sorted([user.email for user in results]) == [user.email for user in users[1:4] + [users[6]]]

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_user_ex_beneficiary_automation(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        users = self._create_users_with_deposits()

        with freeze_time("2022-12-01 16:00:00"):
            result = user_ex_beneficiary_automation()

        mock_remove_contact_from_list.assert_not_called()

        mock_import_contacts.assert_called_once_with(
            RequestContactImport(
                file_url=None,
                file_body=f"EMAIL\n{users[1].email}\n{users[2].email}\n{users[6].email}\n",
                list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_EX_BENEFICIARY_ID],
                notify_url=None,
                new_list=None,
                email_blacklist=False,
                sms_blacklist=False,
                update_existing_contacts=True,
                empty_contacts_attributes=False,
            )
        )

        mock_get_process.assert_called()

        assert result is True

    def test_get_inactive_user_since_thirty_days(self):
        with freeze_time("2021-08-01 15:00:00") as frozen_time:
            beneficiary = users_factories.BeneficiaryGrant18Factory(
                email="fabien+test@example.net", lastConnectionDate=datetime(2021, 8, 1)
            )
            not_beneficiary = users_factories.UserFactory(
                email="marc+test@example.net", lastConnectionDate=datetime(2021, 8, 1)
            )
            users_factories.UserFactory(
                email="pierre+test@example.net",
                lastConnectionDate=datetime(2021, 8, 1),
                roles=[UserRole.PRO],
            )
            users_factories.UserFactory(email="daniel+test@example.net", lastConnectionDate=datetime(2021, 8, 2))
            users_factories.UserFactory(email="billy+test@example.net", dateCreated=datetime(2021, 7, 31))
            users_factories.UserFactory(email="gerard+test@example.net", dateCreated=datetime(2021, 9, 1))

            frozen_time.move_to("2021-08-31 15:00:01")
            results = get_inactive_user_since_thirty_days()
            assert sorted([user.email for user in results]) == sorted([beneficiary.email, not_beneficiary.email])

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_users_inactive_since_30_days_automation(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        with freeze_time("2021-08-01 15:00:00") as frozen_time:
            users_factories.BeneficiaryGrant18Factory(
                email="fabien+test@example.net", lastConnectionDate=datetime(2021, 8, 1)
            )
            users_factories.UserFactory(
                email="pierre+test@example.net",
                lastConnectionDate=datetime(2021, 8, 1),
                roles=[UserRole.PRO],
            )
            users_factories.UserFactory(email="daniel+test@example.net", lastConnectionDate=datetime(2021, 8, 2))
            users_factories.UserFactory(email="billy+test@example.net", dateCreated=datetime(2021, 7, 31))
            users_factories.UserFactory(email="gerard+test@example.net", dateCreated=datetime(2021, 9, 1))

            frozen_time.move_to("2021-08-31 15:00:01")

            result = users_inactive_since_30_days_automation()

            mock_remove_contact_from_list.assert_called_once_with(
                settings.SENDINBLUE_AUTOMATION_YOUNG_INACTIVE_30_DAYS_LIST_ID,
                RemoveContactFromList(emails=None, ids=None, all=True),
            )

            mock_import_contacts.assert_called_once_with(
                RequestContactImport(
                    file_url=None,
                    file_body="EMAIL\nfabien+test@example.net\n",
                    list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_INACTIVE_30_DAYS_LIST_ID],
                    notify_url=None,
                    new_list=None,
                    email_blacklist=False,
                    sms_blacklist=False,
                    update_existing_contacts=True,
                    empty_contacts_attributes=False,
                )
            )

            mock_get_process.assert_called()

            assert result is True

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_users_inactive_since_30_days_automation_no_result(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        with freeze_time("2021-08-01 15:00:00") as frozen_time:
            users_factories.BeneficiaryGrant18Factory(
                email="fabien+test@example.net", lastConnectionDate=datetime(2021, 8, 1)
            )
            users_factories.UserFactory(email="marc+test@example.net", lastConnectionDate=datetime(2021, 8, 1))
            users_factories.UserFactory(email="daniel+test@example.net", lastConnectionDate=datetime(2021, 8, 2))
            users_factories.UserFactory(email="billy+test@example.net", dateCreated=datetime(2021, 7, 31))
            users_factories.UserFactory(email="gerard+test@example.net", dateCreated=datetime(2021, 9, 1))

            frozen_time.move_to("2021-10-31 15:00:01")

            result = users_inactive_since_30_days_automation()

            mock_remove_contact_from_list.assert_called_once_with(
                settings.SENDINBLUE_AUTOMATION_YOUNG_INACTIVE_30_DAYS_LIST_ID,
                RemoveContactFromList(emails=None, ids=None, all=True),
            )

            mock_import_contacts.assert_not_called()
            mock_get_process.assert_called()

            assert result is True

    def test_get_users_by_month_created_one_year_before(self):
        matching_users = []

        users_factories.UserFactory(email="fabien+test@example.net", dateCreated=datetime(2021, 7, 31))
        matching_users.append(
            users_factories.UserFactory(email="pierre+test@example.net", dateCreated=datetime(2021, 8, 1))
        )
        matching_users.append(
            users_factories.UserFactory(email="marc+test@example.net", dateCreated=datetime(2021, 8, 10))
        )
        matching_users.append(
            users_factories.UserFactory(email="daniel+test@example.net", dateCreated=datetime(2021, 8, 31))
        )
        users_factories.UserFactory(email="billy+test@example.net", dateCreated=datetime(2021, 9, 1))
        users_factories.UserFactory(email="gerard+test@example.net", dateCreated=datetime(2021, 9, 21))

        # matching: from 2021-08-01 to 2021-08-31
        with freeze_time("2022-08-10 15:00:00"):
            results = get_users_by_month_created_one_year_before()
            assert sorted([user.email for user in results]) == sorted([user.email for user in matching_users])

    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.process_api.ProcessApi.get_process")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.import_contacts")
    @patch("pcapi.core.users.external.sendinblue.sib_api_v3_sdk.api.contacts_api.ContactsApi.remove_contact_from_list")
    def test_users_nearly_one_year_with_pass_automation(
        self, mock_remove_contact_from_list, mock_import_contacts, mock_get_process
    ):
        users_factories.UserFactory(email="fabien+test@example.net", dateCreated=datetime(2021, 8, 31))
        users_factories.UserFactory(email="pierre+test@example.net", dateCreated=datetime(2021, 9, 1))
        users_factories.UserFactory(email="daniel+test@example.net", dateCreated=datetime(2021, 10, 1))
        users_factories.UserFactory(email="gerard+test@example.net", dateCreated=datetime(2021, 10, 31))

        # matching: from 2021-09-01 to 2021-09-31
        with freeze_time("2022-09-10 15:00:00"):
            result = users_one_year_with_pass_automation()

        mock_remove_contact_from_list.assert_called_once_with(
            settings.SENDINBLUE_AUTOMATION_YOUNG_1_YEAR_WITH_PASS_LIST_ID,
            RemoveContactFromList(emails=None, ids=None, all=True),
        )

        mock_import_contacts.assert_called_once_with(
            RequestContactImport(
                file_url=None,
                file_body="EMAIL\npierre+test@example.net\n",
                list_ids=[settings.SENDINBLUE_AUTOMATION_YOUNG_1_YEAR_WITH_PASS_LIST_ID],
                notify_url=None,
                new_list=None,
                email_blacklist=False,
                sms_blacklist=False,
                update_existing_contacts=True,
                empty_contacts_attributes=False,
            )
        )

        mock_get_process.assert_called()

        assert result is True
