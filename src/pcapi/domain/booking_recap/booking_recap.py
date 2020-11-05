from datetime import datetime
from enum import Enum
from typing import Optional

from pcapi.domain.booking_recap.booking_recap_history import BookingRecapConfirmedHistory, BookingRecapHistory, BookingRecapValidatedHistory, \
    BookingRecapCancelledHistory, BookingRecapReimbursedHistory


class BookingRecapStatus(Enum):
    booked = 'booked'
    validated = 'validated'
    cancelled = 'cancelled'
    reimbursed = 'reimbursed'
    confirmed = 'confirmed'


class BookingRecap:
    def __init__(self,
                 beneficiary_lastname: str,
                 beneficiary_firstname: str,
                 beneficiary_email: str,
                 booking_token: str,
                 booking_date: datetime,
                 booking_is_duo: bool,
                 booking_is_used: bool,
                 booking_is_cancelled: bool,
                 booking_is_reimbursed: bool,
                 booking_is_confirmed: bool,
                 booking_amount: float,
                 cancellation_date: Optional[datetime],
                 confirmation_date: Optional[datetime],
                 payment_date: Optional[datetime],
                 date_used: Optional[datetime],
                 offer_identifier: int,
                 offer_name: str,
                 offerer_name: str,
                 venue_identifier: int,
                 venue_name: str,
                 venue_is_virtual: bool,
                 ):
        self.booking_amount = booking_amount
        self.beneficiary_lastname = beneficiary_lastname
        self.beneficiary_firstname = beneficiary_firstname
        self.beneficiary_email = beneficiary_email
        self.booking_token = booking_token
        self.booking_date = booking_date
        self.booking_is_duo = booking_is_duo
        self.booking_is_used = booking_is_used
        self.booking_is_cancelled = booking_is_cancelled
        self.booking_is_reimbursed = booking_is_reimbursed
        self.booking_is_confirmed = booking_is_confirmed
        self.offer_identifier = offer_identifier
        self.offer_name = offer_name
        self.offerer_name = offerer_name
        self.venue_identifier = venue_identifier
        self.booking_status_history = self.build_status_history(
            booking_date=booking_date,
            cancellation_date=cancellation_date,
            confirmation_date=confirmation_date,
            payment_date=payment_date,
            date_used=date_used)
        self.venue_name = venue_name
        self.venue_is_virtual = venue_is_virtual

    def __new__(cls, *args, **kwargs):
        if cls is BookingRecap:
            raise TypeError("BookingRecap may not be instantiated")
        return object.__new__(cls)

    @property
    def booking_token(self) -> str:
        return self._booking_token

    @booking_token.setter
    def booking_token(self, booking_token) -> str:
        self._booking_token = booking_token

    @property
    def booking_status(self) -> BookingRecapStatus:
        if self.booking_is_reimbursed:
            return BookingRecapStatus.reimbursed
        if self.booking_is_cancelled:
            return BookingRecapStatus.cancelled
        if self.booking_is_used:
            return BookingRecapStatus.validated
        if self.booking_is_confirmed:
            return BookingRecapStatus.confirmed
        else:
            return BookingRecapStatus.booked

    def build_status_history(self,
                             booking_date: datetime,
                             cancellation_date: datetime,
                             confirmation_date: datetime,
                             payment_date: datetime,
                             date_used: datetime) -> BookingRecapHistory:
        if self.booking_is_reimbursed:
            return BookingRecapReimbursedHistory(
                booking_date=booking_date,
                confirmation_date=confirmation_date,
                payment_date=payment_date,
                date_used=date_used
            )
        if self.booking_is_cancelled:
            return BookingRecapCancelledHistory(
                booking_date=booking_date,
                cancellation_date=cancellation_date
            )
        if self.booking_is_used:
            return BookingRecapValidatedHistory(
                booking_date=booking_date,
                confirmation_date=confirmation_date,
                date_used=date_used
            )
        if self.booking_is_confirmed:
            return BookingRecapConfirmedHistory(
                booking_date=booking_date,
                confirmation_date=confirmation_date,
            )
        else:
            return BookingRecapHistory(
                booking_date
            )


class ThingBookingRecap(BookingRecap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @BookingRecap.booking_token.getter
    def booking_token(self) -> Optional[str]:
        if not self.booking_is_used and not self.booking_is_cancelled:
            return None
        else:
            return self._booking_token


class EventBookingRecap(BookingRecap):
    def __init__(self, event_beginning_datetime: datetime, **kwargs):
        super().__init__(**kwargs)
        self.event_beginning_datetime = event_beginning_datetime


class BookBookingRecap(ThingBookingRecap):
    def __init__(self, offer_isbn: str, **kwargs):
        super().__init__(**kwargs)
        self.offer_isbn = offer_isbn
