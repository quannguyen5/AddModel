import logging
from utils.db_util import DatabaseUtil
from models.training_lost import TrainingLost


class TrainingLostDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM TrainingLost"

            rows = self.db_util.execute_query(query, fetchall=True)

            training_losts = []
            for row in rows:
                training_lost = TrainingLost(
                    idTrainingLost=row['idTrainingLost'],
                    epoch=row['epoch'],
                    lost=row['lost'],
                    trainInfoId=row['trainInfoId']
                )
                training_losts.append(training_lost)

            return training_losts
        except Exception as e:
            logging.error(f"Error in TrainingLostDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, training_lost_id):
        try:
            query = "SELECT * FROM TrainingLost WHERE idTrainingLost = %s"

            row = self.db_util.execute_query(
                query, (training_lost_id,), fetchone=True)

            if not row:
                return None

            training_lost = TrainingLost(
                idTrainingLost=row['idTrainingLost'],
                epoch=row['epoch'],
                lost=row['lost'],
                trainInfoId=row['trainInfoId']
            )

            return training_lost
        except Exception as e:
            logging.error(f"Error in TrainingLostDAO.get_by_id: {str(e)}")
            raise

    def get_by_train_info_id(self, train_info_id):
        try:
            query = "SELECT * FROM TrainingLost WHERE trainInfoId = %s ORDER BY epoch"

            rows = self.db_util.execute_query(
                query, (train_info_id,), fetchall=True)

            training_losts = []
            for row in rows:
                training_lost = TrainingLost(
                    idTrainingLost=row['idTrainingLost'],
                    epoch=row['epoch'],
                    lost=row['lost'],
                    trainInfoId=row['trainInfoId']
                )
                training_losts.append(training_lost)

            return training_losts
        except Exception as e:
            logging.error(
                f"Error in TrainingLostDAO.get_by_train_info_id: {str(e)}")
            raise

    def create(self, training_lost):
        try:
            query = """
                INSERT INTO TrainingLost (epoch, lost, trainInfoId)
                VALUES (%s, %s, %s)
            """

            params = (
                training_lost.epoch,
                training_lost.lost,
                training_lost.trainInfoId
            )

            training_lost_id = self.db_util.execute_query(
                query, params, commit=True)

            return training_lost_id
        except Exception as e:
            logging.error(f"Error in TrainingLostDAO.create: {str(e)}")
            raise

    def update(self, training_lost):
        try:
            query = """
                UPDATE TrainingLost
                SET epoch = %s, lost = %s, trainInfoId = %s
                WHERE idTrainingLost = %s
            """

            params = (
                training_lost.epoch,
                training_lost.lost,
                training_lost.trainInfoId,
                training_lost.idTrainingLost
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in TrainingLostDAO.update: {str(e)}")
            raise

    def delete(self, training_lost_id):
        try:
            query = "DELETE FROM TrainingLost WHERE idTrainingLost = %s"
            self.db_util.execute_query(query, (training_lost_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in TrainingLostDAO.delete: {str(e)}")
            raise

    def delete_by_train_info_id(self, train_info_id):
        try:
            query = "DELETE FROM TrainingLost WHERE trainInfoId = %s"
            self.db_util.execute_query(query, (train_info_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in TrainingLostDAO.delete_by_train_info_id: {str(e)}")
            raise
