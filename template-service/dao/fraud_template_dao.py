import logging
from dao.bounding_box_dao import BoundingBoxDAO
from dao.fraud_label_dao import FraudLabelDAO
from utils.db_util import DatabaseUtil
from models.fraud_template import FraudTemplate
from models.fraud_label import FraudLabel
from models.bounding_box import BoundingBox
from datetime import datetime


class FraudTemplateDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query_templates = "SELECT * FROM FraudTemplate ORDER BY idTemplate"
            template_rows = self.db_util.execute_query(
                query_templates, fetchall=True)

            if not template_rows:
                return []
            templates = []
            for template_row in template_rows:
                template_id = template_row['idTemplate']
                template = self.get_by_id(template_id)
                templates.append(template)

            logging.info(
                f"Retrieved {len(templates)} templates with labels and bounding boxes")
            return templates
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, template_id):
        try:
            query_template = "SELECT * FROM FraudTemplate WHERE idTemplate = %s"
            template_row = self.db_util.execute_query(
                query_template, (template_id,), fetchone=True)
            if not template_row:
                return None
            template = FraudTemplate(
                idTemplate=template_row['idTemplate'],
                description=template_row['description'],
                imageUrl=template_row['imageUrl'],
                timeUpdate=template_row['timeUpdate']
            )
            template.labels = FraudLabelDAO().get_by_template_id(template_id)
            template.boundingBox = BoundingBoxDAO().get_by_template_id(template_id)
            return template
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.get_by_id: {str(e)}")
            raise

    def create(self, template):
        try:
            query = """
                INSERT INTO FraudTemplate (description, imageUrl, timeUpdate)
                VALUES (%s, %s, %s)
            """

            time_update = template.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                template.description,
                template.imageUrl,
                time_update
            )

            template_id = self.db_util.execute_query(
                query, params, commit=True)

            # Lưu các FraudLabel
            if template.labels:
                from dao.fraud_label_dao import FraudLabelDAO
                fraud_label_dao = FraudLabelDAO()

                for label in template.labels:
                    label.fraudTemplateId = template_id
                    label_id = fraud_label_dao.create(label)

                    # Update labelId for any boxes that reference this label
                    for box in template.boundingBox:
                        if hasattr(box, 'tempLabelId') and box.tempLabelId == label.tempId:
                            box.fraudLabelId = label_id

            if template.boundingBox:
                from dao.bounding_box_dao import BoundingBoxDAO
                bounding_box_dao = BoundingBoxDAO()

                for box in template.boundingBox:
                    box.fraudTemplateId = template_id
                    bounding_box_dao.create(box)

            return template_id
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.create: {str(e)}")
            raise

    def update(self, template):
        try:
            query = """
                UPDATE FraudTemplate
                SET description = %s, imageUrl = %s, timeUpdate = %s
                WHERE idTemplate = %s
            """

            time_update = template.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                template.description,
                template.imageUrl,
                time_update,
                template.idTemplate
            )

            self.db_util.execute_query(query, params, commit=True)

            # Xóa tất cả các BoundingBox cũ (will cascade delete through labels)
            from dao.bounding_box_dao import BoundingBoxDAO
            bounding_box_dao = BoundingBoxDAO()

            query_boxes = """
                DELETE FROM BoundingBox 
                WHERE fraudLabelId IN (
                    SELECT idLabel FROM FraudLabel WHERE fraudTemplateId = %s
                )
            """
            self.db_util.execute_query(
                query_boxes, (template.idTemplate,), commit=True)

            # Xóa tất cả các FraudLabel cũ
            from dao.fraud_label_dao import FraudLabelDAO
            fraud_label_dao = FraudLabelDAO()
            fraud_label_dao.delete_by_template_id(template.idTemplate)

            # Tạo lại các FraudLabel
            if template.labels:
                for label in template.labels:
                    label.fraudTemplateId = template.idTemplate
                    label_id = fraud_label_dao.create(label)

                    # Update labelId for any boxes that reference this label
                    for box in template.boundingBox:
                        if hasattr(box, 'tempLabelId') and box.tempLabelId == label.tempId:
                            box.fraudLabelId = label_id

            # Tạo lại các BoundingBox
            if template.boundingBox:
                for box in template.boundingBox:
                    box.fraudTemplateId = template.idTemplate
                    bounding_box_dao.create(box)

            return True
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.update: {str(e)}")
            raise

    def delete(self, template_id):
        try:
            # First delete all bounding boxes related to this template's labels
            query_boxes = """
                DELETE FROM BoundingBox 
                WHERE fraudLabelId IN (
                    SELECT idLabel FROM FraudLabel WHERE fraudTemplateId = %s
                )
            """
            self.db_util.execute_query(
                query_boxes, (template_id,), commit=True)

            # Then delete all labels related to this template
            query_labels = "DELETE FROM FraudLabel WHERE fraudTemplateId = %s"
            self.db_util.execute_query(
                query_labels, (template_id,), commit=True)

            # Finally delete the template
            query = "DELETE FROM FraudTemplate WHERE idTemplate = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.delete: {str(e)}")
            raise
