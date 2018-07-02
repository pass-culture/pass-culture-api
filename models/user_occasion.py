from flask import current_app as app

db = app.db


class UserOccasion(app.model.PcObject,
                   db.Model):
    userId = db.Column(db.BigInteger,
                       db.ForeignKey('user.id'),
                       primary_key=True)

    user = db.relationship(lambda: app.model.User,
                           foreign_keys=[userId],
                           backref=db.backref("userOccasions"))

    occasionId = db.Column(db.BigInteger,
                           db.ForeignKey('occasion.id'),
                           primary_key=True)

    occasion = db.relationship(lambda: app.model.Occasion,
                               foreign_keys=[occasionId],
                               backref=db.backref("userOccasions"))

    dateRead = db.Column(db.DateTime,
                         nullable=True,
                         index=True)


app.model.UserOccasion = UserOccasion
