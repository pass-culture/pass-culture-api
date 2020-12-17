import pytest

from pcapi.core.bookings.factories import BookingFactory
from pcapi.core.users.factories import UserFactory
from pcapi.emails.beneficiary_soon_to_be_expired_bookings import (
    build_soon_to_be_expired_bookings_recap_email_data_for_beneficiary,
)


@pytest.mark.usefixtures("db_session")
class BuildSoonToBeExpiredBookingsRecapEmailDataForBeneficiaryTest:
    def test_build_soon_to_be_expired_bookings_data(self, app):
        # Given
        beneficiary = UserFactory(email="isasimov@example.com", firstName="ASIMOV", isBeneficiary=True, isAdmin=False)
        bookings = [
            BookingFactory(
                stock__offer__name="offre 1",
                stock__offer__venue__name="venue 1",
            ),
            BookingFactory(
                stock__offer__name="offre 2",
                stock__offer__venue__name="venue 2",
            ),
        ]

        # When
        data = build_soon_to_be_expired_bookings_recap_email_data_for_beneficiary(beneficiary, bookings)

        # Then
        assert data == {
            "FromEmail": "dev@example.com",
            "Mj-TemplateID": 1927224,
            "Mj-TemplateLanguage": True,
            "To": "dev@example.com",
            "Vars": {
                "user_firstName": "ASIMOV",
                "bookings": [
                    {"offer_name": "offre 1", "venue_name": "venue 1"},
                    {"offer_name": "offre 2", "venue_name": "venue 2"},
                ],
                "env": "-development",
            },
        }
