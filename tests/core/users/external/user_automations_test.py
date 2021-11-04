from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import pytest

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.core.users.external.user_automations import get_users_who_will_turn_eighteen_in_one_month
import pcapi.core.users.factories as users_factories
from pcapi.models import User


@pytest.mark.usefixtures("db_session")
class UserAutomationsTest:
    @freeze_time("2021-08-01 10:00:00")
    def test_get_users_who_will_turn_eighteen_in_one_month(self):
        AGE20_NOT_ELIGIBLE_BIRTH_DATE = datetime.utcnow() - relativedelta(years=20)
        _18_YEARS_IN_1_MONTHS = (
            datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
            - relativedelta(years=ELIGIBILITY_AGE_18)
            + relativedelta(days=30)
        )
        user = users_factories.UserFactory(
            email="fabien+test@example.net", firstName="Fabien", dateOfBirth=_18_YEARS_IN_1_MONTHS
        )
        users_factories.UserFactory(
            email="bernard+test@example.net", firstName="Bernard", dateOfBirth=AGE20_NOT_ELIGIBLE_BIRTH_DATE
        )
        result = get_users_who_will_turn_eighteen_in_one_month()
        assert len(result) == 1
        assert result[0].firstName == user.firstName
        assert result[0].age == user.age

        assert len(User.query.all()) == 2
