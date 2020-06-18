from datetime import datetime
from typing import List, Optional

from domain.beneficiary.beneficiary import Beneficiary
from domain.booking.booking import Booking
from domain.booking_recap.booking_recap import ThingBookingRecap, EventBookingRecap, BookBookingRecap
from domain.stock.stock import Stock
from models import Offer


def create_domain_beneficiary(identifier: int = None,
                              email: str = 'john.doe@example.com',
                              first_name: str = None,
                              last_name: str = None,
                              department_code: str = '93',
                              can_book_free_offers: bool = True,
                              wallet_balance: int = None) -> Beneficiary:
    user = Beneficiary(identifier=identifier,
                       can_book_free_offers=can_book_free_offers,
                       email=email,
                       first_name=first_name,
                       last_name=last_name,
                       department_code=department_code,
                       wallet_balance=wallet_balance)

    return user


def create_domain_thing_booking_recap(offer_name: str = "Le livre de la jungle",
                                      offer_isbn: str = None,
                                      beneficiary_lastname: str = "Sans Nom",
                                      beneficiary_firstname: str = "Mowgli",
                                      beneficiary_email: str = "mowgli@example.com",
                                      booking_token: str = "JUNGLE",
                                      booking_date: datetime = datetime(2020, 3, 14, 19, 5, 3, 0),
                                      booking_is_duo: bool = False,
                                      booking_is_used: bool = False,
                                      booking_is_cancelled: bool = False,
                                      booking_is_reimbursed: bool = False,
                                      venue_identifier: str = 'AE') -> ThingBookingRecap:
    if offer_isbn:
        return BookBookingRecap(
            offer_name=offer_name,
            offer_isbn=offer_isbn,
            beneficiary_lastname=beneficiary_lastname,
            beneficiary_firstname=beneficiary_firstname,
            beneficiary_email=beneficiary_email,
            booking_token=booking_token,
            booking_date=booking_date,
            booking_is_duo=booking_is_duo,
            booking_is_used=booking_is_used,
            booking_is_cancelled=booking_is_cancelled,
            booking_is_reimbursed=booking_is_reimbursed,
            venue_identifier=venue_identifier,
        )
    return ThingBookingRecap(
        offer_name=offer_name,
        beneficiary_lastname=beneficiary_lastname,
        beneficiary_firstname=beneficiary_firstname,
        beneficiary_email=beneficiary_email,
        booking_token=booking_token,
        booking_date=booking_date,
        booking_is_duo=booking_is_duo,
        booking_is_used=booking_is_used,
        booking_is_cancelled=booking_is_cancelled,
        booking_is_reimbursed=booking_is_reimbursed,
        venue_identifier=venue_identifier,
    )


def create_domain_event_booking_recap(offer_name: str = "Le cirque du Soleil",
                                      beneficiary_lastname: str = "Doe",
                                      beneficiary_firstname: str = "Jane",
                                      beneficiary_email: str = "jane.doe@example.com",
                                      booking_token: str = "CIRQUE",
                                      booking_date: datetime = datetime(2020, 3, 14, 19, 5, 3, 0),
                                      booking_is_duo: bool = False,
                                      booking_is_used: bool = False,
                                      booking_is_cancelled: bool = False,
                                      booking_is_reimbursed: bool = False,
                                      event_beginning_datetime: datetime = datetime(2020, 5, 26, 20, 30, 0, 0),
                                      venue_identifier: str = 'AE') -> EventBookingRecap:
    return EventBookingRecap(
        offer_name=offer_name,
        beneficiary_lastname=beneficiary_lastname,
        beneficiary_firstname=beneficiary_firstname,
        beneficiary_email=beneficiary_email,
        booking_token=booking_token,
        booking_date=booking_date,
        booking_is_duo=booking_is_duo,
        booking_is_used=booking_is_used,
        booking_is_cancelled=booking_is_cancelled,
        booking_is_reimbursed=booking_is_reimbursed,
        event_beginning_datetime=event_beginning_datetime,
        venue_identifier=venue_identifier,
    )


def create_domain_stock(identifier: int,
                        quantity: Optional[int],
                        offer: Offer,
                        price: float,
                        beginning_datetime: Optional[datetime],
                        booking_limit_datetime: Optional[datetime],
                        is_soft_deleted: bool,
                        bookings: List[Booking] = []):
    return Stock(
        identifier=identifier,
        quantity=quantity,
        offer=offer,
        price=price,
        beginning_datetime=beginning_datetime,
        booking_limit_datetime=booking_limit_datetime,
        is_soft_deleted=is_soft_deleted,
        bookings=bookings,
    )
