from freezegun import freeze_time
import pytest

import pcapi.core.offers.factories as offers_factories
import pcapi.core.payments.factories as payments_factories
from pcapi.core.payments.factories import PaymentFactory
from pcapi.core.payments.factories import PaymentWithCustomRuleFactory
from pcapi.models.payment_status import TransactionStatus
from pcapi.repository.reimbursement_queries import find_sent_offerer_payments
from pcapi.routes.serialization.reimbursement_csv_serialize import ReimbursementDetails
from pcapi.routes.serialization.reimbursement_csv_serialize import _get_reimbursement_current_status_in_details
from pcapi.routes.serialization.reimbursement_csv_serialize import find_all_offerer_reimbursement_details
from pcapi.routes.serialization.reimbursement_csv_serialize import generate_reimbursement_details_csv


class ReimbursementDetailsTest:
    @pytest.mark.usefixtures("db_session")
    def test_reimbursementDetail_as_csv(self, app):
        # given
        payment = PaymentFactory(
            transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 07-2019",
            booking__amount=10.5,
            booking__quantity=2,
        )
        payments_factories.PaymentStatusFactory(payment=payment, status=TransactionStatus.SENT)

        payments_info = find_sent_offerer_payments(payment.booking.stock.offer.venue.managingOfferer.id)

        # when
        raw_csv = ReimbursementDetails(payments_info[0]).as_csv_row()

        # then
        assert raw_csv[0] == "2019"
        assert raw_csv[1] == "Juillet : remboursement 1ère quinzaine"
        assert raw_csv[2] == payment.booking.stock.offer.venue.name
        assert raw_csv[3] == payment.booking.stock.offer.venue.siret
        assert raw_csv[4] == payment.booking.stock.offer.venue.address
        assert raw_csv[5] == payment.iban
        assert raw_csv[6] == payment.booking.stock.offer.venue.name
        assert raw_csv[7] == payment.booking.stock.offer.name
        assert raw_csv[8] == "Doux"
        assert raw_csv[9] == "Jeanne"
        assert raw_csv[10] == payment.booking.token
        assert raw_csv[11] == payment.booking.dateUsed
        assert raw_csv[12] == payment.booking.total_amount
        assert raw_csv[13] == f"{int(payment.reimbursementRate * 100)}%"
        assert raw_csv[14] == payment.amount
        assert raw_csv[15] == "Remboursement envoyé"

    @pytest.mark.usefixtures("db_session")
    def test_reimbursementDetail_with_custom_rule_as_csv(self, app):
        # given
        payment = PaymentWithCustomRuleFactory(
            transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 07-2019",
            booking__amount=10.5,
            booking__quantity=2,
        )
        payments_factories.PaymentStatusFactory(payment=payment, status=TransactionStatus.SENT)

        payments_info = find_sent_offerer_payments(payment.booking.stock.offer.venue.managingOfferer.id)

        # when
        raw_csv = ReimbursementDetails(payments_info[0]).as_csv_row()

        # then
        assert raw_csv[13] == ""


@pytest.mark.parametrize(
    "current_status,expected_display",
    [
        (TransactionStatus.PENDING, "Remboursement en cours"),
        (TransactionStatus.NOT_PROCESSABLE, "Remboursement impossible : Iban Non Fourni"),
        (TransactionStatus.SENT, "Remboursement envoyé"),
        (TransactionStatus.RETRY, "Remboursement à renvoyer"),
        (TransactionStatus.BANNED, "Remboursement rejeté"),
        (TransactionStatus.ERROR, "Remboursement en cours"),
        (TransactionStatus.UNDER_REVIEW, "Remboursement en cours"),
    ],
)
def test_human_friendly_status_can_contain_details_only_for_not_processable_transaction(
    current_status, expected_display
):
    # given
    current_status_details = "Iban Non Fourni"

    # when
    human_friendly_status = _get_reimbursement_current_status_in_details(current_status, current_status_details)

    # then
    assert human_friendly_status == expected_display


def test_human_friendly_status_contains_details_for_not_processable_transaction_only_when_details_exists():
    # given
    current_status = TransactionStatus.NOT_PROCESSABLE
    current_status_details = ""

    # when
    human_friendly_status = _get_reimbursement_current_status_in_details(current_status, current_status_details)

    # then
    assert human_friendly_status == "Remboursement impossible"


@pytest.mark.usefixtures("db_session")
@freeze_time("2019-07-05 12:00:00")
def test_generate_reimbursement_details_csv():
    # given
    payment = PaymentFactory(
        booking__stock__offer__name='Mon titre ; un peu "spécial"',
        booking__stock__offer__venue__name='Mon lieu ; un peu "spécial"',
        booking__stock__offer__venue__siret="siret-1234",
        booking__token="0E2722",
        booking__amount=10.5,
        booking__quantity=2,
        iban="iban-1234",
        transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 07-2019",
    )
    payments_factories.PaymentStatusFactory(payment=payment, status=TransactionStatus.SENT)
    offerer = payment.booking.stock.offer.venue.managingOfferer
    reimbursement_details = find_all_offerer_reimbursement_details(offerer.id)

    # when
    csv = generate_reimbursement_details_csv(reimbursement_details)

    # then
    rows = csv.splitlines()
    assert (
        rows[0]
        == '"Année";"Virement";"Créditeur";"SIRET créditeur";"Adresse créditeur";"IBAN";"Raison sociale du lieu";"Nom de l\'offre";"Nom utilisateur";"Prénom utilisateur";"Contremarque";"Date de validation de la réservation";"Montant de la réservation";"Barème";"Montant remboursé";"Statut du remboursement"'
    )
    assert (
        rows[1]
        == '"2019";"Juillet : remboursement 1ère quinzaine";"Mon lieu ; un peu ""spécial""";"siret-1234";"1 boulevard Poissonnière";"iban-1234";"Mon lieu ; un peu ""spécial""";"Mon titre ; un peu ""spécial""";"Doux";"Jeanne";"0E2722";"";21.00;"100%";21.00;"Remboursement envoyé"'
    )


@pytest.mark.usefixtures("db_session")
def test_find_all_offerer_reimbursement_details():
    offerer = offers_factories.OffererFactory()
    venue1 = offers_factories.VenueFactory(managingOfferer=offerer)
    venue2 = offers_factories.VenueFactory(managingOfferer=offerer)
    label = ("pass Culture Pro - remboursement 1ère quinzaine 07-2019",)
    payment_1 = payments_factories.PaymentFactory(booking__stock__offer__venue=venue1, transactionLabel=label)
    payments_factories.PaymentStatusFactory(payment=payment_1, status=TransactionStatus.SENT)
    payment_2 = payments_factories.PaymentFactory(booking__stock__offer__venue=venue2, transactionLabel=label)
    payments_factories.PaymentStatusFactory(payment=payment_2, status=TransactionStatus.SENT)

    reimbursement_details = find_all_offerer_reimbursement_details(offerer.id)

    assert len(reimbursement_details) == 2
