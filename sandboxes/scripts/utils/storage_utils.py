import os
from pathlib import Path
from sqlalchemy_api_handler import ApiHandler, humanize

from connectors.thumb_storage import save_thumb
from utils.object_storage import store_public_object
from utils.string_processing import get_model_plural_name

MIMES_BY_FOLDER = {
    "spreadsheets": "application/CSV",
    "thumbs": "image/jpeg",
    "zips": "application/zip"
}

def store_public_object_from_sandbox_assets(folder, obj, product_type, index=0):
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    plural_model_name = get_model_plural_name(obj)
    thumb_id = humanize(obj.id)

    thumb_path = dir_path\
                 / '..' / '..' / folder / plural_model_name\
                 / str(product_type)

    with open(thumb_path, mode='rb') as thumb_file:
        if folder == "thumbs":
            save_thumb(
                obj,
                thumb_file.read(),
                index,
                dominant_color=b'\x00\x00\x00',
                convert=False,
                symlink_path=thumb_path
            )
        else:
            store_public_object(folder,
                                plural_model_name + '/' + thumb_id,
                                thumb_file.read(),
                                MIMES_BY_FOLDER[folder],
                                symlink_path=thumb_path)

    ApiHandler.save(obj)
