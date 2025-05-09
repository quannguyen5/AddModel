# models/fraud.py

class Fraud:
    def __init__(self, idFraud=None, fraud=None, detectResultId=None):
        self.idFraud = idFraud
        self.fraud = fraud
        self.detectResultId = detectResultId

    def to_dict(self):
        return {
            'idFraud': self.idFraud,
            'fraud': self.fraud,
            'detectResultId': self.detectResultId
        }

    @classmethod
    def from_dict(cls, data):
        fraud = cls()
        fraud.idFraud = data.get('idFraud')
        fraud.fraud = data.get('fraud')
        fraud.detectResultId = data.get('detectResultId')
        return fraud