from datetime import timedelta, datetime

from models.payment import Payment
from models.payment_status import TransactionStatus, PaymentStatus
from repository import repository
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_payment, create_user, create_booking, \
    create_deposit, create_payment_message, create_payment_status


class SetStatusTest:
    def test_appends_a_status_to_a_new_payment(self):
        # given
        one_second = timedelta(seconds=1)
        now = datetime.utcnow()
        payment = Payment()

        # when
        payment.setStatus(TransactionStatus.PENDING)

        # then
        assert len(payment.statuses) == 1
        assert payment.statuses[0].status == TransactionStatus.PENDING
        assert payment.statuses[0].detail is None
        assert now - one_second < payment.statuses[0].date < now + one_second

    def test_appends_a_status_to_a_payment_with_existing_status(self):
        # given
        one_second = timedelta(seconds=1)
        now = datetime.utcnow()
        payment = Payment()
        payment_status = PaymentStatus()
        payment_status.status = TransactionStatus.PENDING
        payment_status.date = datetime.utcnow()
        payment.statuses = [payment_status]

        # when
        payment.setStatus(TransactionStatus.SENT)

        # then
        assert len(payment.statuses) == 2
        assert payment.statuses[1].status == TransactionStatus.SENT
        assert payment.statuses[1].detail is None
        assert now - one_second < payment.statuses[1].date < now + one_second


class PaymentDateTest:
    class InPythonContextTest:
        def test_payment_date_should_return_payment_date_for_status_sent(self):
            # Given
            payment_date = datetime.utcnow()
            payment = Payment()
            payment_status = PaymentStatus()
            payment_status.status = TransactionStatus.SENT
            payment_status.date = payment_date
            payment.statuses = [payment_status]

            # When/Then
            payment_sent_date = payment.lastProcessedDate
            assert payment_sent_date == payment_date

        def test_payment_date_should_return_no_payment_date_for_status_pending(self):
            # Given
            payment_date = datetime.utcnow()
            payment = Payment()
            payment_status = PaymentStatus()
            payment_status.status = TransactionStatus.PENDING
            payment_status.date = payment_date
            payment.statuses = [payment_status]

            # When/Then
            payment_sent_date = payment.lastProcessedDate
            assert payment_sent_date is None

    class InSQLContextTest:
        @clean_database
        def test_payment_date_should_return_payment_date_for_status_sent(self, app):
            # Given
            user = create_user()
            booking = create_booking(user=user)
            today = datetime.utcnow()
            create_deposit(user)
            offerer = booking.stock.offer.venue.managingOfferer
            payment_message = create_payment_message(name='mon message')
            payment = create_payment(booking, offerer, 5,  payment_message=payment_message)
            payment_status = create_payment_status(payment, status=TransactionStatus.SENT, date=today)

            repository.save(payment_status)

            # When
            payment_from_query = Payment.query.with_entities(
                Payment.lastProcessedDate.label("payment_date")
            ).first()

            # Then
            assert payment_from_query.payment_date == today

        @clean_database
        def test_payment_date_should_return_no_payment_date_for_status_pending(self, app):
            # Given
            user = create_user()
            booking = create_booking(user=user)
            today = datetime.utcnow()
            create_deposit(user)
            offerer = booking.stock.offer.venue.managingOfferer
            payment_message = create_payment_message(name='mon message')
            payment = create_payment(booking, offerer, 5,  payment_message=payment_message)
            payment_status = create_payment_status(payment, status=TransactionStatus.PENDING, date=today)

            repository.save(payment_status)

            # When
            payment_from_query = Payment.query.with_entities(
                Payment.lastProcessedDate.label("payment_date")
            ).first()

            # Then
            assert payment_from_query.payment_date is None
