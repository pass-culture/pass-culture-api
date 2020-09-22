import base64
import io
from typing import Dict

import qrcode
import qrcode.image.svg
from PIL import Image


QR_CODE_PASS_CULTURE_VERSION = 'v2'
QR_CODE_VERSION = 2
QR_CODE_BOX_SIZE = 5
QR_CODE_BOX_BORDER = 1


def generate_qr_code(booking_token: str, offer_extra_data: Dict) -> str:
    qr = qrcode.QRCode(
        version=QR_CODE_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=QR_CODE_BOX_SIZE,
        border=QR_CODE_BOX_BORDER,
    )

    product_isbn = ''
    if offer_extra_data and 'isbn' in offer_extra_data:
        product_isbn = offer_extra_data['isbn']

    data = f'PASSCULTURE:{QR_CODE_PASS_CULTURE_VERSION};'

    if product_isbn != '':
        data += f'EAN13:{product_isbn};'

    data += f'TOKEN:{booking_token}'

    qr.add_data(data)
    image = qr.make_image(fill_color='black', back_color='white')
    return _convert_image_to_base64(image)


def _convert_image_to_base64(image: Image) -> str:
    image_as_bytes = io.BytesIO()
    image.save(image_as_bytes)
    image_as_base64 = base64.b64encode(image_as_bytes.getvalue())
    return f'data:image/png;base64,{str(image_as_base64, encoding="utf-8")}'
