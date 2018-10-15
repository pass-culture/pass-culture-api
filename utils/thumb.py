""" thumb """
from models.api_errors import ApiErrors
from utils.file import ALLOWED_EXTENSIONS as AE, has_file, read_file

ALLOWED_EXTENSIONS = set([ex for ex in AE if ex != 'pdf'])

def get_crop(form):
    if 'croppingRect[x]' in form \
        and 'croppingRect[y]' in form \
        and 'croppingRect[height]' in form:
        return [float(form['croppingRect[x]']),
                float(form['croppingRect[y]']),
                float(form['croppingRect[height]'])]

def has_thumb(files=None, form=None):
    return has_file('thumb', files=files, form=form)

def read_thumb(files=None, form=None):
    return read_file('thumb', ALLOWED_EXTENSIONS, files=files, form=form)
