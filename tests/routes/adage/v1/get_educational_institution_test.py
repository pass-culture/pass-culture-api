import pytest

from pcapi import settings
from pcapi.core.bookings.factories import EducationalBookingFactory
from pcapi.core.educational.factories import EducationalDepositFactory
from pcapi.core.educational.factories import EducationalInstitutionFactory
from pcapi.core.educational.factories import EducationalYearFactory
from pcapi.core.users.factories import UserFactory
from pcapi.routes.native.v1.serialization.offers import get_serialized_offer_category
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


@pytest.mark.usefixtures("db_session")
class Returns200Test:
    def test_get_educational_institution(self, app) -> None:
        redactor = UserFactory(civility="M.")
        educational_year = EducationalYearFactory()
        educational_institution = EducationalInstitutionFactory()
        EducationalDepositFactory(
            educationalInstitution=educational_institution,
            educationalYear=educational_year,
            amount=2000,
            isFinal=True,
        )
        EducationalInstitutionFactory()
        booking = EducationalBookingFactory(
            user=redactor,
            educationalBooking__educationalYear=educational_year,
            educationalBooking__educationalInstitution=educational_institution,
        )
        other_educational_year = EducationalYearFactory(adageId="toto")
        other_educational_institution = EducationalInstitutionFactory(institutionId="tata")
        EducationalBookingFactory(educationalBooking__educationalYear=other_educational_year)
        EducationalBookingFactory(educationalBooking__educationalInstitution=other_educational_institution)
        EducationalDepositFactory(
            educationalInstitution=educational_institution,
            educationalYear=other_educational_year,
            amount=2000,
            isFinal=False,
        )
        EducationalDepositFactory(
            educationalInstitution=other_educational_institution,
            educationalYear=educational_year,
            amount=2000,
            isFinal=False,
        )

        client = TestClient(app.test_client()).with_eac_token()
        response = client.get(
            f"/adage/v1/years/{educational_year.adageId}/educational_institution/{educational_institution.institutionId}"
        )

        assert response.status_code == 200

        stock = booking.stock
        offer = stock.offer
        venue = offer.venue
        user = booking.user
        assert response.json == {
            "credit": 2000,
            "isFinal": True,
            "prebookings": [
                {
                    "address": venue.address,
                    "beginningDatetime": stock.beginningDatetime.isoformat(),
                    "cancellationDate": None,
                    "cancellationLimitDate": booking.cancellationLimitDate.isoformat(),
                    "category": get_serialized_offer_category(offer),
                    "city": venue.city,
                    "confirmationDate": booking.educationalBooking.confirmationDate.isoformat(),
                    "confirmationLimitDate": booking.educationalBooking.confirmationLimitDate.isoformat(),
                    "coordinates": {
                        "latitude": float(venue.latitude),
                        "longitude": float(venue.longitude),
                    },
                    "creationDate": booking.dateCreated.isoformat(),
                    "description": offer.description,
                    "durationMinutes": offer.durationMinutes,
                    "expirationDate": booking.expirationDate,
                    "id": booking.educationalBooking.id,
                    "image": {"url": offer.image.url, "credit": offer.image.credit} if offer.image else None,
                    "isDigital": offer.isDigital,
                    "venueName": venue.name,
                    "name": offer.name,
                    "postalCode": venue.postalCode,
                    "price": booking.amount,
                    "quantity": booking.quantity,
                    "redactor": {
                        "email": user.email,
                        "redactorFirstName": user.firstName,
                        "redactorLastName": user.lastName,
                        "redactorCivility": user.civility,
                    },
                    "UAICode": booking.educationalBooking.educationalInstitution.institutionId,
                    "yearId": int(booking.educationalBooking.educationalYearId),
                    "status": "CONFIRMED",
                    "venueTimezone": venue.timezone,
                    "totalAmount": booking.amount * booking.quantity,
                    "url": f"{settings.WEBAPP_URL}/accueil/details/{humanize(offer.id)}",
                    "withdrawalDetails": offer.withdrawalDetails,
                }
            ],
        }

    def test_get_educational_institution_without_deposit(self, app) -> None:
        educational_year = EducationalYearFactory()
        educational_institution = EducationalInstitutionFactory()

        client = TestClient(app.test_client()).with_eac_token()
        response = client.get(
            f"/adage/v1/years/{educational_year.adageId}/educational_institution/{educational_institution.institutionId}"
        )

        assert response.status_code == 200

        assert response.json == {
            "credit": 0,
            "isFinal": False,
            "prebookings": [],
        }


class Returns404Test:
    def test_get_educational_institution_not_found(self, app) -> None:
        educational_year = EducationalYearFactory()
        EducationalInstitutionFactory()

        client = TestClient(app.test_client()).with_eac_token()
        response = client.get(f"/adage/v1/years/{educational_year.adageId}/educational_institution/UNKNOWN")

        assert response.status_code == 404
