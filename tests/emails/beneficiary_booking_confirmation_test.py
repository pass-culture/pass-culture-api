from datetime import datetime
from datetime import timezone

import pytest

from pcapi import models
import pcapi.core.bookings.factories as bookings_factories
import pcapi.core.offers.factories as offers_factories
from pcapi.core.testing import override_features
from pcapi.emails.beneficiary_booking_confirmation import retrieve_data_for_beneficiary_booking_confirmation_email
from pcapi.utils.human_ids import humanize


def make_booking(**kwargs):
    attributes = dict(
        dateCreated=datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc),
        token="ABC123",
        user__firstName="Joe",
        stock__beginningDatetime=datetime(2019, 11, 6, 14, 59, 5, tzinfo=timezone.utc),
        stock__price=23.99,
        stock__offer__name="Super événement",
        stock__offer__product__type=str(models.EventType.SPECTACLE_VIVANT),
        stock__offer__venue__name="Lieu de l'offreur",
        stock__offer__venue__address="25 avenue du lieu",
        stock__offer__venue__postalCode="75010",
        stock__offer__venue__city="Paris",
        stock__offer__venue__managingOfferer__name="Théâtre du coin",
    )
    attributes.update(kwargs)
    return bookings_factories.BookingFactory(**attributes)


def get_expected_base_email_data(booking, mediation, **overrides):
    email_data = {
        "MJ-TemplateID": 2841128,
        "MJ-TemplateLanguage": True,
        "Vars": {
            "user_first_name": "Joe",
            "booking_date": "3 octobre 2019",
            "booking_hour": "15h24",
            "offer_name": "Super événement",
            "offerer_name": "Théâtre du coin",
            "event_date": "6 novembre 2019",
            "event_hour": "15h59",
            "offer_price": "23.99",
            "offer_token": "ABC123",
            "venue_name": "Lieu de l'offreur",
            "venue_address": "25 avenue du lieu",
            "venue_postal_code": "75010",
            "venue_city": "Paris",
            "all_but_not_virtual_thing": 1,
            "all_things_not_virtual_thing": 0,
            "is_event": 1,
            "is_single_event": 1,
            "is_duo_event": 0,
            "can_expire": 0,
            "offer_id": humanize(booking.stock.offer.id),
            "mediation_id": humanize(mediation.id),
            "code_expiration_date": None,
            "has_expiration_date": 0,
        },
    }
    email_data["Vars"].update(overrides)
    return email_data


@pytest.mark.usefixtures("db_session")
def test_should_return_event_specific_data_for_email_when_offer_is_an_event():
    booking = make_booking()
    mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

    expected = get_expected_base_email_data(booking, mediation)
    assert email_data == expected


@pytest.mark.usefixtures("db_session")
def test_should_return_event_specific_data_for_email_when_offer_is_a_duo_event():
    booking = make_booking(quantity=2)
    mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

    expected = get_expected_base_email_data(
        booking,
        mediation,
        is_duo_event=1,
        is_single_event=0,
        offer_price="47.98",
    )
    assert email_data == expected


@pytest.mark.usefixtures("db_session")
def test_should_return_thing_specific_data_for_email_when_offer_is_a_thing():
    booking = make_booking(
        stock__offer__product__type=str(models.ThingType.AUDIOVISUEL),
        stock__offer__name="Super bien culturel",
    )
    mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

    expected = get_expected_base_email_data(
        booking,
        mediation,
        all_things_not_virtual_thing=1,
        event_date="",
        event_hour="",
        is_event=0,
        is_single_event=0,
        offer_name="Super bien culturel",
        can_expire=1,
    )
    assert email_data == expected


class DigitalOffersTest:
    @pytest.mark.usefixtures("db_session")
    def test_should_return_digital_thing_specific_data_for_email_when_offer_is_a_digital_thing(self):
        booking = make_booking(
            quantity=10,
            stock__price=0,
            stock__offer__product__type=str(models.ThingType.AUDIOVISUEL),
            stock__offer__product__url="http://example.com",
            stock__offer__name="Super offre numérique",
        )
        mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

        email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

        expected = get_expected_base_email_data(
            booking,
            mediation,
            all_but_not_virtual_thing=0,
            all_things_not_virtual_thing=0,
            event_date="",
            event_hour="",
            is_event=0,
            is_single_event=0,
            offer_name="Super offre numérique",
            offer_price="Gratuit",
            can_expire=1,
        )
        assert email_data == expected

    @override_features(AUTO_ACTIVATE_DIGITAL_BOOKINGS=True)
    @pytest.mark.usefixtures("db_session")
    def test_hide_cancellation_policy_when_auto_validation_activated(self):
        booking = make_booking(
            quantity=10,
            stock__price=0,
            stock__offer__product__type=str(models.ThingType.AUDIOVISUEL),
            stock__offer__product__url="http://example.com",
            stock__offer__name="Super offre numérique",
        )
        mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

        email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)
        expected = get_expected_base_email_data(
            booking,
            mediation,
            all_but_not_virtual_thing=0,
            all_things_not_virtual_thing=0,
            event_date="",
            event_hour="",
            is_event=0,
            is_single_event=0,
            offer_name="Super offre numérique",
            offer_price="Gratuit",
            can_expire=0,
        )

        assert email_data == expected


@pytest.mark.usefixtures("db_session")
def test_use_activation_code_instead_of_token_if_possible():
    booking = make_booking(
        quantity=10,
        stock__price=0,
        stock__offer__product__type=str(models.ThingType.AUDIOVISUEL),
        stock__offer__product__url="http://example.com",
        stock__offer__name="Super offre numérique",
    )
    offers_factories.ActivationCodeFactory(stock=booking.stock, booking=booking, code="code-5uzk15fbha4")
    mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

    expected = get_expected_base_email_data(
        booking,
        mediation,
        all_but_not_virtual_thing=0,
        all_things_not_virtual_thing=0,
        event_date="",
        event_hour="",
        is_event=0,
        is_single_event=0,
        offer_name="Super offre numérique",
        offer_price="Gratuit",
        can_expire=1,
        offer_token="code-5uzk15fbha4",
        code_expiration_date=None,
    )
    assert email_data == expected


@pytest.mark.usefixtures("db_session")
def test_add_expiration_date_from_activation_code():
    booking = make_booking(
        quantity=10,
        stock__price=0,
        stock__offer__product__type=str(models.ThingType.AUDIOVISUEL),
        stock__offer__product__url="http://example.com",
        stock__offer__name="Super offre numérique",
    )
    offers_factories.ActivationCodeFactory(
        stock=booking.stock, booking=booking, code="code-5uzk15fbha4", expirationDate=datetime(2030, 1, 1)
    )
    mediation = offers_factories.MediationFactory(offer=booking.stock.offer)

    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)

    expected = get_expected_base_email_data(
        booking,
        mediation,
        all_but_not_virtual_thing=0,
        all_things_not_virtual_thing=0,
        event_date="",
        event_hour="",
        is_event=0,
        is_single_event=0,
        offer_name="Super offre numérique",
        offer_price="Gratuit",
        can_expire=1,
        offer_token="code-5uzk15fbha4",
        has_expiration_date=1,
        code_expiration_date="1 janvier 2030",
    )
    assert email_data == expected


@pytest.mark.usefixtures("db_session")
def test_should_return_total_price_for_duo_offers():
    booking = bookings_factories.BookingFactory(quantity=2, stock__price=10)
    email_data = retrieve_data_for_beneficiary_booking_confirmation_email(booking)
    assert email_data["Vars"]["offer_price"] == "20.00"
