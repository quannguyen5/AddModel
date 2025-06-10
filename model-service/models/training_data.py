from datetime import datetime


class TrainingData:
    def __init__(self, idTrainingData=None, timeUpdate=None, description=None,
                 model=None, fraudTemplate=None, modelId=None, fraudTemplateId=None):
        self.idTrainingData = idTrainingData
        self.timeUpdate = timeUpdate if timeUpdate else datetime.now()
        self.description = description
        self.model = model
        self.fraudTemplate = fraudTemplate
        self.modelId = modelId
        self.fraudTemplateId = fraudTemplateId

    def to_dict(self):
        training_data_dict = {
            'idTrainingData': self.idTrainingData,
            'timeUpdate': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else self.timeUpdate,
            'description': self.description,
            'modelId': self.modelId,
            'fraudTemplateId': self.fraudTemplateId
        }

        if self.model:
            training_data_dict['model'] = self.model.to_dict() if hasattr(
                self.model, 'to_dict') else self.model

        if self.fraudTemplate:
            training_data_dict['fraudTemplate'] = self.fraudTemplate.to_dict() if hasattr(
                self.fraudTemplate, 'to_dict') else self.fraudTemplate

        return training_data_dict

    @classmethod
    def from_dict(cls, data):
        from .model import Model
        from .fraud_template import FraudTemplate

        training_data = cls()

        training_data.idTrainingData = data.get('idTrainingData')

        time_update = data.get('timeUpdate')
        if time_update and isinstance(time_update, str):
            try:
                training_data.timeUpdate = datetime.strptime(
                    time_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                training_data.timeUpdate = time_update
        else:
            training_data.timeUpdate = time_update

        training_data.description = data.get('description')
        training_data.modelId = data.get('modelId')
        training_data.fraudTemplateId = data.get('fraudTemplateId')

        model_data = data.get('model')
        if model_data:
            if isinstance(model_data, dict):
                training_data.model = Model.from_dict(model_data)
            else:
                training_data.model = model_data

        fraud_template_data = data.get('fraudTemplate')
        if fraud_template_data:
            if isinstance(fraud_template_data, dict):
                training_data.fraudTemplate = FraudTemplate.from_dict(
                    fraud_template_data)
            else:
                training_data.fraudTemplate = fraud_template_data

        return training_data
