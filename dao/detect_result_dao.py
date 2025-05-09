# dao/detect_result_dao.py

import logging
from utils.db_util import DatabaseUtil
from models.detect_result import DetectResult


class DetectResultDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM DetectResult"
            rows = self.db_util.execute_query(query, fetchall=True)

            if not rows:
                return []

            results = []
            for row in rows:
                result = DetectResult(
                    idResult=row['idResult'],
                    description=row['description'],
                    imageUrl=row['imageUrl'],
                    phaseId=row['phaseId']
                )

                from dao.fraud_dao import FraudDAO
                fraud_dao = FraudDAO()
                result.frauds = fraud_dao.get_by_detect_result_id(
                    row['idResult'])

                results.append(result)

            return results
        except Exception as e:
            logging.error(f"Error in DetectResultDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, result_id):
        try:
            query = "SELECT * FROM DetectResult WHERE idResult = %s"
            row = self.db_util.execute_query(
                query, (result_id,), fetchone=True)

            if not row:
                return None

            result = DetectResult(
                idResult=row['idResult'],
                description=row['description'],
                imageUrl=row['imageUrl'],
                phaseId=row['phaseId']
            )

            # Lấy danh sách frauds cho result này
            from dao.fraud_dao import FraudDAO
            fraud_dao = FraudDAO()
            result.frauds = fraud_dao.get_by_detect_result_id(row['idResult'])

            return result
        except Exception as e:
            logging.error(f"Error in DetectResultDAO.get_by_id: {str(e)}")
            raise

    def get_by_phase_id(self, phase_id):
        try:
            query = "SELECT * FROM DetectResult WHERE phaseId = %s"
            rows = self.db_util.execute_query(
                query, (phase_id,), fetchall=True)

            if not rows:
                return []

            results = []
            for row in rows:
                result = DetectResult(
                    idResult=row['idResult'],
                    description=row['description'],
                    imageUrl=row['imageUrl'],
                    phaseId=row['phaseId']
                )

                # Lấy danh sách frauds cho result này
                from dao.fraud_dao import FraudDAO
                fraud_dao = FraudDAO()
                result.frauds = fraud_dao.get_by_detect_result_id(
                    row['idResult'])

                results.append(result)

            return results
        except Exception as e:
            logging.error(
                f"Error in DetectResultDAO.get_by_phase_id: {str(e)}")
            raise

    def create(self, detect_result):
        try:
            query = """
                INSERT INTO DetectResult (description, imageUrl, phaseId)
                VALUES (%s, %s, %s)
            """

            params = (
                detect_result.description,
                detect_result.imageUrl,
                detect_result.phaseId
            )

            result_id = self.db_util.execute_query(query, params, commit=True)

            # Lưu các frauds nếu có
            if detect_result.frauds:
                from dao.fraud_dao import FraudDAO
                fraud_dao = FraudDAO()

                for fraud in detect_result.frauds:
                    fraud.detectResultId = result_id
                    fraud_dao.create(fraud)

            return result_id
        except Exception as e:
            logging.error(f"Error in DetectResultDAO.create: {str(e)}")
            raise

    def update(self, detect_result):
        try:
            query = """
                UPDATE DetectResult
                SET description = %s, imageUrl = %s, phaseId = %s
                WHERE idResult = %s
            """

            params = (
                detect_result.description,
                detect_result.imageUrl,
                detect_result.phaseId,
                detect_result.idResult
            )

            self.db_util.execute_query(query, params, commit=True)

            # Cập nhật các frauds
            if detect_result.frauds:
                from dao.fraud_dao import FraudDAO
                fraud_dao = FraudDAO()

                # Xóa các frauds cũ
                fraud_dao.delete_by_detect_result_id(detect_result.idResult)

                # Tạo lại các frauds mới
                for fraud in detect_result.frauds:
                    fraud.detectResultId = detect_result.idResult
                    fraud_dao.create(fraud)

            return True
        except Exception as e:
            logging.error(f"Error in DetectResultDAO.update: {str(e)}")
            raise

    def delete(self, result_id):
        try:
            # Xóa các frauds liên quan (sẽ tự động xóa do ON DELETE CASCADE)
            query = "DELETE FROM DetectResult WHERE idResult = %s"
            self.db_util.execute_query(query, (result_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in DetectResultDAO.delete: {str(e)}")
            raise

    def delete_by_phase_id(self, phase_id):
        try:
            # Xóa các frauds liên quan (sẽ tự động xóa do ON DELETE CASCADE)
            query = "DELETE FROM DetectResult WHERE phaseId = %s"
            self.db_util.execute_query(query, (phase_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in DetectResultDAO.delete_by_phase_id: {str(e)}")
            raise
