from pcapi.routes.apis import public_api
from pcapi.utils.health_checker import check_database_connection
from pcapi.utils.health_checker import read_version_from_file


@public_api.route("/health/api", methods=["GET"])
def health_api():
    output = read_version_from_file()
    return output, 200


@public_api.route("/health/database", methods=["GET"])
def health_database():
    database_working = check_database_connection()
    return_code = 200 if database_working else 500
    output = read_version_from_file()
    return output, return_code


@public_api.route('/check/transactions', methods=['POST'])
def check_transactions():
    import uuid
    from flask import request
    from pcapi.models import UserSession
    from pcapi.repository import repository

    s = UserSession()
    s.userId = 1
    s.uuid = uuid.uuid4()
    # The code typically calls `repository.save()` for every addition or update.
    repository.save(s)

    # If an error is raised, we should not commit the transaction. And yet we do...
    if 'raise' in request.args:
        raise ValueError("an horrible error occurs, let's rollback, shall we?")

    return 'OK', 200
