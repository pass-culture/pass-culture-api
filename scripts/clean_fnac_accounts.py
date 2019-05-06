from typing import List

from models import User, Offerer, PcObject, UserOfferer


def find_all_fnac_users():
    is_fnac_email = User.email.endswith('@fnacdarty.com') | User.email.endswith('@fnac.com')
    return User.query.filter(is_fnac_email).all()


def find_all_fnac_offerers():
    all_fnac_siren = ['350127460', '434001954', '334473352', '343282380']
    is_fnac_offerer = Offerer.siren.in_(all_fnac_siren)
    return Offerer.query.filter(is_fnac_offerer).all()


def create_all_possible_user_offerers(users: List[User], offerers: List[Offerer]):
    for user in users:
        for offerer in offerers:
            if offerer not in user.offerers:
                user.offerers.append(offerer)
    PcObject.check_and_save(*users)


def clear_all_existing_user_offerers(siren: str):
    offerer = Offerer.query.filter_by(siren=siren).one()
    offerer.users = []
    PcObject.check_and_save(offerer)