import logging
from utils.db_util import DatabaseUtil
from models.fraud_label import FraudLabel
from utils.enums import TypeLabel


class FraudLabelDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM FraudLabel"
            rows = self.db_util.execute_query(query, fetchall=True)

            if not rows:
                return []

            labels = []
            for row in rows:
                label = FraudLabel(
                    idLabel=row['idLabel'],
                    description=row['description'],
                    typeLabel=row['typeLabel']
                )
                labels.append(label)
            return labels
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, label_id):
        try:
            query = "SELECT * FROM FraudLabel WHERE idLabel = %s"
            row = self.db_util.execute_query(query, (label_id,), fetchone=True)

            if not row:
                return None

            label = FraudLabel(
                idLabel=row['idLabel'],
                description=row['description'],
                typeLabel=row['typeLabel']
            )

            return label
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.get_by_id: {str(e)}")
            raise

    def get_by_template_id(self, template_id):
        try:
            query = "SELECT * FROM BoundingBox WHERE fraudTemplateId = %s"
            rows = self.db_util.execute_query(
                query, (template_id,), fetchall=True)

            if not rows:
                return []

            labels = []
            for row in rows:
                label = self.get_by_id(row['fraudLabelId'])
                labels.append(label)

            return labels
        except Exception as e:
            logging.error(
                f"Error in FraudLabelDAO.get_by_template_id: {str(e)}")
            raise
