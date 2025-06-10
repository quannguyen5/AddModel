from datetime import datetime


class Model:
    def __init__(self, idModel=None, modelName=None, modelType=None, version=None,
                 description=None, lastUpdate=None, trainInfo=None):
        self.idModel = idModel
        self.modelName = modelName
        self.modelType = modelType
        self.version = version
        self.description = description
        self.lastUpdate = lastUpdate if lastUpdate else datetime.now()
        self.trainInfo = trainInfo

    def to_dict(self):
        result = {
            'idModel': self.idModel,
            'modelName': self.modelName,
            'modelType': self.modelType,
            'version': self.version,
            'description': self.description,
            'lastUpdate': self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.lastUpdate, datetime) else str(self.lastUpdate),
            'accuracy': self.trainInfo.accuracy if self.trainInfo else 0.0
        }

        if self.trainInfo:
            result['trainInfo'] = self.trainInfo.to_dict()

        return result
