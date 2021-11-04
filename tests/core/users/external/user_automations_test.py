import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import pytest

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.core.users.external.user_automations import get_inactive_user_since_thirty_days
from pcapi.core.users.external.user_automations import get_users_by_month_created_one_year_before
from pcapi.core.users.external.user_automations import get_users_who_will_turn_eighteen_in_one_month
import pcapi.core.users.factories as users_factories
from pcapi.models import User


@pytest.mark.usefixtures("db_session")
class UserAutomationsTest:
    @freeze_time("2021-08-01 10:00:00")
    def test_get_users_who_will_turn_eighteen_in_one_month(self):
        AGE20_NOT_ELIGIBLE_BIRTH_DATE = datetime.datetime.utcnow() - relativedelta(years=20)
        _18_YEARS_IN_1_MONTHS = (
            datetime.datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
            - relativedelta(years=ELIGIBILITY_AGE_18)
            + relativedelta(days=30)
        )
        user = users_factories.UserFactory(email="fabien+test@example.net", dateOfBirth=_18_YEARS_IN_1_MONTHS)
        users_factories.UserFactory(email="bernard+test@example.net", dateOfBirth=AGE20_NOT_ELIGIBLE_BIRTH_DATE)
        result = get_users_who_will_turn_eighteen_in_one_month()
        assert len(result) == 1
        assert result[0].email == user.email

        assert len(User.query.all()) == 2

    @freeze_time("2021-08-01 10:00:00")
    def test_get_users_having_one_year_since_subscription_by_month(self):
        with freeze_time("2021-08-01 15:00:00") as frozen_time:

            user = users_factories.UserFactory(
                email="fabien+test@example.net", dateCreated=datetime.datetime(2021, 8, 1)
            )
            user2 = users_factories.UserFactory(
                email="daniel+test@example.net", dateCreated=datetime.datetime(2021, 8, 31)
            )
            user3 = users_factories.UserFactory(
                email="billy+test@example.net", dateCreated=datetime.datetime(2021, 7, 31)
            )
            user4 = users_factories.UserFactory(
                email="gerard+test@example.net", dateCreated=datetime.datetime(2021, 9, 1)
            )
            frozen_time.move_to("2022-08-20 15:00:00")
            results = get_users_by_month_created_one_year_before()
            assert len(results) == 2
            for result in results:
                assert result.email in [user.email, user2.email]
                assert result.email not in [user3.email, user4.email]

    @freeze_time("2021-08-01 10:00:00")
    def test_get_inactive_user_since_thirty_days(self):
        with freeze_time("2021-08-01 15:00:00") as frozen_time:

            user = users_factories.UserFactory(
                email="fabien+test@example.net", lastConnectionDate=datetime.datetime(2021, 8, 1)
            )
            user2 = users_factories.UserFactory(
                email="daniel+test@example.net", lastConnectionDate=datetime.datetime(2021, 8, 2)
            )
            user3 = users_factories.UserFactory(
                email="billy+test@example.net", dateCreated=datetime.datetime(2021, 7, 31)
            )
            user4 = users_factories.UserFactory(
                email="gerard+test@example.net", dateCreated=datetime.datetime(2021, 9, 1)
            )
            frozen_time.move_to("2021-08-31 15:00:01")
            result = get_inactive_user_since_thirty_days()
            assert len(result) == 1
            result = result[0]
            assert result.email == user.email
            assert result.email not in [user2.email, user3.email, user4.email]
