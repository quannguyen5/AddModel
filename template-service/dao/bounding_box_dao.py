from utils.db_util import DatabaseUtil
from models.bounding_box import BoundingBox


class BoundingBoxDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM BoundingBox"
            rows = self.db_util.execute_query(query, fetchall=True)
            return [self._row_to_box(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_all: {e}")
            raise

    def get_by_id(self, box_id):
        try:
            query = "SELECT * FROM BoundingBox WHERE idBox = %s"
            row = self.db_util.execute_query(query, (box_id,), fetchone=True)
            return self._row_to_box(row) if row else None
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise

    def get_by_template_id(self, template_id):
        """
        Lấy bounding boxes liên quan đến template
        Vì structure hiện tại, ta sẽ lấy boxes thông qua fraudLabelId
        """
        try:
            # Lấy tất cả bounding boxes
            # Nếu cần filter theo template, cần thêm logic liên kết
            query = "SELECT * FROM BoundingBox"
            rows = self.db_util.execute_query(query, fetchall=True)
            return [self._row_to_box(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_by_template_id: {e}")
            raise

    def get_by_label_id(self, label_id):
        """Lấy bounding boxes theo fraudLabelId"""
        try:
            query = "SELECT * FROM BoundingBox WHERE fraudLabelId = %s"
            rows = self.db_util.execute_query(
                query, (label_id,), fetchall=True)
            return [self._row_to_box(row) for row in rows] if rows else []
        except Exception as e:
            print(f"Error in get_by_label_id: {e}")
            raise

    def create(self, box):
        try:
            query = """
            INSERT INTO BoundingBox 
            (xCenter, yCenter, width, height, xPixel, yPixel, widthPixel, heightPixel, fraudLabelId) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (box.xCenter, box.yCenter, box.width, box.height,
                      box.xPixel, box.yPixel, box.widthPixel, box.heightPixel, box.fraudLabelId)

            return self.db_util.execute_query(query, params, commit=True)
        except Exception as e:
            print(f"Error in create: {e}")
            raise

    def _row_to_box(self, row):
        return BoundingBox(
            idBox=row['idBox'],
            xCenter=row['xCenter'],
            yCenter=row['yCenter'],
            width=row['width'],
            height=row['height'],
            xPixel=row.get('xPixel'),
            yPixel=row.get('yPixel'),
            widthPixel=row.get('widthPixel'),
            heightPixel=row.get('heightPixel'),
            fraudLabelId=row['fraudLabelId']
        )
