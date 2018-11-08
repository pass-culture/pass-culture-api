from models.pc_object import PcObject
from utils.logger import logger
from utils.test_utils import create_deposit

def create_scratch_deposits(users_by_name):

    deposits_by_name = {}

    deposits_by_name['jeune 93 / public / 500'] = create_deposit(
        amount=500,
        source="public",
        user=users_by_name['jeune 93']
    )

    return deposits_by_name
