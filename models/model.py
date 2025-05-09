from datetime import datetime
from utils.enums import ModelType
from .train_info import TrainInfo


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

    def get_fraud_templates(self):
        pass

    def get_train_info(self):
        return self.trainInfo

    def to_dict(self):
        model_dict = {
            'idModel': self.idModel,
            'modelName': self.modelName,
            'modelType': self.modelType.value if isinstance(self.modelType, ModelType) else self.modelType,
            'version': self.version,
            'description': self.description,
            'lastUpdate': self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.lastUpdate, datetime) else self.lastUpdate,
            'accuracy': self.trainInfo.accuracy
        }

        if self.trainInfo:
            model_dict['trainInfo'] = self.trainInfo.to_dict() if hasattr(
                self.trainInfo, 'to_dict') else self.trainInfo

        return model_dict

    @classmethod
    def from_dict(cls, data):
        model = cls()

        model.idModel = data.get('idModel')
        model.modelName = data.get('modelName')

        model_type = data.get('modelType')
        if model_type:
            try:
                model.modelType = ModelType(model_type)
            except ValueError:
                model.modelType = model_type

        model.version = data.get('version')
        model.description = data.get('description')

        last_update = data.get('lastUpdate')
        if last_update and isinstance(last_update, str):
            try:
                model.lastUpdate = datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                model.lastUpdate = last_update
        else:
            model.lastUpdate = last_update

        train_info_data = data.get('trainInfo')
        if train_info_data:
            if isinstance(train_info_data, dict):
                model.trainInfo = TrainInfo.from_dict(train_info_data)
            else:
                model.trainInfo = train_info_data

        return model
