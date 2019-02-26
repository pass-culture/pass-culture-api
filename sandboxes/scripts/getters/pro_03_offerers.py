from models.offerer import Offerer
from models.user_offerer import UserOfferer
from models.user import User
from repository.user_queries import filter_users_with_at_least_one_validated_offerer_validated_user_offerer, \
                                    filter_users_with_at_least_one_validated_offerer_not_validated_user_offerer, \
                                    filter_users_with_at_least_one_not_validated_offerer_validated_user_offerer
from sandboxes.scripts.utils.helpers import get_user_helper, get_offerer_helper

def get_existing_pro_validated_user_with_validated_offerer_validated_user_offerer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_validated_user_offerer(query)
    user = query.first()

    offerer = [
        uo.offerer for uo in user.UserOfferers
        if uo.validationToken == None \
        and uo.offerer.validationToken == None
    ][0]

    return {
        "offerer": get_offerer_helper(offerer),
        "user": get_user_helper(user)
    }

def get_existing_pro_validated_user_with_not_validated_offerer_validated_user_offerer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_not_validated_offerer_validated_user_offerer(query)
    user = query.first()

    offerer = [
        uo.offerer for uo in user.UserOfferers
        if uo.validationToken == None \
        and uo.offerer.validationToken != None
    ][0]

    return {
        "offerer": get_offerer_helper(offerer),
        "user": get_user_helper(user)
    }

def get_existing_pro_validated_user_with_validated_offerer_not_validated_user_offerer():
    query = User.query.filter(User.validationToken == None)
    query = filter_users_with_at_least_one_validated_offerer_not_validated_user_offerer(query)
    user = query.first()

    offerer = [
        uo.offerer for uo in user.UserOfferers
        if uo.validationToken != None \
        and uo.offerer.validationToken == None
    ][0]

    return {
        "offerer": get_offerer_helper(offerer),
        "user": get_user_helper(user)
    }

def get_existing_pro_validated_user_with_not_validated_offerer_validated_user_offerer_and_validated_offerer_not_validated_user_offerer():
    query = User.query.filter(User.validationToken == None)
    first_query = filter_users_with_at_least_one_not_validated_offerer_validated_user_offerer(query)
    second_query = filter_users_with_at_least_one_validated_offerer_not_validated_user_offerer(query)
    query = first_query.union_all(second_query)
    user = query.first()

    not_validated_offerer = [
        uo.offerer for uo in user.UserOfferers
        if uo.offerer.validationToken != None \
        and uo.validationToken == None
    ][0]

    validated_offerer = [
        uo.offerer for uo in user.UserOfferers
        if uo.offerer.validationToken == None \
        and uo.validationToken != None
    ][0]

    return {
        "notValidatedOfferer": get_offerer_helper(not_validated_offerer),
        "user": get_user_helper(user),
        "validatedOfferer": get_offerer_helper(validated_offerer)
    }
