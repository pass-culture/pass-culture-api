import datetime
from decimal import Decimal

import pytest

from pcapi.core.bookings import factories
from pcapi.core.bookings import models
import pcapi.core.recommendations.factories as recommendations_factories
import pcapi.core.users.factories as users_factories
from pcapi.models import ApiErrors
from pcapi.models import EventType
from pcapi.models import ThingType
from pcapi.models import db
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize


@pytest.mark.usefixtures("db_session")
def test_total_amount():
    booking = factories.BookingFactory(amount=1.2, quantity=2)
    assert booking.total_amount == Decimal("2.4")


@pytest.mark.usefixtures("db_session")
def test_save_cancellation_date_postgresql_function():
    # In this test, we manually COMMIT so that save_cancellation_date
    # PotsgreSQL function is triggered.
    booking = factories.BookingFactory()
    assert booking.cancellationDate is None

    booking.isCancelled = True
    db.session.commit()
    assert booking.cancellationDate is not None

    # Don't change cancellationDate when another attribute is updated.
    previous = booking.cancellationDate
    booking.isUsed = True
    db.session.commit()
    assert booking.cancellationDate == previous

    booking.isCancelled = False
    db.session.commit()
    assert booking.cancellationDate is None


@pytest.mark.usefixtures("db_session")
def test_booking_completed_url_gets_normalized():
    booking = factories.BookingFactory(
        token="ABCDEF",
        user__email="1@example.com",
        stock__offer__url="example.com?token={token}&email={email}",
    )
    assert booking.completedUrl == "http://example.com?token=ABCDEF&email=1@example.com"


@pytest.mark.usefixtures("db_session")
def test_too_many_bookings_postgresql_exception():
    booking1 = factories.BookingFactory(stock__quantity=1)
    with db.session.no_autoflush:
        booking2 = models.Booking()
        booking2.user = users_factories.UserFactory()
        booking2.stock = booking1.stock
        booking2.quantity = 1
        booking2.amount = booking1.stock.price
        booking2.token = "123456"
        with pytest.raises(ApiErrors) as exc:
            repository.save(booking2)
        assert exc.value.errors["global"] == ["La quantité disponible pour cette offre est atteinte."]


@pytest.mark.usefixtures("db_session")
class BookingThumbUrlTest:
    def test_thumb_url_use_mediation_if_exists(self):
        recommendation = recommendations_factories.RecommendationFactory(
            mediation__thumbCount=1,
        )
        booking = factories.BookingFactory(
            recommendation=recommendation,
            stock__offer=recommendation.offer,
        )
        mediation_id = humanize(recommendation.mediation.id)
        assert booking.thumbUrl == f"http://localhost/storage/thumbs/mediations/{mediation_id}"

    def test_thumb_url_use_product_if_no_mediation(self):
        booking = factories.BookingFactory(stock__offer__product__thumbCount=1)
        product_id = humanize(booking.stock.offer.product.id)
        assert booking.thumbUrl == f"http://localhost/storage/thumbs/products/{product_id}"

    def test_no_thumb_if_no_mediation_and_product_thumb_count_is_zero(self):
        booking = factories.BookingFactory(stock__offer__product__thumbCount=0)
        assert booking.thumbUrl is None

    def test_no_thumb_if_mediation_thumb_count_is_zero(self):
        recommendation = recommendations_factories.RecommendationFactory(
            mediation__thumbCount=0,
        )
        booking = factories.BookingFactory(
            recommendation=recommendation,
            stock__offer=recommendation.offer,
        )
        assert booking.thumbUrl is None


@pytest.mark.usefixtures("db_session")
class BookingQrCodeTest:
    def test_event_return_qr_code_if_event_is_not_expired_nor_cancelled(self):
        booking = factories.BookingFactory(
            stock__offer__product__type=str(EventType.CINEMA),
        )
        assert isinstance(booking.qrCode, str)

    def test_event_return_none_if_event_is_expired(self):
        booking = factories.BookingFactory(
            stock__offer__type=str(EventType.CINEMA),
            stock__beginningDatetime=datetime.datetime.now() - datetime.timedelta(days=1),
        )
        assert booking.qrCode is None

    def test_event_return_none_if_booking_is_cancelled(self):
        booking = factories.BookingFactory(
            isCancelled=True,
            stock__offer__type=str(EventType.CINEMA),
        )
        assert booking.qrCode is None

    def test_thing_return_qr_code_if_not_used_nor_cancelled(self):
        booking = factories.BookingFactory(
            stock__offer__product__type=str(ThingType.JEUX),
        )
        assert isinstance(booking.qrCode, str)

    def test_thing_return_none_if_booking_is_used(self):
        booking = factories.BookingFactory(
            isUsed=True,
            stock__offer__product__type=str(ThingType.JEUX),
        )
        assert booking.qrCode is None

    def test_thing_return_none_if_booking_is_cancelled(self):
        booking = factories.BookingFactory(
            isCancelled=True,
            stock__offer__product__type=str(ThingType.JEUX),
        )
        assert booking.qrCode is None
