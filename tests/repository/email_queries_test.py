from models import PcObject
from models.email import EmailStatus
from repository.email_queries import find_all_in_error
from tests.conftest import clean_database
from tests.test_utils import create_email


class FindAllInErrorTest:
    @clean_database
    def test_returns_emails_failed_with_status_ERROR_only(self, app):
        # given
        email = {}
        email_failed_in_error = create_email(email, status=EmailStatus.ERROR)
        email_failed_sent= create_email(email, status=EmailStatus.SENT)

        PcObject.save(email_failed_in_error, email_failed_sent)

        # when
        email_failed_in_error = find_all_in_error()

        # then
        assert len(email_failed_in_error)
        assert email_failed_in_error[0].status == EmailStatus.ERROR
