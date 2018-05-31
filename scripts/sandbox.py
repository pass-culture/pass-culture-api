""" sandbox script """
#https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pprint import pprint
import traceback
from flask import current_app as app

from utils.mock import set_from_mock

@app.manager.command
def sandbox():
    try:
        do_sandbox()
    except Exception as e:
        print('ERROR: '+str(e))
        traceback.print_tb(e.__traceback__)
        pprint(vars(e))


def do_sandbox():
    check_and_save = app.model.PcObject.check_and_save
    model = app.model

    # un jeune qui veut profiter du pass-culture
    client_user = model.User()
    client_user.publicName = "Utilisateur test jeune"
    client_user.account = 100
    client_user.email = "pctest.jeune@btmx.fr"
    client_user.departementCode = "93"
    client_user.setPassword("pctestjeune")
    check_and_save(client_user)
    set_from_mock("thumbs", client_user, 1)

    # un acteur culturel qui peut jouer a rajouter des offres partout
    admin_user = model.User()
    admin_user.publicName = "Utilisateur test admin"
    admin_user.email = "pctest.admin@btmx.fr"
    admin_user.departementCode = "93"
    admin_user.setPassword("pctestadmin")
    check_and_save(admin_user)
    set_from_mock("thumbs", admin_user, 2)

    for offerer in model.Offerer.query.all():
        userOfferer = model.UserOfferer()
        userOfferer.rights = "admin"
        userOfferer.user = admin_user
        userOfferer.offerer = offerer
        check_and_save(userOfferer)
