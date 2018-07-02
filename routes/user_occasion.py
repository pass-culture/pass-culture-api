""" user mediation """
from flask import current_app as app, jsonify, request

from utils.rest import load_or_404,\
                       update

UserOccasion = app.model.UserOccasion

@app.route('/userOccasions', methods=['PUT'])
def put_user_occasion():
    user_occasions = []
    for user_occasion_dict in request.json:
        user_occasion = load_or_404(UserOccasion, user_occasion_dict['id'])
        update(user_occasion, user_occasion_dict)
        app.model.PcObject.check_and_save(user_occasion)
        user_occasions.append(user_occasion)
    return jsonify(
        [
            user_occasion._asdict() for user_occasion in user_occasions
        ]
    ), 201
