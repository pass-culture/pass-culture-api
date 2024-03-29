from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import pcapi.core.mails.testing as mails_testing
from pcapi.core.offers.factories import OfferFactory
from pcapi.core.offers.factories import OffererFactory
from pcapi.core.offers.factories import UserOffererFactory
from pcapi.core.offers.models import OfferValidationStatus
import pcapi.core.users.factories as users_factories
from pcapi.domain.admin_emails import maybe_send_offerer_validation_email
from pcapi.domain.admin_emails import send_offer_creation_notification_to_administration
from pcapi.domain.admin_emails import send_offer_rejection_notification_to_administration
from pcapi.domain.admin_emails import send_offer_validation_notification_to_administration
from pcapi.domain.admin_emails import send_payment_details_email
from pcapi.domain.admin_emails import send_payments_report_emails
from pcapi.domain.admin_emails import send_wallet_balances_email


@pytest.mark.usefixtures("db_session")
@patch("pcapi.connectors.api_entreprises.requests.get")
def test_maybe_send_offerer_validation_email_sends_email_to_pass_culture_when_objects_to_validate(
    mock_api_entreprise, app
):
    # Given
    response_return_value = MagicMock(status_code=200, text="")
    response_return_value.json = MagicMock(
        return_value={
            "unite_legale": {"etablissement_siege": {"siret": ""}, "etablissements": [], "activite_principale": ""}
        }
    )
    mock_api_entreprise.return_value = response_return_value
    user = users_factories.UserFactory()
    offerer = OffererFactory(validationToken="12356")
    user_offerer = UserOffererFactory(offerer=offerer, user=user)

    # When
    maybe_send_offerer_validation_email(offerer, user_offerer)

    # Then
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["To"] == "administration@example.com"


@pytest.mark.usefixtures("db_session")
def test_maybe_send_offerer_validation_email_does_not_send_email_if_all_validated(app):
    # Given
    user = users_factories.UserFactory()
    offerer = OffererFactory()
    user_offerer = UserOffererFactory(offerer=offerer, user=user)

    # When
    maybe_send_offerer_validation_email(offerer, user_offerer)

    # Then
    assert not mails_testing.outbox


def test_send_payment_details_email_sends_email_to_pass_culture(app):
    # Given
    csv = '"header A","header B","header C","header D"\n"part A","part B","part C","part D"\n'
    recipients = ["comptable1@culture.fr", "comptable2@culture.fr"]

    # When
    send_payment_details_email(csv, recipients)

    # Then
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["To"] == "comptable1@culture.fr, comptable2@culture.fr"


def test_send_wallet_balances_email_sends_email_to_recipients(app):
    # Given
    csv = '"header A","header B","header C","header D"\n"part A","part B","part C","part D"\n'
    recipients = ["comptable1@culture.fr", "comptable2@culture.fr"]

    # When
    send_wallet_balances_email(csv, recipients)

    # Then
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["To"] == "comptable1@culture.fr, comptable2@culture.fr"


def test_send_payments_report_email_sends_email_to_recipients(app):
    # Given
    not_processable_csv = '"header A","header B","header C","header D"\n"part A","part B","part C","part D"\n'
    n_payments_by_status = {"ERROR": 1, "PENDING": 2}

    # When
    send_payments_report_emails(not_processable_csv, n_payments_by_status, ["recipient@example.com"])

    # Then
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["To"] == "recipient@example.com"


@pytest.mark.usefixtures("db_session")
class SendOfferCreationNotificationToAdministrationTest:
    def test_when_mailjet_status_code_200_sends_email_to_administration_email(self, app):
        author = users_factories.UserFactory()
        offer = OfferFactory(author=author)

        # When
        send_offer_creation_notification_to_administration(offer)

        # Then
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["To"] == "administration@example.com"


@pytest.mark.usefixtures("db_session")
class SendOfferCreationRefusalNotificationToAdministrationTest:
    def test_when_mailjet_status_code_200_sends_email_to_administration_email(self, app):
        author = users_factories.UserFactory(email="author@email.com")
        offer = OfferFactory(author=author)

        # When
        send_offer_rejection_notification_to_administration(offer)

        # Then
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["To"] == "administration@example.com"


@pytest.mark.usefixtures("db_session")
class SendOfferNotificationToAdministrationTest:
    def test_send_refusal_notification(self, app):
        author = users_factories.UserFactory(email="author@email.com")
        offer = OfferFactory(name="Test Book", author=author)

        # When
        send_offer_validation_notification_to_administration(OfferValidationStatus.REJECTED, offer)

        # Then
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["To"] == "administration@example.com"
        assert mails_testing.outbox[0].sent_data["Subject"] == "[Création d’offre : refus - 75] Test Book"

    def test_send_approval_notification(self, app):
        author = users_factories.UserFactory(email="author@email.com")
        offer = OfferFactory(name="Test Book", author=author)

        # When
        send_offer_validation_notification_to_administration(OfferValidationStatus.APPROVED, offer)

        # Then
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["To"] == "administration@example.com"
        assert mails_testing.outbox[0].sent_data["Subject"] == "[Création d’offre - 75] Test Book"
