import logging
from utils.db_util import DatabaseUtil
from models.bounding_box import BoundingBox


class BoundingBoxDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    # lấy ra danh sách tất cả các bounding box
    def get_all(self):
        try:
            query = "SELECT * FROM BoundingBox"
            rows = self.db_util.execute_query(query, fetchall=True)

            if not rows:
                return []

            boxes = []
            for row in rows:
                box = BoundingBox(
                    idBox=row['idBox'],
                    xCenter=row['xCenter'],
                    yCenter=row['yCenter'],
                    width=row['width'],
                    height=row['height'],
                    xPixel=row['xPixel'],
                    yPixel=row['yPixel'],
                    widthPixel=row['widthPixel'],
                    heightPixel=row['heightPixel'],
                    fraudLabelId=row['fraudLabelId'],
                    fraudTemplateId=row['fraudTemplateId']
                )
                boxes.append(box)
            return boxes
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.get_all: {str(e)}")
            raise


    def get_by_id(self, box_id):
        try:
            query = "SELECT * FROM BoundingBox WHERE idBox = %s"
            row = self.db_util.execute_query(query, (box_id,), fetchone=True)

            if not row:
                return None

            box = BoundingBox(
                idBox=row['idBox'],
                xCenter=row['xCenter'],
                yCenter=row['yCenter'],
                width=row['width'],
                height=row['height'],
                xPixel=row['xPixel'],
                yPixel=row['yPixel'],
                widthPixel=row['widthPixel'],
                heightPixel=row['heightPixel'],
                fraudLabelId=row['fraudLabelId'],
                fraudTemplateId=row['fraudTemplateId']
            )
            return box
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.get_by_id: {str(e)}")
            raise

    def get_by_template_id(self, template_id):
        try:
            query = "SELECT * FROM BoundingBox WHERE fraudTemplateId = %s"
            rows = self.db_util.execute_query(
                query, (template_id,), fetchall=True)

            if not rows:
                return []

            boxes = []
            for row in rows:
                box = BoundingBox(
                    idBox=row['idBox'],
                    xCenter=row['xCenter'],
                    yCenter=row['yCenter'],
                    width=row['width'],
                    height=row['height'],
                    xPixel=row['xPixel'],
                    yPixel=row['yPixel'],
                    widthPixel=row['widthPixel'],
                    heightPixel=row['heightPixel'],
                    fraudLabelId=row['fraudLabelId'],
                    fraudTemplateId=template_id
                )

                boxes.append(box)

            return boxes
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.get_by_template_id: {str(e)}")
            raise

    def create(self, box):
        try:
            query = """
                INSERT INTO BoundingBox (xCenter, yCenter, width, height, xPixel, yPixel, widthPixel, heightPixel, fraudLabelId, fraudTemplateId) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                box.xCenter,
                box.yCenter,
                box.width,
                box.height,
                box.xPixel,
                box.yPixel,
                box.widthPixel,
                box.heightPixel,
                box.fraudLabelId,
                box.fraudTemplateId
            )

            box_id = self.db_util.execute_query(query, params, commit=True)

            return box_id
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.create: {str(e)}")
            raise

    def update(self, box):
        try:
            query = """
                UPDATE BoundingBox
                SET xCenter = %s, yCenter = %s, width = %s, height = %s,
                    xPixel = %s, yPixel = %s, widthPixel = %s, heightPixel = %s,
                    fraudLabelId = %s
                WHERE idBox = %s
            """

            params = (
                box.xCenter,
                box.yCenter,
                box.width,
                box.height,
                box.xPixel,
                box.yPixel,
                box.widthPixel,
                box.heightPixel,
                box.fraudLabelId,
                box.idBox
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.update: {str(e)}")
            raise

    def delete(self, box_id):
        try:
            query = "DELETE FROM BoundingBox WHERE idBox = %s"
            self.db_util.execute_query(query, (box_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.delete: {str(e)}")
            raise

    def delete_by_label_id(self, label_id):
        try:
            query = "DELETE FROM BoundingBox WHERE fraudLabelId = %s"
            self.db_util.execute_query(query, (label_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.delete_by_label_id: {str(e)}")
            raise

    def delete_by_template_id(self, template_id):
        try:
            query = """
                DELETE FROM BoundingBox
                WHERE fraudLabelId IN (
                    SELECT idLabel FROM FraudLabel WHERE fraudTemplateId = %s
                )
            """
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.delete_by_template_id: {str(e)}")
            raise
