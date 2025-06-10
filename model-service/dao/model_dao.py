from utils.db_util import DatabaseUtil
from models.model import Model
from dao.train_info_dao import TrainInfoDAO


class ModelDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()
        self.train_info_dao = TrainInfoDAO()

    def get_all(self):
        try:
            query = "SELECT * FROM Model ORDER BY lastUpdate DESC"
            rows = self.db_util.execute_query(query, fetchall=True)

            models = []
            for row in rows:
                model = self._row_to_model(row)
                if row['trainInfoId']:
                    model.trainInfo = self.train_info_dao.get_by_id(
                        row['trainInfoId'])
                models.append(model)

            return models
        except Exception as e:
            print(f"Error in get_all: {e}")
            raise

    def get_by_id(self, model_id):
        try:
            query = "SELECT * FROM Model WHERE idModel = %s"
            row = self.db_util.execute_query(query, (model_id,), fetchone=True)

            if not row:
                return None

            model = self._row_to_model(row)
            if row['trainInfoId']:
                model.trainInfo = self.train_info_dao.get_by_id(
                    row['trainInfoId'])

            return model
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise

    def get_by_name_and_version(self, model_name, version):
        """Kiểm tra xem model với tên và version đã tồn tại chưa"""
        try:
            query = "SELECT * FROM Model WHERE modelName = %s AND version = %s"
            row = self.db_util.execute_query(
                query, (model_name, version), fetchone=True)

            if not row:
                return None

            model = self._row_to_model(row)
            if row['trainInfoId']:
                model.trainInfo = self.train_info_dao.get_by_id(
                    row['trainInfoId'])

            return model
        except Exception as e:
            print(f"Error in get_by_name_and_version: {e}")
            raise

    def create(self, model):
        try:
            # Tạo train info trước nếu có
            train_info_id = None
            if model.trainInfo:
                train_info_id = self.train_info_dao.create(model.trainInfo)

            query = """
            INSERT INTO Model (modelName, modelType, version, description, trainInfoId)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (model.modelName, model.modelType, model.version,
                      model.description, train_info_id)

            return self.db_util.execute_query(query, params, commit=True)
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def update(self, model):
        """Update existing model"""
        try:
            # Update train info nếu có
            if model.trainInfo and model.trainInfo.idInfo:
                self.train_info_dao.update(model.trainInfo)

            query = """
            UPDATE Model 
            SET modelName = %s, modelType = %s, version = %s, 
                description = %s, lastUpdate = CURRENT_TIMESTAMP
            WHERE idModel = %s
            """
            params = (model.modelName, model.modelType, model.version,
                      model.description, model.idModel)

            self.db_util.execute_query(query, params, commit=True)
            return True
        except Exception as e:
            print(f"Error in update: {e}")
            raise

    def delete(self, model_id):
        try:
            query = "DELETE FROM Model WHERE idModel = %s"
            self.db_util.execute_query(query, (model_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error in delete: {e}")
            raise

    def _row_to_model(self, row):
        return Model(
            idModel=row['idModel'],
            modelName=row['modelName'],
            modelType=row['modelType'],
            version=row['version'],
            description=row['description'],
            lastUpdate=row['lastUpdate']
        )
