import logging
from utils.db_util import DatabaseUtil
from models.training_data import TrainingData
from datetime import datetime


class TrainingDataDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM TrainingData"

            rows = self.db_util.execute_query(query, fetchall=True)

            training_data_list = []
            for row in rows:
                training_data = TrainingData(
                    idTrainingData=row['idTrainingData'],
                    timeUpdate=row['timeUpdate'],
                    description=row['description'],
                    modelId=row['modelId'],
                    fraudTemplateId=row['fraudTemplateId']
                )

                # Lấy thông tin Model và FraudTemplate
                from dao.model_dao import ModelDAO
                from dao.fraud_template_dao import FraudTemplateDAO

                model_dao = ModelDAO()
                fraud_template_dao = FraudTemplateDAO()

                training_data.model = model_dao.get_by_id(row['modelId'])
                training_data.fraudTemplate = fraud_template_dao.get_by_id(
                    row['fraudTemplateId'])

                training_data_list.append(training_data)

            return training_data_list
        except Exception as e:
            logging.error(f"Error in TrainingDataDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, training_data_id):
        try:
            query = "SELECT * FROM TrainingData WHERE idTrainingData = %s"

            row = self.db_util.execute_query(
                query, (training_data_id,), fetchone=True)

            if not row:
                return None

            training_data = TrainingData(
                idTrainingData=row['idTrainingData'],
                timeUpdate=row['timeUpdate'],
                description=row['description'],
                modelId=row['modelId'],
                fraudTemplateId=row['fraudTemplateId']
            )

            # Lấy thông tin Model và FraudTemplate
            from dao.model_dao import ModelDAO
            from dao.fraud_template_dao import FraudTemplateDAO

            model_dao = ModelDAO()
            fraud_template_dao = FraudTemplateDAO()

            training_data.model = model_dao.get_by_id(row['modelId'])
            training_data.fraudTemplate = fraud_template_dao.get_by_id(
                row['fraudTemplateId'])

            return training_data
        except Exception as e:
            logging.error(f"Error in TrainingDataDAO.get_by_id: {str(e)}")
            raise

    def get_by_model_id(self, model_id):
        try:
            query = "SELECT * FROM TrainingData WHERE modelId = %s"

            rows = self.db_util.execute_query(
                query, (model_id,), fetchall=True)

            training_data_list = []
            for row in rows:
                training_data = TrainingData(
                    idTrainingData=row['idTrainingData'],
                    timeUpdate=row['timeUpdate'],
                    description=row['description'],
                    modelId=row['modelId'],
                    fraudTemplateId=row['fraudTemplateId']
                )

                # Lấy thông tin FraudTemplate
                from dao.fraud_template_dao import FraudTemplateDAO
                fraud_template_dao = FraudTemplateDAO()
                training_data.fraudTemplate = fraud_template_dao.get_by_id(
                    row['fraudTemplateId'])

                training_data_list.append(training_data)

            return training_data_list
        except Exception as e:
            logging.error(
                f"Error in TrainingDataDAO.get_by_model_id: {str(e)}")
            raise

    def get_by_template_id(self, template_id):
        try:
            query = "SELECT * FROM TrainingData WHERE fraudTemplateId = %s"

            rows = self.db_util.execute_query(
                query, (template_id,), fetchall=True)

            training_data_list = []
            for row in rows:
                training_data = TrainingData(
                    idTrainingData=row['idTrainingData'],
                    timeUpdate=row['timeUpdate'],
                    description=row['description'],
                    modelId=row['modelId'],
                    fraudTemplateId=row['fraudTemplateId']
                )

                # Lấy thông tin Model
                from dao.model_dao import ModelDAO
                model_dao = ModelDAO()
                training_data.model = model_dao.get_by_id(row['modelId'])

                training_data_list.append(training_data)

            return training_data_list
        except Exception as e:
            logging.error(
                f"Error in TrainingDataDAO.get_by_template_id: {str(e)}")
            raise

    def create(self, training_data):
        try:
            query = """
                INSERT INTO TrainingData (timeUpdate, description, modelId, fraudTemplateId)
                VALUES (%s, %s, %s, %s)
            """

            time_update = training_data.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                time_update,
                training_data.description,
                training_data.modelId,
                training_data.fraudTemplateId
            )

            training_data_id = self.db_util.execute_query(
                query, params, commit=True)

            return training_data_id
        except Exception as e:
            logging.error(f"Error in TrainingDataDAO.create: {str(e)}")
            raise

    def update(self, training_data):
        try:
            query = """
                UPDATE TrainingData
                SET timeUpdate = %s, description = %s, modelId = %s, fraudTemplateId = %s
                WHERE idTrainingData = %s
            """

            time_update = training_data.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                time_update,
                training_data.description,
                training_data.modelId,
                training_data.fraudTemplateId,
                training_data.idTrainingData
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in TrainingDataDAO.update: {str(e)}")
            raise

    def delete(self, training_data_id):
        try:
            query = "DELETE FROM TrainingData WHERE idTrainingData = %s"
            self.db_util.execute_query(query, (training_data_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in TrainingDataDAO.delete: {str(e)}")
            raise

    def delete_by_model_id(self, model_id):
        try:
            query = "DELETE FROM TrainingData WHERE modelId = %s"
            self.db_util.execute_query(query, (model_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in TrainingDataDAO.delete_by_model_id: {str(e)}")
            raise

    def delete_by_template_id(self, template_id):
        try:
            query = "DELETE FROM TrainingData WHERE fraudTemplateId = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in TrainingDataDAO.delete_by_template_id: {str(e)}")
            raise
