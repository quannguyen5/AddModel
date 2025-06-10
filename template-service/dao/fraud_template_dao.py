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
                template.labels = self.label_dao.get_by_template_id(
                    template.idTemplate)
                template.boundingBox = self.box_dao.get_by_template_id(
                    template.idTemplate)
                templates.append(template)

            return templates
        except Exception as e:
            print(f"Error in get_all: {e}")
            raise

    def get_by_id(self, template_id):
        try:
            query = "SELECT * FROM FraudTemplate WHERE idTemplate = %s"
            row = self.db_util.execute_query(
                query, (template_id,), fetchone=True)

            if not row:
                return None

            template = self._row_to_template(row)
            template.labels = self.label_dao.get_by_template_id(template_id)
            template.boundingBox = self.box_dao.get_by_template_id(template_id)

            return template
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise

    def create(self, template):
        try:
            query = "INSERT INTO FraudTemplate (description, imageUrl) VALUES (%s, %s)"
            template_id = self.db_util.execute_query(
                query, (template.description, template.imageUrl), commit=True)

            # Tạo labels và boxes
            if template.labels:
                for label in template.labels:
                    label.fraudTemplateId = template_id
                    self.label_dao.create(label)

            if template.boundingBox:
                for box in template.boundingBox:
                    box.fraudTemplateId = template_id
                    self.box_dao.create(box)

            return template_id
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def delete(self, template_id):
        try:
            query = "DELETE FROM FraudTemplate WHERE idTemplate = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error in delete: {e}")
            raise

    def _row_to_template(self, row):
        return FraudTemplate(
            idTemplate=row['idTemplate'],
            description=row['description'],
            imageUrl=row['imageUrl'],
            timeUpdate=row['timeUpdate']
        )
