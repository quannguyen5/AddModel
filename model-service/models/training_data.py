from datetime import datetime


class TrainingData:
    def __init__(self, idTrainingData=None, timeUpdate=None, description=None,
                 modelId=None, fraudTemplateId=None):
        self.idTrainingData = idTrainingData
        self.timeUpdate = timeUpdate if timeUpdate else datetime.now()
        self.description = description
        self.modelId = modelId
        self.fraudTemplateId = fraudTemplateId

    def to_dict(self):
        return {
            'idTrainingData': self.idTrainingData,
            'timeUpdate': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else str(self.timeUpdate),
            'description': self.description,
            'modelId': self.modelId,
            'fraudTemplateId': self.fraudTemplateId
        }
