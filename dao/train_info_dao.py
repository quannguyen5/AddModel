import logging
from utils.db_util import DatabaseUtil
from models.train_info import TrainInfo


class TrainInfoDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM TrainInfo"

            rows = self.db_util.execute_query(query, fetchall=True)

            train_infos = []
            for row in rows:
                train_info = TrainInfo(
                    idInfo=row['idInfo'],
                    epoch=row['epoch'],
                    learningRate=row['learningRate'],
                    batchSize=row['batchSize'],
                    mae=row['mae'],
                    mse=row['mse'],
                    trainDuration=row['trainDuration'],
                    accuracy=row['accuracy'],
                    timeTrain=row['timeTrain']
                )

                # Lấy danh sách TrainingLost
                from dao.training_lost_dao import TrainingLostDAO
                training_lost_dao = TrainingLostDAO()
                train_info.trainingLosts = training_lost_dao.get_by_train_info_id(
                    row['idInfo'])

                train_infos.append(train_info)

            return train_infos
        except Exception as e:
            logging.error(f"Error in TrainInfoDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, train_info_id):
        try:
            query = "SELECT * FROM TrainInfo WHERE idInfo = %s"

            row = self.db_util.execute_query(
                query, (train_info_id,), fetchone=True)

            if not row:
                return None

            train_info = TrainInfo(
                idInfo=row['idInfo'],
                epoch=row['epoch'],
                learningRate=row['learningRate'],
                batchSize=row['batchSize'],
                mae=row['mae'],
                mse=row['mse'],
                trainDuration=row['trainDuration'],
                accuracy=row['accuracy'],
                timeTrain=row['timeTrain']
            )

            # Lấy danh sách TrainingLost
            from dao.training_lost_dao import TrainingLostDAO
            training_lost_dao = TrainingLostDAO()
            train_info.trainingLosts = training_lost_dao.get_by_train_info_id(
                row['idInfo'])

            return train_info
        except Exception as e:
            logging.error(f"Error in TrainInfoDAO.get_by_id: {str(e)}")
            raise

    def create(self, train_info):
        try:
            query = """
                INSERT INTO TrainInfo (epoch, learningRate, batchSize, mae, mse, trainDuration, accuracy, timeTrain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                train_info.epoch,
                train_info.learningRate,
                train_info.batchSize,
                train_info.mae,
                train_info.mse,
                train_info.trainDuration,
                train_info.accuracy,
                train_info.timeTrain
            )

            train_info_id = self.db_util.execute_query(
                query, params, commit=True)

            # Nếu có TrainingLosts, tạo các TrainingLost
            if train_info.trainingLosts:
                from dao.training_lost_dao import TrainingLostDAO
                training_lost_dao = TrainingLostDAO()

                for training_lost in train_info.trainingLosts:
                    training_lost.trainInfoId = train_info_id
                    training_lost_dao.create(training_lost)

            return train_info_id
        except Exception as e:
            logging.error(f"Error in TrainInfoDAO.create: {str(e)}")
            raise

    def update(self, train_info):
        try:
            query = """
                UPDATE TrainInfo
                SET epoch = %s, learningRate = %s, batchSize = %s, mae = %s, 
                    mse = %s, trainDuration = %s, accuracy = %s, timeTrain = %s
                WHERE idInfo = %s
            """

            params = (
                train_info.epoch,
                train_info.learningRate,
                train_info.batchSize,
                train_info.mae,
                train_info.mse,
                train_info.trainDuration,
                train_info.accuracy,
                train_info.timeTrain,
                train_info.idInfo
            )

            self.db_util.execute_query(query, params, commit=True)

            # Cập nhật các TrainingLost
            if train_info.trainingLosts:
                from dao.training_lost_dao import TrainingLostDAO
                training_lost_dao = TrainingLostDAO()

                # Xóa tất cả các TrainingLost cũ
                training_lost_dao.delete_by_train_info_id(train_info.idInfo)

                # Tạo lại các TrainingLost mới
                for training_lost in train_info.trainingLosts:
                    training_lost.trainInfoId = train_info.idInfo
                    training_lost_dao.create(training_lost)

            return True
        except Exception as e:
            logging.error(f"Error in TrainInfoDAO.update: {str(e)}")
            raise

    def delete(self, train_info_id):
        try:
            # Xóa tất cả các TrainingLost liên quan
            from dao.training_lost_dao import TrainingLostDAO
            training_lost_dao = TrainingLostDAO()
            training_lost_dao.delete_by_train_info_id(train_info_id)

            # Xóa TrainInfo
            query = "DELETE FROM TrainInfo WHERE idInfo = %s"
            self.db_util.execute_query(query, (train_info_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in TrainInfoDAO.delete: {str(e)}")
            raise
