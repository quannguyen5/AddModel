from enum import Enum


class ModelType(Enum):
    """Enum cho các loại mô hình"""
    HumanDetection = "Human Detection"
    FraudDetection = "Fraud Detection"

    @classmethod
    def get_all_values(cls):
        """Trả về tất cả các giá trị của enum"""
        return [e.value for e in cls]


class TypeLabel(Enum):
    """Enum cho các loại nhãn"""
    HumanDetect = "HumanDetect"
    literal = "literal"

    @classmethod
    def get_all_values(cls):
        """Trả về tất cả các giá trị của enum"""
        return [e.value for e in cls]
