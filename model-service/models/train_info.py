from datetime import datetime


class TrainInfo:
    def __init__(self, idInfo=None, epoch=None, learningRate=None, batchSize=None,
                 mae=None, mse=None, trainingLosts=None, accuracy=None,
                 timeTrain=None, trainDuration=None):
        self.idInfo = idInfo
        self.epoch = epoch
        self.learningRate = learningRate
        self.batchSize = batchSize
        self.mae = mae
        self.mse = mse
        self.trainingLosts = trainingLosts if trainingLosts else []
        self.accuracy = accuracy
        self.timeTrain = timeTrain
        self.trainDuration = trainDuration

    def to_dict(self):
        train_info_dict = {
            'idInfo': self.idInfo,
            'epoch': self.epoch,
            'learningRate': self.learningRate,
            'batchSize': self.batchSize,
            'mae': self.mae,
            'mse': self.mse,
            'accuracy': self.accuracy,
            'timeTrain': self.timeTrain,
            'trainDuration': self.trainDuration
        }

        if self.trainingLosts:
            train_info_dict['trainingLosts'] = [
                lost.to_dict() if hasattr(lost, 'to_dict') else lost
                for lost in self.trainingLosts
            ]

        return train_info_dict

    @classmethod
    def from_dict(cls, data):
        from .training_lost import TrainingLost

        train_info = cls()

        train_info.idInfo = data.get('idInfo')
        train_info.epoch = data.get('epoch')
        train_info.learningRate = data.get('learningRate')
        train_info.batchSize = data.get('batchSize')
        train_info.mae = data.get('mae')
        train_info.mse = data.get('mse')
        train_info.accuracy = data.get('accuracy')
        train_info.timeTrain = data.get('timeTrain')
        train_info.trainDuration = data.get('trainDuration')

        training_losts_data = data.get('trainingLosts')
        if training_losts_data:
            train_info.trainingLosts = [
                TrainingLost.from_dict(lost) if isinstance(
                    lost, dict) else lost
                for lost in training_losts_data
            ]

        return train_info
