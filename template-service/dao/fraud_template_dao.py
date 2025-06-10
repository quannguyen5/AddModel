# template-service/dao/fraud_template_dao.py (Simplified)
from utils.db_util import DatabaseUtil
from models.fraud_template import FraudTemplate
from dao.fraud_label_dao import FraudLabelDAO
from dao.bounding_box_dao import BoundingBoxDAO


class FraudTemplateDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()
        self.label_dao = FraudLabelDAO()
        self.box_dao = BoundingBoxDAO()

    def get_all(self):
        try:
            query = "SELECT * FROM FraudTemplate ORDER BY idTemplate"
            rows = self.db_util.execute_query(query, fetchall=True)

            templates = []
            for row in rows:
                template = self._row_to_template(row)
                # Gán tất cả labels và boxes cho mỗi template
                template.labels = self.label_dao.get_all()
                template.boundingBox = self.box_dao.get_all()
                templates.append(template)

            return templates
        except Exception as e:
            print(f"Error in get_all: {e}")
            return []  # Return empty list instead of raising

    def get_by_id(self, template_id):
        try:
            query = "SELECT * FROM FraudTemplate WHERE idTemplate = %s"
            row = self.db_util.execute_query(
                query, (template_id,), fetchone=True)

            if not row:
                return None

            template = self._row_to_template(row)
            # Gán tất cả labels và boxes
            template.labels = self.label_dao.get_all()
            template.boundingBox = self.box_dao.get_all()

            return template
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            return None

    def create(self, template):
        try:
            query = "INSERT INTO FraudTemplate (description, imageUrl) VALUES (%s, %s)"
            template_id = self.db_util.execute_query(
                query, (template.description, template.imageUrl), commit=True)
            return template_id
        except Exception as e:
            print(f"Error in create: {e}")
            return None

    def delete(self, template_id):
        try:
            query = "DELETE FROM FraudTemplate WHERE idTemplate = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error in delete: {e}")
            return False

    def _row_to_template(self, row):
        return FraudTemplate(
            idTemplate=row['idTemplate'],
            description=row['description'],
            imageUrl=row['imageUrl'],
            timeUpdate=row['timeUpdate']
        )
