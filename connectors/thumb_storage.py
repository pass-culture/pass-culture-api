from typing import Callable

import requests

from domain.mediations import DO_NOT_CROP, standardize_image, BLACK
from models import ApiErrors
from models.pc_object import PcObject
from utils.logger import logger
from utils.object_storage import store_public_object

ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg', 'gif'}
READABLE_EXTENSIONS = '(%s)' % ', '.join(map(lambda e: f'.{e}', reversed(sorted(ALLOWED_EXTENSIONS))))


def read_thumb(files=None, form=None):
    if 'thumb' in files:
        thumb = files['thumb']
        filename_parts = thumb.filename.rsplit('.', 1)
        if len(filename_parts) < 2 \
                or filename_parts[1].lower() not in ALLOWED_EXTENSIONS:
            raise ApiErrors(
                {'thumb': [
                    f"Cette image manque d'une extension {READABLE_EXTENSIONS} ou son format n'est pas autorisé"]}
            )
        return thumb.read()

    if 'thumbUrl' in form:
        try:
            return _fetch_image(form['thumbUrl'])
        except ValueError as e:
            logger.error(e)
            raise ApiErrors({'thumbUrl': ["L'adresse saisie n'est pas valide"]})


def save_thumb(
        model_with_thumb,
        thumb,
        image_index,
        image_type=None,
        dominant_color=None,
        convert=True,
        crop=None,
        symlink_path=None,
        need_save=True,
        store_thumb: Callable = store_public_object
):
    new_thumb = thumb

    if convert:
        crop_params = crop if crop is not None else DO_NOT_CROP
        new_thumb = standardize_image(thumb, crop_params)

    if image_index == 0:
        if dominant_color:
            model_with_thumb.firstThumbDominantColor = dominant_color
        else:
            model_with_thumb.firstThumbDominantColor = BLACK

    store_thumb(
        'thumbs',
        model_with_thumb.get_thumb_storage_id(image_index),
        new_thumb,
        'image/' + (image_type or 'jpeg'),
        symlink_path=symlink_path
    )

    model_with_thumb.thumbCount = model_with_thumb.thumbCount + 1

    if need_save:
        PcObject.save(model_with_thumb)


def _fetch_image(thumb_url: str) -> bytes:
    if not thumb_url[0:4] == 'http':
        raise ValueError('Invalid thumb URL : %s' % thumb_url)

    try:
        response = requests.get(thumb_url)
    except Exception as e:
        logger.error(e)
        raise ApiErrors({'thumbUrl': ["Impossible de télécharger l'image à cette adresse"]})
    content_type = response.headers['Content-type']
    is_an_image = content_type.split('/')[0] == 'image'

    if response.status_code == 200 and is_an_image:
        return response.content
    else:
        raise ValueError(
            'Error downloading thumb from url %s (status_code : %s)'
            % (thumb_url, str(response.status_code)))
