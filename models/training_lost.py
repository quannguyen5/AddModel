class TrainingLost:
    def __init__(self, idTrainingLost=None, epoch=None, lost=None, trainInfoId=None):
        self.idTrainingLost = idTrainingLost
        self.epoch = epoch
        self.lost = lost
        self.trainInfoId = trainInfoId

    def to_dict(self):
        return {
            'idTrainingLost': self.idTrainingLost,
            'epoch': self.epoch,
            'lost': self.lost,
            'trainInfoId': self.trainInfoId
        }

    @classmethod
    def from_dict(cls, data):
        training_lost = cls()

        training_lost.idTrainingLost = data.get('idTrainingLost')
        training_lost.epoch = data.get('epoch')
        training_lost.lost = data.get('lost')
        training_lost.trainInfoId = data.get('trainInfoId')

        return training_lost
