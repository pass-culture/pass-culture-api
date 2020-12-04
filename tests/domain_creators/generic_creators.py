from datetime import datetime
from typing import Optional

from pcapi.core.bookings.api import compute_confirmation_date
from pcapi.core.offers.models import Mediation
from pcapi.domain.beneficiary.beneficiary import Beneficiary
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.domain.booking_recap.booking_recap import BookBookingRecap
from pcapi.domain.booking_recap.booking_recap import EventBookingRecap
from pcapi.domain.booking_recap.booking_recap import ThingBookingRecap
from pcapi.domain.favorite.favorite import Favorite
from pcapi.models import Offer


def create_domain_beneficiary(
    identifier: int = None,
    email: str = "john.doe@example.com",
    first_name: str = None,
    last_name: str = None,
    department_code: str = "93",
    is_beneficiary: bool = True,
    wallet_balance: int = None,
    reset_password_token: str = "",
) -> Beneficiary:
    user = Beneficiary(
        identifier=identifier,
        is_beneficiary=is_beneficiary,
        email=email,
        first_name=first_name,
        last_name=last_name,
        department_code=department_code,
        wallet_balance=wallet_balance,
        reset_password_token=reset_password_token,
    )

    return user


def create_domain_beneficiary_pre_subcription(
    date_of_birth: datetime = datetime(1995, 2, 5),
    activity: str = "Apprenti",
    address: str = "3 rue de Valois",
    application_id: str = "12",
    city: str = "Paris",
    postal_code: str = "35123",
    email: str = "rennes@example.org",
    first_name: str = "Thomas",
    civility: str = "Mme",
    last_name: str = "DURAND",
    phone_number: str = "0123456789",
    source: str = "jouve",
    source_id: str = None,
) -> BeneficiaryPreSubscription:
    return BeneficiaryPreSubscription(
        address=address,
        activity=activity,
        application_id=application_id,
        city=city,
        date_of_birth=date_of_birth,
        postal_code=postal_code,
        email=email,
        first_name=first_name,
        civility=civility,
        last_name=last_name,
        phone_number=phone_number,
        source=source,
        source_id=source_id,
    )


def create_domain_thing_booking_recap(
    offer_identifier: int = 1,
    offer_name: str = "Le livre de la jungle",
    offerer_name: str = "Libraire de Caen",
    offer_isbn: str = None,
    beneficiary_lastname: str = "Sans Nom",
    beneficiary_firstname: str = "Mowgli",
    beneficiary_email: str = "mowgli@example.com",
    booking_amount: float = 0,
    booking_token: str = "JUNGLE",
    booking_date: datetime = datetime(2020, 3, 14, 19, 5, 3, 0),
    booking_is_duo: bool = False,
    booking_is_used: bool = False,
    booking_is_cancelled: bool = False,
    booking_is_reimbursed: bool = False,
    booking_is_confirmed: bool = False,
    payment_date: Optional[datetime] = None,
    cancellation_date: Optional[datetime] = None,
    date_used: Optional[datetime] = None,
    venue_identifier: int = 1,
    venue_name="Librairie Kléber",
    venue_is_virtual=False,
) -> ThingBookingRecap:
    if offer_isbn:
        return BookBookingRecap(
            offer_identifier=offer_identifier,
            offer_name=offer_name,
            offerer_name=offerer_name,
            offer_isbn=offer_isbn,
            beneficiary_lastname=beneficiary_lastname,
            beneficiary_firstname=beneficiary_firstname,
            beneficiary_email=beneficiary_email,
            booking_amount=booking_amount,
            booking_token=booking_token,
            booking_date=booking_date,
            booking_is_duo=booking_is_duo,
            booking_is_used=booking_is_used,
            booking_is_cancelled=booking_is_cancelled,
            booking_is_reimbursed=booking_is_reimbursed,
            booking_is_confirmed=booking_is_confirmed,
            payment_date=payment_date,
            cancellation_date=cancellation_date,
            confirmation_date=None,
            date_used=date_used,
            venue_identifier=venue_identifier,
            venue_name=venue_name,
            venue_is_virtual=venue_is_virtual,
        )
    return ThingBookingRecap(
        offer_identifier=offer_identifier,
        offer_name=offer_name,
        offerer_name=offerer_name,
        beneficiary_lastname=beneficiary_lastname,
        beneficiary_firstname=beneficiary_firstname,
        beneficiary_email=beneficiary_email,
        booking_amount=booking_amount,
        booking_token=booking_token,
        booking_date=booking_date,
        booking_is_duo=booking_is_duo,
        booking_is_used=booking_is_used,
        booking_is_cancelled=booking_is_cancelled,
        booking_is_reimbursed=booking_is_reimbursed,
        booking_is_confirmed=booking_is_confirmed,
        payment_date=payment_date,
        cancellation_date=cancellation_date,
        confirmation_date=None,
        date_used=date_used,
        venue_identifier=venue_identifier,
        venue_name=venue_name,
        venue_is_virtual=venue_is_virtual,
    )


def create_domain_event_booking_recap(
    payment_date: Optional[datetime] = None,
    cancellation_date: Optional[datetime] = None,
    date_used: Optional[datetime] = None,
    offer_identifier: int = 1,
    offer_name: str = "Le cirque du Soleil",
    offerer_name="Libraire de Caen",
    beneficiary_lastname: str = "Doe",
    beneficiary_firstname: str = "Jane",
    beneficiary_email: str = "jane.doe@example.com",
    booking_amount: float = 0,
    booking_token: str = "CIRQUE",
    booking_date: datetime = datetime(2020, 3, 14, 19, 5, 3, 0),
    booking_is_duo: bool = False,
    booking_is_used: bool = False,
    booking_is_cancelled: bool = False,
    booking_is_reimbursed: bool = False,
    booking_is_confirmed: bool = False,
    event_beginning_datetime: datetime = datetime(2020, 5, 26, 20, 30, 0, 0),
    venue_identifier: int = 1,
    venue_name="Librairie Kléber",
    venue_is_virtual=False,
) -> EventBookingRecap:
    return EventBookingRecap(
        offer_identifier=offer_identifier,
        offer_name=offer_name,
        offerer_name=offerer_name,
        beneficiary_lastname=beneficiary_lastname,
        beneficiary_firstname=beneficiary_firstname,
        beneficiary_email=beneficiary_email,
        booking_amount=booking_amount,
        booking_token=booking_token,
        booking_date=booking_date,
        booking_is_duo=booking_is_duo,
        booking_is_used=booking_is_used,
        booking_is_cancelled=booking_is_cancelled,
        booking_is_confirmed=booking_is_confirmed,
        booking_is_reimbursed=booking_is_reimbursed,
        event_beginning_datetime=event_beginning_datetime,
        venue_identifier=venue_identifier,
        cancellation_date=cancellation_date,
        confirmation_date=compute_confirmation_date(event_beginning_datetime, booking_date),
        payment_date=payment_date,
        date_used=date_used,
        venue_name=venue_name,
        venue_is_virtual=venue_is_virtual,
    )


def create_domain_favorite(identifier: int, offer: Offer, mediation: Mediation = None, booking: dict = None):
    return Favorite(identifier=identifier, offer=offer, mediation=mediation, booking=booking)
