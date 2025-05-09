import logging
from utils.db_util import DatabaseUtil
from models.model import Model
from utils.enums import ModelType
from datetime import datetime


class ModelDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = """
                SELECT m.*, ti.idInfo AS trainInfoId
                FROM Model m
                LEFT JOIN TrainInfo ti ON m.trainInfoId = ti.idInfo
                ORDER BY m.lastUpdate DESC
            """

            rows = self.db_util.execute_query(query, fetchall=True)

            models = []
            for row in rows:
                model = Model(
                    idModel=row['idModel'],
                    modelName=row['modelName'],
                    modelType=row['modelType'],
                    version=row['version'],
                    description=row['description'],
                    lastUpdate=row['lastUpdate']
                )

                # Nếu có TrainInfo, lấy thông tin TrainInfo từ TrainInfoDAO
                if row['trainInfoId']:
                    from dao.train_info_dao import TrainInfoDAO
                    train_info_dao = TrainInfoDAO()
                    model.trainInfo = train_info_dao.get_by_id(
                        row['trainInfoId'])

                models.append(model)

            return models
        except Exception as e:
            logging.error(f"Error in ModelDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, model_id):
        try:
            query = """
                SELECT m.*, ti.idInfo AS trainInfoId
                FROM Model m
                LEFT JOIN TrainInfo ti ON m.trainInfoId = ti.idInfo
                WHERE m.idModel = %s
            """
            row = self.db_util.execute_query(query, (model_id,), fetchone=True)
            if not row:
                return None
            model = Model(
                idModel=row['idModel'],
                modelName=row['modelName'],
                modelType=row['modelType'],
                version=row['version'],
                description=row['description'],
                lastUpdate=row['lastUpdate']
            )
            # Nếu có TrainInfo, lấy thông tin TrainInfo từ TrainInfoDAO
            if row['trainInfoId']:
                from dao.train_info_dao import TrainInfoDAO
                train_info_dao = TrainInfoDAO()
                model.trainInfo = train_info_dao.get_by_id(row['trainInfoId'])
            return model

        except Exception as e:
            logging.error(f"Error in ModelDAO.get_by_id: {str(e)}")
            raise

    def create(self, model):
        try:
            # Kiểm tra TrainInfo
            trainInfoId = None
            if model.trainInfo and model.trainInfo.idInfo:
                trainInfoId = model.trainInfo.idInfo
            elif model.trainInfo:
                # Nếu có TrainInfo nhưng chưa có ID, cần tạo TrainInfo trước
                from dao.train_info_dao import TrainInfoDAO
                train_info_dao = TrainInfoDAO()
                trainInfoId = train_info_dao.create(model.trainInfo)
            # Chuẩn bị dữ liệu cho truy vấn
            model_type = model.modelType.value if isinstance(
                model.modelType, ModelType) else model.modelType

            query = """
                INSERT INTO Model (modelName, modelType, version, description, lastUpdate, trainInfoId)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            last_update = model.lastUpdate
            if isinstance(last_update, datetime):
                last_update = last_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                model.modelName,
                model_type,
                model.version,
                model.description,
                last_update,
                trainInfoId
            )
            model_id = self.db_util.execute_query(query, params, commit=True)

            return model_id
        except Exception as e:
            logging.error(f"Error in ModelDAO.create: {str(e)}")
            raise

    def update(self, model):
        try:
            # Kiểm tra TrainInfo
            trainInfoId = None
            if model.trainInfo and model.trainInfo.idInfo:
                trainInfoId = model.trainInfo.idInfo
                # Cập nhật TrainInfo
                from dao.train_info_dao import TrainInfoDAO
                train_info_dao = TrainInfoDAO()
                train_info_dao.update(model.trainInfo)
            elif model.trainInfo:
                # Nếu có TrainInfo nhưng chưa có ID, cần tạo TrainInfo mới
                from dao.train_info_dao import TrainInfoDAO
                train_info_dao = TrainInfoDAO()
                trainInfoId = train_info_dao.create(model.trainInfo)

            # Chuẩn bị dữ liệu cho truy vấn
            model_type = model.modelType.value if isinstance(
                model.modelType, ModelType) else model.modelType

            query = """
                UPDATE Model
                SET modelName = %s, modelType = %s, version = %s, 
                    description = %s, lastUpdate = %s, trainInfoId = %s
                WHERE idModel = %s
            """

            last_update = model.lastUpdate
            if isinstance(last_update, datetime):
                last_update = last_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                model.modelName,
                model_type,
                model.version,
                model.description,
                last_update,
                trainInfoId,
                model.idModel
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in ModelDAO.update: {str(e)}")
            raise

    def delete(self, model_id):
        try:
            # Lấy thông tin mô hình trước khi xóa
            model = self.get_by_id(model_id)
            if not model:
                return False

            # Xóa mô hình
            query = "DELETE FROM Model WHERE idModel = %s"
            self.db_util.execute_query(query, (model_id,), commit=True)

            # Nếu mô hình có TrainInfo, xóa TrainInfo
            if model.trainInfo:
                from dao.train_info_dao import TrainInfoDAO
                train_info_dao = TrainInfoDAO()
                train_info_dao.delete(model.trainInfo.idInfo)

            return True
        except Exception as e:
            logging.error(f"Error in ModelDAO.delete: {str(e)}")
            raise

    def get_fraud_templates(self, model_id):
        try:
            query = """
                SELECT ft.*
                FROM FraudTemplate ft
                JOIN TrainingData td ON ft.idTemplate = td.fraudTemplateId
                WHERE td.modelId = %s
            """

            rows = self.db_util.execute_query(
                query, (model_id,), fetchall=True)

            if not rows:
                return []

            from dao.fraud_template_dao import FraudTemplateDAO
            fraud_template_dao = FraudTemplateDAO()

            templates = []
            for row in rows:
                template = fraud_template_dao.get_by_id(row['idTemplate'])
                if template:
                    templates.append(template)

            return templates
        except Exception as e:
            logging.error(f"Error in ModelDAO.get_fraud_templates: {str(e)}")
            raise
