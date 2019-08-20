from models import PcObject
from models.feature import FeatureToggle
from models.payment import Payment
from scripts.payment.batch_steps import generate_new_payments
from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_venue, create_offer_with_thing_product, create_stock_from_offer, \
    create_booking, create_user, create_deposit, create_payment, create_bank_information, deactivate_feature


class GenerateNewPaymentsTest:
    class WithCurrentRulesTest:
        @clean_database
        def test_records_new_payment_lines_in_database(self, app):
            # Given
            deactivate_feature(FeatureToggle.DEGRESSIVE_REIMBURSEMENT_RATE)
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            paying_stock = create_stock_from_offer(offer)
            free_stock = create_stock_from_offer(offer, price=0)
            user = create_user()
            deposit = create_deposit(user, amount=500)
            booking1 = create_booking(user, paying_stock, venue, is_used=True)
            booking2 = create_booking(user, paying_stock, venue, is_used=True)
            booking3 = create_booking(user, paying_stock, venue, is_used=True)
            booking4 = create_booking(user, free_stock, venue, is_used=True)
            payment1 = create_payment(booking2, offerer, 10, payment_message_name="ABCD123")

            PcObject.save(payment1)
            PcObject.save(deposit, booking1, booking3, booking4)

            initial_payment_count = Payment.query.count()

            # When
            generate_new_payments()

            # Then
            assert Payment.query.count() - initial_payment_count == 2

        @clean_database
        def test_returns_a_tuple_of_pending_and_not_processable_payments(self, app):
            # Given
            deactivate_feature(FeatureToggle.DEGRESSIVE_REIMBURSEMENT_RATE)
            offerer1 = create_offerer(siren='123456789')
            offerer2 = create_offerer(siren='987654321')
            PcObject.save(offerer1)
            bank_information = create_bank_information(bic='BDFEFR2LCCB', iban='FR7630006000011234567890189',
                                                       id_at_providers='123456789', offerer=offerer1)
            venue1 = create_venue(offerer1, siret='12345678912345')
            venue2 = create_venue(offerer2, siret='98765432154321')
            offer1 = create_offer_with_thing_product(venue1)
            offer2 = create_offer_with_thing_product(venue2)
            paying_stock1 = create_stock_from_offer(offer1)
            paying_stock2 = create_stock_from_offer(offer2)
            free_stock1 = create_stock_from_offer(offer1, price=0)
            user = create_user()
            deposit = create_deposit(user, amount=500)
            booking1 = create_booking(user, paying_stock1, venue1, is_used=True)
            booking2 = create_booking(user, paying_stock1, venue1, is_used=True)
            booking3 = create_booking(user, paying_stock2, venue2, is_used=True)
            booking4 = create_booking(user, free_stock1, venue1, is_used=True)
            PcObject.save(deposit, booking1, booking2, booking3, booking4, bank_information)

            # When
            pending, not_processable = generate_new_payments()

            # Then
            assert len(pending) == 2
            assert len(not_processable) == 1

        @clean_database
        def test_should_not_reimburse_offerer_if_he_has_more_than_20000_euros_in_bookings_on_several_venues(self, app):
            # Given
            deactivate_feature(FeatureToggle.DEGRESSIVE_REIMBURSEMENT_RATE)
            offerer1 = create_offerer(siren='123456789')
            PcObject.save(offerer1)
            bank_information = create_bank_information(bic='BDFEFR2LCCB', iban='FR7630006000011234567890189',
                                                       id_at_providers='123456789', offerer=offerer1)
            venue1 = create_venue(offerer1, siret='12345678912345')
            venue2 = create_venue(offerer1, siret='98765432154321')
            venue3 = create_venue(offerer1, siret='98123432154321')
            offer1 = create_offer_with_thing_product(venue1)
            offer2 = create_offer_with_thing_product(venue2)
            offer3 = create_offer_with_thing_product(venue3)
            paying_stock1 = create_stock_from_offer(offer1, price=10000)
            paying_stock2 = create_stock_from_offer(offer2, price=10000)
            paying_stock3 = create_stock_from_offer(offer3, price=10000)
            user = create_user()
            deposit = create_deposit(user, amount=50000)
            booking1 = create_booking(user, paying_stock1, venue1, quantity=1, is_used=True)
            booking2 = create_booking(user, paying_stock2, venue2, quantity=1, is_used=True)
            booking3 = create_booking(user, paying_stock3, venue3, quantity=1, is_used=True)
            PcObject.save(deposit, booking1, booking2, booking3, bank_information)

            # When
            pending, not_processable = generate_new_payments()

            # Then
            assert len(pending) == 2
            assert len(not_processable) == 0
            assert sum(p.amount for p in pending) == 20000

    class WithNewRulesTest:
        @clean_database
        def test_records_new_payment_lines_in_database(self, app):
            # Given
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            paying_stock = create_stock_from_offer(offer)
            free_stock = create_stock_from_offer(offer, price=0)
            user = create_user()
            deposit = create_deposit(user, amount=500)
            booking1 = create_booking(user, paying_stock, venue, is_used=True)
            booking2 = create_booking(user, paying_stock, venue, is_used=True)
            booking3 = create_booking(user, paying_stock, venue, is_used=True)
            booking4 = create_booking(user, free_stock, venue, is_used=True)
            payment1 = create_payment(booking2, offerer, 10, payment_message_name="ABCD123")

            PcObject.save(payment1)
            PcObject.save(deposit, booking1, booking3, booking4)

            initial_payment_count = Payment.query.count()

            # When
            generate_new_payments()

            # Then
            assert Payment.query.count() - initial_payment_count == 2

        @clean_database
        def test_returns_a_tuple_of_pending_and_not_processable_payments(self, app):
            # Given
            offerer1 = create_offerer(siren='123456789')
            offerer2 = create_offerer(siren='987654321')
            PcObject.save(offerer1)
            bank_information = create_bank_information(bic='BDFEFR2LCCB', iban='FR7630006000011234567890189',
                                                       id_at_providers='123456789', offerer=offerer1)
            venue1 = create_venue(offerer1, siret='12345678912345')
            venue2 = create_venue(offerer2, siret='98765432154321')
            offer1 = create_offer_with_thing_product(venue1)
            offer2 = create_offer_with_thing_product(venue2)
            paying_stock1 = create_stock_from_offer(offer1)
            paying_stock2 = create_stock_from_offer(offer2)
            free_stock1 = create_stock_from_offer(offer1, price=0)
            user = create_user()
            deposit = create_deposit(user, amount=500)
            booking1 = create_booking(user, paying_stock1, venue1, is_used=True)
            booking2 = create_booking(user, paying_stock1, venue1, is_used=True)
            booking3 = create_booking(user, paying_stock2, venue2, is_used=True)
            booking4 = create_booking(user, free_stock1, venue1, is_used=True)
            PcObject.save(deposit, booking1, booking2, booking3, booking4, bank_information)

            # When
            pending, not_processable = generate_new_payments()

            # Then
            assert len(pending) == 2
            assert len(not_processable) == 1

        @clean_database
        def test_reimburses_offerer_if_he_has_more_than_20000_euros_in_bookings_on_several_venues(self, app):
            # Given
            offerer1 = create_offerer(siren='123456789')
            PcObject.save(offerer1)
            bank_information = create_bank_information(bic='BDFEFR2LCCB', iban='FR7630006000011234567890189',
                                                       id_at_providers='123456789', offerer=offerer1)
            venue1 = create_venue(offerer1, siret='12345678912345')
            venue2 = create_venue(offerer1, siret='98765432154321')
            venue3 = create_venue(offerer1, siret='98123432154321')
            offer1 = create_offer_with_thing_product(venue1)
            offer2 = create_offer_with_thing_product(venue2)
            offer3 = create_offer_with_thing_product(venue3)
            paying_stock1 = create_stock_from_offer(offer1, price=10000)
            paying_stock2 = create_stock_from_offer(offer2, price=10000)
            paying_stock3 = create_stock_from_offer(offer3, price=10000)
            user = create_user()
            deposit = create_deposit(user, amount=50000)
            booking1 = create_booking(user, paying_stock1, venue1, quantity=1, is_used=True)
            booking2 = create_booking(user, paying_stock2, venue2, quantity=1, is_used=True)
            booking3 = create_booking(user, paying_stock3, venue3, quantity=1, is_used=True)
            PcObject.save(deposit, booking1, booking2, booking3, bank_information)

            # When
            pending, not_processable = generate_new_payments()

            # Then
            assert len(pending) == 3
            assert len(not_processable) == 0
            assert sum(p.amount for p in pending) == 30000

        @clean_database
        def test_reimburses_offerer_with_degressive_rate_for_venues_with_bookings_exceeding_20000_euros(self, app):
            # Given
            offerer1 = create_offerer(siren='123456789')
            PcObject.save(offerer1)
            bank_information = create_bank_information(bic='BDFEFR2LCCB', iban='FR7630006000011234567890189',
                                                       id_at_providers='123456789', offerer=offerer1)
            venue1 = create_venue(offerer1, siret='12345678912345')
            venue2 = create_venue(offerer1, siret='98765432154321')
            venue3 = create_venue(offerer1, siret='98123432154321')
            offer1 = create_offer_with_thing_product(venue1)
            offer2 = create_offer_with_thing_product(venue2)
            offer3 = create_offer_with_thing_product(venue3)
            paying_stock1 = create_stock_from_offer(offer1, price=10000)
            paying_stock2 = create_stock_from_offer(offer2, price=10000)
            paying_stock3 = create_stock_from_offer(offer3, price=30000)
            user = create_user()
            deposit = create_deposit(user, amount=50000)
            booking1 = create_booking(user, paying_stock1, venue1, quantity=1, is_used=True)
            booking2 = create_booking(user, paying_stock2, venue2, quantity=1, is_used=True)
            booking3 = create_booking(user, paying_stock3, venue3, quantity=1, is_used=True)
            PcObject.save(deposit, booking1, booking2, booking3, bank_information)

            # When
            pending, not_processable = generate_new_payments()

            # Then
            assert len(pending) == 3
            assert len(not_processable) == 0
            assert sum(p.amount for p in pending) == 48500