from itertools import chain
from datetime import datetime

from tests.conftest import clean_database

from models import Booking, Offerer, Payment, PcObject
from models.payment_status import TransactionStatus, PaymentStatus
from scripts.payment.batch_steps import generate_new_payments
from tests.test_utils import create_bank_information, create_stock_with_thing_offer, \
    create_deposit, create_venue, create_offerer, create_payment, \
    create_user, create_booking, create_user_offerer
from repository.reimbursement_queries import find_all_offerer_reimbursement_details
from domain.reimbursement import generate_reimbursement_details_csv
from domain.reimbursement import ReimbursementDetails


class ReimbursementDetailsCSVTest:
    @clean_database
    def test_generate_payment_details_csv_with_human_readable_header(self, app):
        # given
        reimbursement_details = []

        # when
        csv = generate_reimbursement_details_csv(reimbursement_details)

        # then
        assert _get_header(csv,
                           0) == "Année;Virement;Créditeur;SIRET créditeur;Adresse créditeur;IBAN;Raison sociale du lieu;Nom de l'offre;Nom utilisateur;Prénom utilisateur;Contremarque;Date de validation de la réservation;Montant remboursé;Statut du remboursement"

    @clean_database
    def test_generate_payment_details_csv_with_right_values(self, app):
        # given
        user = create_user(email='user+plus@email.fr')
        deposit = create_deposit(user, datetime.utcnow(), amount=500, source='public')
        offerer1 = create_offerer()
        user_offerer1 = create_user_offerer(user, offerer1, validation_token=None)
        venue1 = create_venue(offerer1)
        bank_information1 = create_bank_information(id_at_providers='79387501900056', venue=venue1)
        stock1 = create_stock_with_thing_offer(offerer=offerer1, venue=venue1, price=10)
        booking1 = create_booking(user, stock1, venue=venue1, token='ABCDEF', is_used=True)
        booking2 = create_booking(user, stock1, venue=venue1, token='ABCDEG')

        PcObject.save(deposit, booking1, booking2, user_offerer1, bank_information1)

        generate_new_payments()

        reimbursement_details = find_all_offerer_reimbursement_details(offerer1.id)


        # when
        csv = generate_reimbursement_details_csv(reimbursement_details)

        # then
        assert _count_non_empty_lines(csv) == 2
        assert _get_header(csv,
                           1) == "2019;Juillet : remboursement 1ère quinzaine;La petite librairie;12345678912345;123 rue de Paris;FR7630006000011234567890189;La petite librairie;Test Book;Doe;John;ABCDEF;;10.00;Remboursement initié"


class AsCsvRowTest:
    @clean_database
    def test_generate_payment_csv_raw_contains_human_readable_status_with_details(self, app):
        # given
        payment = Payment()
        user = create_user(email='user+plus@email.fr')
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_thing_offer(offerer=offerer, venue=venue, price=10)
        booking = create_booking(user, stock, venue=venue, token='ABCDEF', is_used=True)
        payment.booking = booking
        payment.booking.stock = stock

        payment_status = PaymentStatus()
        payment.transactionLabel = 'pass Culture Pro - remboursement 1ère quinzaine 07-2019'
        payment.amount = 50
        payment_status.status = TransactionStatus.ERROR
        payment_status.detail = 'Iban non fourni'
        payment_status.date = datetime.utcnow()
        payment.statuses = [payment_status]

        # when
        raw_csv = ReimbursementDetails(payment).as_csv_row()

        # then
        assert raw_csv[13] == 'Erreur d\'envoi du remboursement : Iban non fourni'


def _get_header(csv, line):
    return csv.split('\r\n')[line]


def _count_non_empty_lines(csv):
    return len(list(filter(lambda line: line != '', csv.split('\r\n'))))
