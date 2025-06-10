from enum import Enum


class ModelType(Enum):
    HumanDetection = "HumanDetection"
    FraudDetection = "FraudDetection"

    @classmethod
    def get_all_values(cls):
        return [e.value for e in cls]


class TypeLabel(Enum):
    HumanDetect = "HumanDetect"
    literal = "literal"

    @classmethod
    def get_all_values(cls):
        return [e.value for e in cls]
