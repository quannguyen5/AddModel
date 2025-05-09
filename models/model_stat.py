from dao.phase_detection_dao import PhaseDetectionDAO
from models.model import Model
from dao.fraud_dao import FraudDAO


class ModelStat(Model()):
    def __init__(self):
        self.usages = get_usage()
        self.totalFraud = get_total_fraud()
        self.totalUse = get_total_use()

    def get_total_fraud():
        count = 0
        for use in usages:
            for res in use.result:
                count += len(res.frauds)
        return count

    def get_total_use():
        return len(self.usages)

    def get_usage():
        phase_dao = PhaseDetectionDAO()
        return phase_dao.get_by_model_id(self.idModel)

    def to_dict():
        pass
