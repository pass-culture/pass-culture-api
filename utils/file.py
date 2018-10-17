""" file """
from flask import jsonify

from models.api_errors import ApiErrors

ALLOWED_EXTENSIONS = set(['jpg', 'png', 'jpeg', 'gif', 'pdf'])

def has_file(key, files=files, form=form):
    if key in files:
        if files[key].filename == '':
            return False
    elif key + 'Url' not in form:
        return False
    return True

def read_file(key, extensions=ALLOWED_EXTENSIONS, files=files, form=form):
    if key in files:
        data_file = files[key]
        filename_parts = file.filename.rsplit('.', 1)
        if len(filename_parts) < 2 \
           or filename_parts[1].lower() not in extensions:
            api_errors = ApiErrors()
            api_errors.addError(key, "Ce fichier manque d'une extension (.png, .jpg...) ou son format n'est pas autorisé")
            raise api_errors
        return data_file.read()
