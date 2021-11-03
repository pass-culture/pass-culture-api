from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import pytest

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.core.users.external.user_automations import get_users_who_turned_eighteen_today
import pcapi.core.users.factories as users_factories
from pcapi.models import User


@pytest.mark.usefixtures("db_session")
class UserAutomationsTest:
    @freeze_time("2021-08-01 02:00:00")
    def test_get_users_who_turned_eighteen_today(self):
        AGE18_ELIGIBLE_BIRTH_DATE = datetime.today() - relativedelta(years=ELIGIBILITY_AGE_18, months=0)
        AGE20_NOT_ELIGIBLE_BIRTH_DATE = datetime.utcnow() - relativedelta(years=20)
        user = users_factories.UserFactory(
            email="fabien+test@example.net", firstName="Fabien", dateOfBirth=AGE18_ELIGIBLE_BIRTH_DATE
        )
        users_factories.UserFactory(
            email="bernard+test@example.net", firstName="Bernard", dateOfBirth=AGE20_NOT_ELIGIBLE_BIRTH_DATE
        )
        result = get_users_who_turned_eighteen_today()
        assert result[0].firstName == user.firstName == "Fabien"
        assert result[0].age == user.age == 18
        assert len(result) == 1

        assert len(User.query.all()) == 2
