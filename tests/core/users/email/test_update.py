import pytest

from pcapi.core.mails import testing as mails_testing
from pcapi.core.users import email as email_api
from pcapi.core.users import exceptions as users_exceptions
from pcapi.core.users import factories as users_factories


pytestmark = pytest.mark.usefixtures("db_session")


class UpdateEmailTest:
    def test_update_email(self):
        user = users_factories.UserFactory(email="py@test.com")
        user.setPassword("some_password")

        email_api.update_email(user, "new@email.com", "some_password")
        assert len(mails_testing.outbox) == 2

    def test_token_exists(self):
        user = users_factories.UserFactory(email="py@test.com")
        user.setPassword("some_password")

        with pytest.raises(users_exceptions.EmailUpdateTokenExists):
            email_api.update_email(user, "new@email.com", "some_password")
            email_api.update_email(user, "another@email.com", "some_password")
