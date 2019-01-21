from models import UserOfferer, User


def find_user_offerer_email(user_offerer_id):
    return UserOfferer.query \
        .filter_by(id=user_offerer_id) \
        .join(User) \
        .with_entities(User.email) \
        .first()[0]


def filter_query_where_user_is_user_offerer_and_is_validated(query, user):
    return query \
        .join(UserOfferer) \
        .filter_by(user=user) \
        .filter_by(validationToken=None) \
        .reset_joinpoint()


def filter_query_where_user_is_user_offerer_and_is_not_validated(query, user):
    return query \
        .join(UserOfferer) \
        .filter_by(user=user) \
        .filter(UserOfferer.validationToken != None)


def count_user_offerers_by_offerer(offerer):
    return UserOfferer.query \
        .filter_by(offerer=offerer) \
        .count()


def find_first_by_user_id(user_id):
    return UserOfferer.query.filter_by(userId=user_id).first()
