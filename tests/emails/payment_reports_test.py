import base64
import io
from unittest.mock import Mock
from unittest.mock import patch
import zipfile

from bs4 import BeautifulSoup
from freezegun import freeze_time

from pcapi.utils.mailing import make_payment_details_email
from pcapi.utils.mailing import make_payment_message_email
from pcapi.utils.mailing import make_payments_report_email


@freeze_time('2018-10-15 09:21:34')
class MakePaymentsReportEmailTest:
    @classmethod
    def setup_class(self):
        self.grouped_payments = {
            'ERROR': [Mock(), Mock()],
            'SENT': [Mock()],
            'PENDING': [Mock(), Mock(), Mock()]
        }

        self.not_processable_csv = '"header A","header B","header C","header D"\n"part A","part B","part C","part D"\n'
        self.error_csv = '"header 1","header 2","header 3","header 4"\n"part 1","part 2","part 3","part 4"\n'

    def test_it_contains_the_two_csv_files_as_attachment(self, app):
        # When
        email = make_payments_report_email(self.not_processable_csv, self.error_csv, self.grouped_payments)

        # Then
        assert email["Attachments"] == [
            {
                "ContentType": "text/csv",
                "Filename": "paiements_non_traitables_2018-10-15.csv",
                "Content": 'ImhlYWRlciBBIiwiaGVhZGVyIEIiLCJoZWFkZXIgQyIsImhlYWRlciBE'
                           'IgoicGFydCBBIiwicGFydCBCIiwicGFydCBDIiwicGFydCBEIgo='
            },
            {
                "ContentType": "text/csv",
                "Filename": "paiements_en_erreur_2018-10-15.csv",
                "Content": 'ImhlYWRlciAxIiwiaGVhZGVyIDIiLCJoZWFkZXIgMyIsImhlYWRlciA0'
                           'IgoicGFydCAxIiwicGFydCAyIiwicGFydCAzIiwicGFydCA0Igo='
            }
        ]

    def test_it_contains_from_and_subject_info(self, app):
        # When
        email = make_payments_report_email(self.not_processable_csv, self.error_csv, self.grouped_payments)

        # Then
        assert email["FromEmail"] == 'support@example.com'
        assert email["FromName"] == "pass Culture Pro"
        assert email["Subject"] == "Récapitulatif des paiements pass Culture Pro - 2018-10-15"

    def test_it_contains_the_total_count_of_payments(self, app):
        # When
        email = make_payments_report_email(self.not_processable_csv, self.error_csv, self.grouped_payments)

        # Then
        email_html = BeautifulSoup(email['Html-part'], 'html.parser')
        assert email_html.find('p', {'id': 'total'}).text == 'Nombre total de paiements : 6'

    def test_it_contains_a_count_of_payments_by_status_in_html_part(self, app):
        # When
        email = make_payments_report_email(self.not_processable_csv, self.error_csv, self.grouped_payments)

        # Then
        email_html = BeautifulSoup(email['Html-part'], 'html.parser')
        assert email_html.find('ul').text == '\nERROR : 2\nSENT : 1\nPENDING : 3\n'


@freeze_time('2018-10-15 09:21:34')
def test_make_payment_message_email_sends_a_xml_file_with_its_checksum_in_email_body(app):
    # Given
    xml = '<?xml version="1.0" encoding="UTF-8"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"></Document>'
    checksum = b'\x16\x91\x0c\x11~Hs\xc5\x1a\xa3W1\x13\xbf!jq@\xea  <h&\xef\x1f\xaf\xfc\x7fO\xc8\x82'

    # When
    email = make_payment_message_email(xml, checksum)

    # Then
    assert email["FromEmail"] == 'support@example.com'
    assert email["FromName"] == "pass Culture Pro"
    assert email["Subject"] == "Virements XML pass Culture Pro - 2018-10-15"
    assert email["Attachments"] == [{"ContentType": "text/xml",
                                     "Filename": "message_banque_de_france_20181015.xml",
                                     "Content": 'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48RG9j'
                                                'dW1lbnQgeG1sbnM9InVybjppc286c3RkOmlzbzoyMDAyMjp0ZWNoOnhz'
                                                'ZDpwYWluLjAwMS4wMDEuMDMiPjwvRG9jdW1lbnQ+'}]
    email_html = BeautifulSoup(email['Html-part'], 'html.parser')
    assert 'message_banque_de_france_20181015.xml' in email_html.find('p', {'id': 'file_name'}).find('strong').text
    assert '16910c117e4873c51aa3573113bf216a7140ea20203c6826ef1faffc7f4fc882' \
           in email_html.find('p', {'id': 'checksum'}).find('strong').text


@freeze_time('2018-10-15 09:21:34')
def test_make_payment_details_email():
    # Given
    csv = '"header A","header B","header É"\n"part A","part B","part É"\n'

    # When
    email = make_payment_details_email(csv)

    # Then
    expected_csv_name = "details_des_paiements_20181015.csv"
    assert email["FromEmail"] == 'support@example.com'
    assert email["FromName"] == "pass Culture Pro"
    assert email["Subject"] == "Détails des paiements pass Culture Pro - 2018-10-15"
    assert email["Html-part"] == ""
    assert len(email["Attachments"]) == 1
    attachment = email["Attachments"][0]
    assert attachment["ContentType"] == "application/zip"
    assert attachment['Filename'] == f"{expected_csv_name}.zip"
    encoded_zip_content = attachment["Content"]
    zip_content = base64.b64decode(encoded_zip_content)
    zf = zipfile.ZipFile(io.BytesIO(zip_content))
    assert zf.namelist() == [expected_csv_name]
    csv_in_zip_file = zf.open(expected_csv_name).read().decode('utf-8')
    assert csv_in_zip_file == csv
