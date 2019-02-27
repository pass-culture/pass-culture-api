from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from uuid import UUID

import pytest
from freezegun import freeze_time
from lxml import etree
from lxml.etree import DocumentInvalid

from domain.payments import validate_transaction_file_structure, generate_transaction_file, \
    read_message_id_in_transaction_file, \
    generate_file_checksum
from tests.test_utils import create_payment, create_offerer, create_user, create_venue, create_stock_from_offer, \
    create_booking, create_thing_offer, create_bank_information

XML_NAMESPACE = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'}
MESSAGE_ID = 'passCulture-SCT-20181015-114356'


@pytest.mark.standalone
class GenerateTransactionFileTest:
    def test_generate_transaction_file_has_custom_message_id_in_group_header(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)
        payment1 = create_payment(booking, offerer, Decimal(10))
        payment2 = create_payment(booking, offerer, Decimal(20))
        payments = [
            payment1,
            payment2
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:GrpHdr/ns:MsgId', xml) == MESSAGE_ID, \
            'The message id should look like "passCulture-SCT-YYYYMMDD-HHMMSS"'

    @freeze_time('2018-10-15 09:21:34')
    def test_generate_transaction_file_has_creation_datetime_in_group_header(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)
        payment1 = create_payment(booking, offerer, Decimal(10))
        payment2 = create_payment(booking, offerer, Decimal(20))
        payments = [
            payment1,
            payment2
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:GrpHdr/ns:CreDtTm', xml) == '2018-10-15T09:21:34', \
            'The creation datetime should look like YYYY-MM-DDTHH:MM:SS"'

    def test_generate_transaction_file_has_initiating_party_in_group_header(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)
        payment1 = create_payment(booking, offerer, Decimal(10))
        payment2 = create_payment(booking, offerer, Decimal(20))
        payments = [
            payment1,
            payment2
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:GrpHdr/ns:InitgPty/ns:Nm', xml) == 'pass Culture', \
            'The initiating party should be "pass Culture"'

    def test_generate_transaction_file_has_control_sum_in_group_header(self, app):
        # Given
        user = create_user()
        offerer1 = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer1
        offerer2 = create_offerer()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking1, offerer1, Decimal(20)),
            create_payment(booking2, offerer2, Decimal(30))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:GrpHdr/ns:CtrlSum', xml) == '30', \
            'The control sum should match the total amount of money to pay'

    def test_generate_transaction_file_has_number_of_transactions_in_group_header(self, app):
        # Given
        offerer1 = create_offerer()
        offerer2 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        offerer3 = create_offerer()
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        venue3 = create_venue(offerer3)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer2, Decimal(20)),
            create_payment(booking3, offerer3, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:GrpHdr/ns:NbOfTxs', xml) == '2', \
            'The number of transactions should match the distinct number of IBANs'

    def test_generate_transaction_file_has_payment_info_id_in_payment_info(self, app):
        # Given
        offerer1 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        user = create_user()
        venue1 = create_venue(offerer1)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        booking1 = create_booking(user, stock1)

        payments = [create_payment(booking1, offerer1, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:PmtInfId', xml) == MESSAGE_ID, \
            'The payment info id should be the same as message id since we only send one payment per XML message'

    def test_generate_transaction_file_has_number_of_transactions_in_payment_info(self, app):
        # Given
        offerer1 = create_offerer()
        offerer2 = create_offerer()
        offerer3 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        venue3 = create_venue(offerer3)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer2, Decimal(20)),
            create_payment(booking3, offerer3, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:NbOfTxs', xml) == '2', \
            'The number of transactions should match the distinct number of IBANs'

    def test_generate_transaction_file_has_control_sum_in_payment_info(self, app):
        # Given
        user = create_user()
        offerer1 = create_offerer()
        offerer2 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking1, offerer1, Decimal(20)),
            create_payment(booking2, offerer2, Decimal(30))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:CtrlSum', xml) == '30', \
            'The control sum should match the total amount of money to pay'

    def test_generate_transaction_file_has_payment_method_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:PmtMtd', xml) == 'TRF', \
            'The payment method should be TRF because we want to transfer money'

    def test_generate_transaction_file_has_service_level_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:PmtTpInf/ns:SvcLvl/ns:Cd', xml) == 'SEPA', \
            'The service level should be SEPA'

    def test_generate_transaction_file_has_category_purpose_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:PmtTpInf/ns:CtgyPurp/ns:Cd', xml) == 'GOVT', \
            'The category purpose should be GOVT since we handle government subventions'

    def test_generate_transaction_file_has_banque_de_france_bic_in_debtor_agent(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:DbtrAgt/ns:FinInstnId/ns:BIC', xml) == 'AZERTY9Q666'

    def test_generate_transaction_file_has_banque_de_france_iban_in_debtor_account(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:DbtrAcct/ns:Id/ns:IBAN', xml) == 'BD12AZERTY123456'

    def test_generate_transaction_file_has_debtor_name_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:Dbtr/ns:Nm', xml) == 'pass Culture', \
            'The name of the debtor should be "pass Culture"'

    @freeze_time('2018-10-15 09:21:34')
    def test_generate_transaction_file_has_requested_execution_datetime_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:ReqdExctnDt', xml) == '2018-10-22', \
            'The requested execution datetime should be in one week from now'

    def test_generate_transaction_file_has_charge_bearer_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:ChrgBr', xml) == 'SLEV', \
            'The charge bearer should be SLEV as in "following service level"'

    def test_generate_transaction_file_has_iban_in_credit_transfer_transaction_info(self, app):
        # Given
        offerer1 = create_offerer()
        offerer2 = create_offerer()
        offerer3 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1, idx=4)
        venue2 = create_venue(offerer2, idx=5)
        venue3 = create_venue(offerer3, idx=6)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10), idx=7),
            create_payment(booking2, offerer2, Decimal(20), idx=8),
            create_payment(booking3, offerer3, Decimal(20), idx=9)
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:CdtrAcct/ns:Id/ns:IBAN', xml)[0] == 'CF13QSDFGH456789'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:CdtrAcct/ns:Id/ns:IBAN', xml)[1] == 'FR14WXCVBN123456'

    def test_generate_transaction_file_has_recipient_name_and_siren_in_creditor_info(self, app):
        # Given
        offerer1 = create_offerer(name='first offerer', siren='123456789')
        offerer2 = create_offerer(name='second offerer', siren='987654321')
        offerer3 = create_offerer()
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        venue3 = create_venue(offerer3)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer2, Decimal(20)),
            create_payment(booking3, offerer3, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:Cdtr/ns:Nm', xml)[0] == 'first offerer'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:Cdtr/ns:Id/ns:OrgId/ns:Othr/ns:Id', xml)[0] == '123456789'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:Cdtr/ns:Nm', xml)[1] == 'second offerer'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:Cdtr/ns:Id/ns:OrgId/ns:Othr/ns:Id', xml)[1] == '987654321'

    def test_generate_transaction_file_has_bic_in_credit_transfer_transaction_info(self, app):
        # Given
        offerer1 = create_offerer(name='first offerer')
        offerer2 = create_offerer(name='second offerer')
        offerer3 = create_offerer(name='third offerer')
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        venue3 = create_venue(offerer3)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer2, Decimal(20)),
            create_payment(booking3, offerer3, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:CdtrAgt/ns:FinInstnId/ns:BIC', xml)[0] == 'QSDFGH8Z555'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:CdtrAgt/ns:FinInstnId/ns:BIC', xml)[1] == 'WXCVBN7B444'

    def test_generate_transaction_file_has_bic_in_credit_transfer_transaction_info(self, app):
        # Given
        offerer1 = create_offerer(name='first offerer')
        offerer2 = create_offerer(name='second offerer')
        offerer3 = create_offerer(name='third offerer')
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        venue3 = create_venue(offerer3)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        stock3 = create_stock_from_offer(create_thing_offer(venue3))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10), custom_message='remboursement 1ère quinzaine 09-2018',
                    ),
            create_payment(booking2, offerer2, Decimal(20), custom_message='remboursement 1ère quinzaine 09-2018',
                    ),
            create_payment(booking3, offerer3, Decimal(20), custom_message='remboursement 1ère quinzaine 09-2018',
                    )
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:RmtInf/ns:Ustrd', xml)[0] \
               == 'remboursement 1ère quinzaine 09-2018'
        assert find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:RmtInf/ns:Ustrd', xml)[1] \
               == 'remboursement 1ère quinzaine 09-2018'

    def test_generate_transaction_file_has_amount_in_credit_transfer_transaction_info(self, app):
        # Given
        offerer1 = create_offerer(name='first offerer')
        offerer2 = create_offerer(name='second offerer')
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        user = create_user()
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue1))
        stock3 = create_stock_from_offer(create_thing_offer(venue2))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        booking3 = create_booking(user, stock3)

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer1, Decimal(20)),
            create_payment(booking3, offerer2, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        nodes_amount = find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:Amt/ns:InstdAmt', xml)
        assert nodes_amount[0] == '30'
        assert nodes_amount[1] == '20'

    @patch('domain.payments.uuid.uuid4')
    def test_generate_transaction_file_has_hexadecimal_uuids_as_end_to_end_ids_in_transaction_info(self, mocked_uuid,
                                                                                                   app):
        # Given
        user = create_user()
        offerer1 = create_offerer(name='first offerer')
        offerer2 = create_offerer(name='second offerer')
        offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information1.offerer = offerer1
        offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
        offerer_bank_information2.offerer = offerer2
        venue1 = create_venue(offerer1)
        venue2 = create_venue(offerer2)
        stock1 = create_stock_from_offer(create_thing_offer(venue1))
        stock2 = create_stock_from_offer(create_thing_offer(venue2))
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        uuid1 = UUID(hex='abcd1234abcd1234abcd1234abcd1234', version=4)
        uuid2 = UUID(hex='cdef5678cdef5678cdef5678cdef5678', version=4)
        mocked_uuid.side_effect = [uuid1, uuid2]

        payments = [
            create_payment(booking1, offerer1, Decimal(10)),
            create_payment(booking2, offerer2, Decimal(20))
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        nodes_id = find_all_nodes('//ns:PmtInf/ns:CdtTrfTxInf/ns:PmtId/ns:EndToEndId', xml)
        assert nodes_id[0] == uuid1.hex
        assert nodes_id[1] == uuid2.hex

    def test_generate_transaction_file_has_ultimate_debtor_in_transaction_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)
        payment1 = create_payment(booking, offerer, Decimal(10))
        payment2 = create_payment(booking, offerer, Decimal(20))
        payments = [
            payment1,
            payment2
        ]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:PmtInf/ns:CdtTrfTxInf/ns:UltmtDbtr/ns:Nm', xml) == 'pass Culture', \
            'The ultimate debtor name should be "pass Culture"'

    def test_generate_transaction_file_has_initiating_party_id_in_payment_info(self, app):
        # Given
        offerer = create_offerer()
        offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
        offerer_bank_information.offerer = offerer
        user = create_user()
        venue = create_venue(offerer)
        stock = create_stock_from_offer(create_thing_offer(venue))
        booking = create_booking(user, stock)

        payments = [create_payment(booking, offerer, Decimal(10))]

        # When
        xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

        # Then
        assert find_node('//ns:InitgPty/ns:Id/ns:OrgId/ns:Othr/ns:Id', xml) == '0000', \
            'The initiating party id should be 0000"'


@pytest.mark.standalone
@freeze_time('2018-10-15 09:21:34')
@patch('domain.payments.uuid.uuid4')
def test_generate_file_checksum_returns_a_checksum_of_the_file(mocked_uuid, app):
    # given
    offerer1 = create_offerer(name='first offerer')
    offerer2 = create_offerer(name='second offerer')
    offerer_bank_information1 = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
    offerer_bank_information1.offerer = offerer1
    offerer_bank_information2 = create_bank_information(iban='FR14WXCVBN123456', bic='WXCVBN7B444')
    offerer_bank_information2.offerer = offerer2
    user = create_user()
    venue1 = create_venue(offerer1)
    venue2 = create_venue(offerer2)
    stock1 = create_stock_from_offer(create_thing_offer(venue1))
    stock2 = create_stock_from_offer(create_thing_offer(venue1))
    stock3 = create_stock_from_offer(create_thing_offer(venue2))
    booking1 = create_booking(user, stock1)
    booking2 = create_booking(user, stock2)
    booking3 = create_booking(user, stock3)

    payments = [
        create_payment(booking1, offerer1, Decimal(10)),
        create_payment(booking2, offerer1, Decimal(20)),
        create_payment(booking3, offerer2, Decimal(20))
    ]
    uuid1 = UUID(hex='abcd1234abcd1234abcd1234abcd1234', version=4)
    uuid2 = UUID(hex='cdef5678cdef5678cdef5678cdef5678', version=4)
    mocked_uuid.side_effect = [uuid1, uuid2]

    xml = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

    # when
    checksum = generate_file_checksum(xml)

    # then
    assert checksum == b'\x16\x91\x0c\x11~Hs\xc5\x1a\xa3W1\x13\xbf!jq@\xea  <h&\xef\x1f\xaf\xfc\x7fO\xc8\x82'


@pytest.mark.standalone
def test_validate_transaction_file_structure_raises_a_document_invalid_exception_with_specific_error_when_xml_is_invalid(
        app):
    # given
    transaction_file = '''
        <broken><xml></xml></broken>
    '''

    # when
    with pytest.raises(DocumentInvalid) as e:
        validate_transaction_file_structure(transaction_file)

    # then
    assert str(e.value) == "Element 'broken': No matching global declaration available for the validation root., line 2"


@pytest.mark.standalone
def test_read_message_id_in_transaction_file_returns_the_content_of_message_id_tag(app):
    # given
    offerer = create_offerer()

    offerer_bank_information = create_bank_information(iban='CF13QSDFGH456789', bic='QSDFGH8Z555')
    offerer_bank_information.offerer = offerer

    user = create_user()
    venue = create_venue(offerer)
    stock = create_stock_from_offer(create_thing_offer(venue))
    booking = create_booking(user, stock)
    payment1 = create_payment(booking, offerer, Decimal(10))
    payment2 = create_payment(booking, offerer, Decimal(20))
    payments = [payment1, payment2]

    xml_file = generate_transaction_file(payments, 'BD12AZERTY123456', 'AZERTY9Q666', MESSAGE_ID, '0000')

    # when
    message_id = read_message_id_in_transaction_file(xml_file)

    # then
    assert message_id == MESSAGE_ID


def find_node(xpath, transaction_file):
    xml = BytesIO(transaction_file.encode())
    tree = etree.parse(xml, etree.XMLParser())
    node = tree.find(xpath, namespaces=XML_NAMESPACE)
    return node.text


def find_all_nodes(xpath, transaction_file):
    xml = BytesIO(transaction_file.encode())
    tree = etree.parse(xml, etree.XMLParser())
    nodes = tree.findall(xpath, namespaces=XML_NAMESPACE)
    return [node.text for node in nodes]
