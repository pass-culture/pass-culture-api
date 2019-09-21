import re
from sqlalchemy import Column, String
from sqlalchemy_api_handler import ApiErrors

# TODO: turn this into a custom type "Address" ?


class HasAddressMixin(object):
    address = Column(String(200), nullable=True)

    postalCode = Column(String(6), nullable=False)

    city = Column(String(50), nullable=False)

    def errors(self):
        errors = ApiErrors()
        if self.postalCode is not None\
           and not re.match('^\d[AB0-9]\d{3,4}$', self.postalCode):
            errors.add_error('postalCode', 'Ce code postal est invalide')
        return errors
