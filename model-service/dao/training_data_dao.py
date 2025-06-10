from utils.db_util import DatabaseUtil
from models.training_data import TrainingData


class TrainingDataDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def create(self, training_data):
        try:
            query = """
            INSERT INTO TrainingData (description, modelId, fraudTemplateId)
            VALUES (%s, %s, %s)
            """
            params = (training_data.description,
                      training_data.modelId, training_data.fraudTemplateId)
            return self.db_util.execute_query(query, params, commit=True)
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def get_by_model_id(self, model_id):
        try:
            query = "SELECT * FROM TrainingData WHERE modelId = %s"
            rows = self.db_util.execute_query(
                query, (model_id,), fetchall=True)
            return [self._row_to_training_data(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_by_model_id: {e}")
            raise

    def _row_to_training_data(self, row):
        return TrainingData(
            idTrainingData=row['idTrainingData'],
            timeUpdate=row['timeUpdate'],
            description=row['description'],
            modelId=row['modelId'],
            fraudTemplateId=row['fraudTemplateId']
        )
