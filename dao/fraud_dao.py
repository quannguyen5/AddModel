# dao/fraud_dao.py

import logging
from utils.db_util import DatabaseUtil
from models.fraud import Fraud


class FraudDAO:
    """
    Data Access Object cho đối tượng Fraud
    """

    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM Fraud"
            rows = self.db_util.execute_query(query, fetchall=True)

            if not rows:
                return []

            frauds = []
            for row in rows:
                fraud = Fraud(
                    idFraud=row['idFraud'],
                    fraud=row['fraud'],
                    detectResultId=row['detectResultId']
                )
                frauds.append(fraud)

            return frauds
        except Exception as e:
            logging.error(f"Error in FraudDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, fraud_id):
        """
        Lấy fraud theo ID
        """
        try:
            query = "SELECT * FROM Fraud WHERE idFraud = %s"
            row = self.db_util.execute_query(query, (fraud_id,), fetchone=True)

            if not row:
                return None

            fraud = Fraud(
                idFraud=row['idFraud'],
                fraud=row['fraud'],
                detectResultId=row['detectResultId']
            )

            return fraud
        except Exception as e:
            logging.error(f"Error in FraudDAO.get_by_id: {str(e)}")
            raise

    def get_by_detect_result_id(self, detect_result_id):
        """
        Lấy tất cả các fraud theo DetectResult ID
        """
        try:
            query = "SELECT * FROM Fraud WHERE detectResultId = %s"
            rows = self.db_util.execute_query(query, (detect_result_id,), fetchall=True)

            if not rows:
                return []

            frauds = []
            for row in rows:
                fraud = Fraud(
                    idFraud=row['idFraud'],
                    fraud=row['fraud'],
                    detectResultId=row['detectResultId']
                )
                frauds.append(fraud)

            return frauds
        except Exception as e:
            logging.error(f"Error in FraudDAO.get_by_detect_result_id: {str(e)}")
            raise

    def create(self, fraud):
        """
        Tạo fraud mới
        """
        try:
            query = """
                INSERT INTO Fraud (fraud, detectResultId)
                VALUES (%s, %s)
            """

            params = (
                fraud.fraud,
                fraud.detectResultId
            )

            fraud_id = self.db_util.execute_query(query, params, commit=True)

            return fraud_id
        except Exception as e:
            logging.error(f"Error in FraudDAO.create: {str(e)}")
            raise

    def update(self, fraud):
        """
        Cập nhật fraud
        """
        try:
            query = """
                UPDATE Fraud
                SET fraud = %s, detectResultId = %s
                WHERE idFraud = %s
            """

            params = (
                fraud.fraud,
                fraud.detectResultId,
                fraud.idFraud
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudDAO.update: {str(e)}")
            raise

    def delete(self, fraud_id):
        """
        Xóa fraud theo ID
        """
        try:
            query = "DELETE FROM Fraud WHERE idFraud = %s"
            self.db_util.execute_query(query, (fraud_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudDAO.delete: {str(e)}")
            raise

    def delete_by_detect_result_id(self, detect_result_id):
        """
        Xóa tất cả các fraud theo DetectResult ID
        """
        try:
            query = "DELETE FROM Fraud WHERE detectResultId = %s"
            self.db_util.execute_query(query, (detect_result_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudDAO.delete_by_detect_result_id: {str(e)}")
            raise