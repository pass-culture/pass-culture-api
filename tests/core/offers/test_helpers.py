from unittest.mock import patch

from core.offers import helpers
from utils.token import random_token


class TestGenerateQrCode:
    @patch('domain.bookings.qrcode.QRCode')
    def test_correct_technical_parameters(self, build_qr_code):
        helpers.generate_qr_code(random_token(), offer_extra_data={})
        build_qr_code.assert_called_once_with(
            version=2,
            error_correction=3,
            box_size=5,
            border=1,
        )

    @patch('domain.bookings.qrcode.QRCode.make_image')
    def test_should_build_qr_code_with_correct_image_parameters(
            self,
            build_qr_code_image_parameters
    ):
        helpers.generate_qr_code(booking_token='ABCDE', offer_extra_data={})
        build_qr_code_image_parameters.assert_called_once_with(
            back_color='white',
            fill_color='black',
        )

    @patch('domain.bookings.qrcode.QRCode.add_data')
    def test_include_product_isbn_if_provided(self, build_qr_code_booking_info):
        helpers.generate_qr_code('ABCDE', offer_extra_data={})
        build_qr_code_booking_info.assert_called_once_with(
            f'PASSCULTURE:v2;'
            f'TOKEN:ABCDE'
        )

        helpers.generate_qr_code('ABCDE', offer_extra_data={'isbn': '123456789'})
        build_qr_code_booking_info.assert_called_once_with(
            f'PASSCULTURE:v2;'
            f'EAN13:123456789;'
            f'TOKEN:ABCDE'
        )

    def test_generated_qr_code(self):
        qr_code = helpers.generate_qr_code('ABCDE', offer_extra_data={})
        assert isinstance(qr_code, str)
        assert qr_code == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJsAAACbAQAAAABdGtQhAAABs0lEQVR4nL1XMY7bMBCcFQXQqagf0EDeYSlp8o/8w7Hko/8VyfcR6gdURwKSJ4VdxYc0580WJDDFDHZJzoBCPNVcPWPAZ8EiIlKq5ZcUkWEWkfrTnB+DHRnRukDHBJAclIQoNeyI8758wwVFmhdwflD1fWMF2HNjXsL5b9BEdBw0hYQrIAkoXXOEZdIRQgaA3LoQc+tCBGCiihBJkiMMLVNPklQSmsiIjqvPrVs9mbQ6mpLhY2GI6BiUhG5uBW8uRDu6QMDpjK4uP3DxkLR9LSds+/wlKV1v+wYz4brYyGnmBGp5Xfk+r750zXEulav9ruOq5QxOxI6uhh2x7e3bSzifqwaW1QscPNikvuzQ/9Tp6ODDxBu2fekTAKFWHgFbhytMtL+bC3ZYdM4IWRJgR0daJkN7czoPtsLBD76cgDnTD8jvSS0m5nUGFtlLhU3ktOhE+d29c5d6kskwt0qje+SRcPBoXYhZy+uQOzJydCFaJsMsWnmUW5jIKT16g9boHuChMbyn31XpHT3AK46wZwlx176M829QuKL0Cdi1rp7t6HQs6H4yvOGIDPR6t07+12/iD1lz9hCJWM0gAAAAAElFTkSuQmCC"
