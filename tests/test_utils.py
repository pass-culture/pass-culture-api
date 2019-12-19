from models.feature import Feature, FeatureToggle
from models.pc_object import PcObject


def get_occurrence_short_name(concatened_names_with_a_date):
    splitted_names = concatened_names_with_a_date.split(' / ')
    if len(splitted_names) > 0:
        return splitted_names[0]
    else:
        return None


def get_price_by_short_name(occurrence_short_name=None):
    if occurrence_short_name is None:
        return 0
    else:
        return sum(map(ord, occurrence_short_name)) % 50


def deactivate_feature(feature_toggle: FeatureToggle):
    feature = Feature.query.filter_by(name=feature_toggle.name).one()
    feature.isActive = False
    PcObject.save(feature)
