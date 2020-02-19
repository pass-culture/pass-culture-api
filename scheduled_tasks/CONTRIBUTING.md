# Package `scheduled_tasks`

Les modules de ce package contiennent des tâches à exécution régulières.

## Do
Ces fonctions doivent être regroupées par domaine fonctionel.
Afin que ces fonctions soit exécuté

Par exemple :
```python
@app.route("/users/current", methods=["GET"])
@login_required
def get_profile():
    user = as_dict(current_user, includes=USER_INCLUDES)
    user['expenses'] = get_expenses(current_user.userBookings)
    return jsonify(user), 200
```
