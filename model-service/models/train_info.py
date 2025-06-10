class TrainInfo:
    def __init__(self, idInfo=None, epoch=None, learningRate=None, batchSize=None,
                 mae=None, mse=None, trainDuration=None, accuracy=None, timeTrain=None):
        self.idInfo = idInfo
        self.epoch = epoch
        self.learningRate = learningRate
        self.batchSize = batchSize
        self.mae = mae
        self.mse = mse
        self.trainDuration = trainDuration
        self.accuracy = accuracy
        self.timeTrain = timeTrain

    def to_dict(self):
        return {
            'idInfo': self.idInfo,
            'epoch': self.epoch,
            'learningRate': self.learningRate,
            'batchSize': self.batchSize,
            'mae': self.mae,
            'mse': self.mse,
            'trainDuration': self.trainDuration,
            'accuracy': self.accuracy,
            'timeTrain': self.timeTrain
        }
