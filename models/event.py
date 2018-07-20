from datetime import datetime
from enum import Enum
from flask import current_app as app
from sqlalchemy import Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.sql.expression import cast, false
from sqlalchemy.sql.functions import coalesce

from utils.schema_org import make_schema_org_hierarchy_and_enum
from utils.search import create_tsvector


class Accessibility(Enum):
    HEARING_IMPAIRED = 1
    VISUALLY_IMPAIRED = 2
    SIGN_LANGUAGE = 4
    MOTION_IMPAIRED = 8
    MENTALLY_IMPAIRED = 16


class EventType(Enum):
    Workshop          = "Cours ou atelier de pratique artistique, bal..."
    MovieScreening    = "Cinéma / Projection de film"
    Meeting           = "Dédicace / Rencontre / Conférence"
    Game              = "Jeu / Concours / Tournoi"
    SchoolHelp        = "Soutien scolaire"
    StreetPerformance = "Arts de la rue"
    Other             = "Autres"
    BookReading       = "Lecture"
    CircusAndMagic    = "Cirque / Magie"
    DancePerformance  = "Danse"
    Comedy            = "Humour / Café-théâtre"
    Concert           = "Concert"
    Combo             = "Pluridisciplinaire"
    Youth             = "Spectacle Jeunesse"
    Musical           = "Spectacle Musical / Cabaret / Opérette"
    Theater           = "Théâtre"
    GuidedVisit       = "Visite guidée : Exposition, Musée, Monument..."
    FreeVisit         = "Visite libre : Exposition, Musée, Monument..."


app.model.EventType = EventType

db = app.db


class Event(app.model.PcObject,
            db.Model,
            app.model.DeactivableMixin,
            app.model.ExtraDataMixin,
            app.model.HasThumbMixin,
            app.model.ProvidableMixin
            ):
    id = db.Column(db.BigInteger,
                   primary_key=True)

    type = db.Column(db.String(50),
                     nullable=True)

    name = db.Column(db.String(140), nullable=False)

    description = db.Column(db.Text, nullable=True)

    conditions = db.Column(db.String(120),
                           nullable=True)

    ageMin = db.Column(db.Integer,
                       nullable=True)
    ageMax = db.Column(db.Integer,
                       nullable=True)
    #TODO (from schema.org)
    #doorTime (datetime)
    #eventStatus
    #isAccessibleForFree (boolean)
    #typicalAgeRange → = $ageMin-$ageMax

    accessibility = db.Column(db.Binary(1),
                              nullable=False,
                              default=bytes([0]))

    mediaUrls = db.Column(ARRAY(db.String(220)),
                          nullable=False,
                          default=[])

    durationMinutes = db.Column(db.Integer,
                                nullable=False)

    isNational = db.Column(db.Boolean,
                           server_default=false(),
                           default=False,
                           nullable=False)


Event.__ts_vector__ = create_tsvector(
    cast(coalesce(Event.name, ''), TEXT)
)

Event.__table_args__ = (
    Index(
        'idx_event_fts',
        Event.__ts_vector__,
        postgresql_using='gin'
    ),
)


app.model.Event = Event
