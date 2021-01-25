from pcapi.models.db import Model
from pcapi.utils import object_storage
from pcapi.utils.image_conversion import standardize_image


def create_thumb(
    model_with_thumb: Model,
    image_as_bytes: bytes,
    image_index: int,
    crop_params: tuple = None,
    symlink_path: str = None,
) -> None:
    image_as_bytes = standardize_image(image_as_bytes, crop_params)

    object_storage.store_public_object(
        bucket="thumbs",
        object_id=model_with_thumb.get_thumb_storage_id(image_index),
        blob=image_as_bytes,
        content_type="image/jpeg",
        symlink_path=symlink_path,
    )
