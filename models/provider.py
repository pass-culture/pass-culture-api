""" provider """
from flask import current_app as app
from sqlalchemy.dialects.postgresql import CHAR

db = app.db


class Provider(app.model.PcObject,
               app.model.DeactivableMixin,
               db.Model):
    id = db.Column(db.BigInteger,
                   primary_key=True)

    name = db.Column(db.String(60),
                     nullable=False)

    localClass = db.Column(db.String(30),
                           db.CheckConstraint('("localClass" IS NOT NULL AND "apiKey" IS NULL)'
                                              + 'OR ("localClass" IS NULL AND "apiKey" IS NOT NULL)',
                                              name='check_provider_has_localclass_or_apikey'),
                           nullable=True,
                           unique=True)

    venueProviders = db.relationship(app.model.VenueProvider,
                                     back_populates="provider",
                                     foreign_keys=[app.model.VenueProvider.providerId])

    apiKey = db.Column(CHAR(32),
                       nullable=True)

    apiKeyGenerationDate = db.Column(db.DateTime,
                                     nullable=True)

    def getByClassName(name):
        return Provider.query\
                       .filter_by(localClass=name)\
                       .first()


app.model.Provider = Provider
