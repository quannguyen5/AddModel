from utils.db_util import DatabaseUtil
from models.fraud_label import FraudLabel


class FraudLabelDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM FraudLabel"
            rows = self.db_util.execute_query(query, fetchall=True)
            return [self._row_to_label(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_all: {e}")
            raise

    def get_by_id(self, label_id):
        try:
            query = "SELECT * FROM FraudLabel WHERE idLabel = %s"
            row = self.db_util.execute_query(query, (label_id,), fetchone=True)
            return self._row_to_label(row) if row else None
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise

    def get_by_template_id(self, template_id):
        try:
            query = "SELECT * FROM FraudLabel"
            rows = self.db_util.execute_query(query, fetchall=True)
            return [self._row_to_label(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_by_template_id: {e}")
            raise

    def create(self, label):
        try:
            query = "INSERT INTO FraudLabel (description, typeLabel) VALUES (%s, %s)"
            return self.db_util.execute_query(
                query, (label.description, label.typeLabel), commit=True)
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def _row_to_label(self, row):
        return FraudLabel(
            idLabel=row['idLabel'],
            description=row['description'],
            typeLabel=row['typeLabel']
        )
