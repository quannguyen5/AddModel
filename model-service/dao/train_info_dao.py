from utils.db_util import DatabaseUtil
from models.train_info import TrainInfo


class TrainInfoDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_by_id(self, train_info_id):
        try:
            query = "SELECT * FROM TrainInfo WHERE idInfo = %s"
            row = self.db_util.execute_query(
                query, (train_info_id,), fetchone=True)
            return self._row_to_train_info(row) if row else None
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise

    def create(self, train_info):
        try:
            query = """
            INSERT INTO TrainInfo (epoch, learningRate, batchSize, mae, mse, trainDuration, accuracy, timeTrain)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (train_info.epoch, train_info.learningRate, train_info.batchSize,
                      train_info.mae, train_info.mse, train_info.trainDuration,
                      train_info.accuracy, train_info.timeTrain)

            return self.db_util.execute_query(query, params, commit=True)
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def _row_to_train_info(self, row):
        return TrainInfo(
            idInfo=row['idInfo'],
            epoch=row['epoch'],
            learningRate=row['learningRate'],
            batchSize=row['batchSize'],
            mae=row.get('mae'),
            mse=row.get('mse'),
            trainDuration=row.get('trainDuration'),
            accuracy=row.get('accuracy'),
            timeTrain=row.get('timeTrain')
        )
