from tests.test_utils import create_api_key
from utils.logger import logger

PROS_COUNT = 1
API_KEYS_VALUES = [
    "4UQYGEFQUYRYP96YY48ACEXYXY7Q9EL9JE4EHEXUWA3E497YSYSMFEFAAULQP4LY",
    "HQDE6MV42UHYQEKACA89M9U4QE9AZYFEYELU3QVQ7MFAWM3UNQBAJA7MWYMUCYTY",
    "PQAY24CY9YG4ZMX4D95AUUTAA9LETQMA2YC4P9NYK4FUCYNUCAYAZ4XAJEPM9QKU",
    "49JY9AREJUYYRE9EGE8ENQG44AHYLADUF49QUQZ9CM3Q94SY8EUAKMCUPAXUS43A",
    "64Q4X4BMEECYZ45E89FYEME4UMS9F4BMKYCYN9EMBAMEDMLEBA74397A2AFU49Q4",
    "NA5Q2A6YA4LUJ9FEMET4QM4QB4QMJYCQAQ5MSMTUP9QQTMGEV9SA4AUYKMKY7USA",
    "MEHMD4HQMQ7QBES9REJERYB95M7MKUHQ8QCAZ4649URM7A9UJ4SAR98QXEGYTUFM",
    "M459PYFYLADQM4G44Y9UQAJYCYDEYME48QBQJE6ML48MMABAB95AAUPYVUG4P4E4",
    "TAUQ6UGMKEDQ84YQX97MLYXEAYDEBYR429GUUEGAMMTMBUZYVQ5Q3UE99A8EAUWM",
    "MAX98A9UTUVQEQ3MS9ZY2A5924CMBMZQ5EFM3AA4RUPYTUB99YFA4AF4RU6EJYXM",
    "894QN4UA7MFAFAS944XEF9799AHQDMVAXU5YV9AMZ48949TE7U6UKULQGUQAEM9A",
    "3A6M3YHM9UXQ84FA5QLMPE9MFEEAD4E9A49U7AXMMMFMFM3YKUPM7QW9X95U39RQ",
    "7MGQLYGQAMZMVEK9GUSQNMEYL9Z4Q4LYBY3AJ989C924897EZQ6MFME4LEUMXQ3E"
]

def create_industrial_pro_users_api_keys(offerers_by_name):
    logger.info('create_industrial_pro_users_api_keys')
    n = 0
    for offerer in offerers_by_name.items():
        create_api_key(offerer[1], API_KEYS_VALUES[n])
        n += 1

    logger.info('created {} offerers with api key'.format(len(offerers_by_name)))

