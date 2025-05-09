import logging
from utils.db_util import DatabaseUtil
from models.phase_detection import PhaseDetection
from datetime import datetime


class PhaseDetectionDAO:
    """
    Data Access Object cho đối tượng PhaseDetection
    """

    def __init__(self):
        self.db_util = DatabaseUtil()

    def _calculate_errors_for_phase(self, phase):
        """
        Tính số lỗi cho một phiên phát hiện dựa trên số lượng fraud
        """
        errors_detected = 0
        for result in phase.result:
            errors_detected += len(result.frauds)
        phase.errors_detected = errors_detected
        return phase

    def get_all(self):
        """
        Lấy tất cả các phiên nhận dạng

        Returns:
            list: Danh sách các đối tượng PhaseDetection
        """
        try:
            query = """
                SELECT p.*, m.idModel as modelId
                FROM PhaseDetection p
                LEFT JOIN Model m ON p.modelId = m.idModel
                ORDER BY p.timeDetect DESC
            """

            rows = self.db_util.execute_query(query, fetchall=True)

            if not rows:
                return []

            phases = []
            for row in rows:
                phase = PhaseDetection(
                    idPhase=row['idPhase'],
                    description=row['description'],
                    timeDetect=row['timeDetect']
                )

                # Lấy thông tin Model nếu có
                if row['modelId']:
                    from dao.model_dao import ModelDAO
                    model_dao = ModelDAO()
                    phase.model = model_dao.get_by_id(row['modelId'])

                # Lấy danh sách kết quả
                from dao.detect_result_dao import DetectResultDAO
                result_dao = DetectResultDAO()
                phase.result = result_dao.get_by_phase_id(row['idPhase'])
                
                # Tính số lỗi
                phase = self._calculate_errors_for_phase(phase)

                phases.append(phase)

            return phases
        except Exception as e:
            logging.error(f"Error in PhaseDetectionDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, phase_id):
        """
        Lấy phiên nhận dạng theo ID

        Args:
            phase_id (int): ID của phiên nhận dạng

        Returns:
            PhaseDetection: Đối tượng PhaseDetection tương ứng hoặc None nếu không tìm thấy
        """
        try:
            query = """
                SELECT p.*, m.idModel as modelId
                FROM PhaseDetection p
                LEFT JOIN Model m ON p.modelId = m.idModel
                WHERE p.idPhase = %s
            """

            row = self.db_util.execute_query(query, (phase_id,), fetchone=True)

            if not row:
                return None

            phase = PhaseDetection(
                idPhase=row['idPhase'],
                description=row['description'],
                timeDetect=row['timeDetect']
            )

            # Lấy thông tin Model nếu có
            if row['modelId']:
                from dao.model_dao import ModelDAO
                model_dao = ModelDAO()
                phase.model = model_dao.get_by_id(row['modelId'])

            # Lấy danh sách kết quả
            from dao.detect_result_dao import DetectResultDAO
            result_dao = DetectResultDAO()
            phase.result = result_dao.get_by_phase_id(row['idPhase'])
            
            # Tính số lỗi
            phase = self._calculate_errors_for_phase(phase)

            return phase
        except Exception as e:
            logging.error(f"Error in PhaseDetectionDAO.get_by_id: {str(e)}")
            raise

    def get_by_model_id(self, model_id):
        """
        Lấy tất cả các phiên nhận dạng theo Model ID

        Args:
            model_id (int): ID của Model

        Returns:
            list: Danh sách các đối tượng PhaseDetection
        """
        try:
            query = """
                SELECT p.*, m.idModel as modelId
                FROM PhaseDetection p
                LEFT JOIN Model m ON p.modelId = m.idModel
                WHERE p.modelId = %s
                ORDER BY p.timeDetect DESC
            """

            rows = self.db_util.execute_query(
                query, (model_id,), fetchall=True)

            if not rows:
                return []

            phases = []
            for row in rows:
                phase = PhaseDetection(
                    idPhase=row['idPhase'],
                    description=row['description'],
                    timeDetect=row['timeDetect']
                )

                # Lấy thông tin Model
                from dao.model_dao import ModelDAO
                model_dao = ModelDAO()
                phase.model = model_dao.get_by_id(model_id)

                # Lấy danh sách kết quả
                from dao.detect_result_dao import DetectResultDAO
                result_dao = DetectResultDAO()
                phase.result = result_dao.get_by_phase_id(row['idPhase'])
                
                # Tính số lỗi
                phase = self._calculate_errors_for_phase(phase)

                phases.append(phase)

            return phases
        except Exception as e:
            logging.error(
                f"Error in PhaseDetectionDAO.get_by_model_id: {str(e)}")
            raise

    def create(self, phase):
        """
        Tạo phiên nhận dạng mới

        Args:
            phase (PhaseDetection): Đối tượng PhaseDetection cần tạo

        Returns:
            int: ID của phiên nhận dạng vừa tạo
        """
        try:
            query = """
                INSERT INTO PhaseDetection (description, timeDetect, modelId)
                VALUES (%s, %s, %s)
            """

            time_detect = phase.timeDetect
            if isinstance(time_detect, datetime):
                time_detect = time_detect.strftime('%Y-%m-%d %H:%M:%S')

            model_id = None
            if phase.model:
                model_id = phase.model.idModel

            params = (
                phase.description,
                time_detect,
                model_id
            )

            phase_id = self.db_util.execute_query(query, params, commit=True)

            # Lưu các DetectResult
            if phase.result:
                from dao.detect_result_dao import DetectResultDAO
                result_dao = DetectResultDAO()

                for result in phase.result:
                    result.phaseId = phase_id
                    result_dao.create(result)

            return phase_id
        except Exception as e:
            logging.error(f"Error in PhaseDetectionDAO.create: {str(e)}")
            raise

    def update(self, phase):
        """
        Cập nhật phiên nhận dạng

        Args:
            phase (PhaseDetection): Đối tượng PhaseDetection cần cập nhật

        Returns:
            bool: True nếu cập nhật thành công, False nếu không
        """
        try:
            query = """
                UPDATE PhaseDetection
                SET description = %s, timeDetect = %s, modelId = %s
                WHERE idPhase = %s
            """

            time_detect = phase.timeDetect
            if isinstance(time_detect, datetime):
                time_detect = time_detect.strftime('%Y-%m-%d %H:%M:%S')

            model_id = None
            if phase.model:
                model_id = phase.model.idModel

            params = (
                phase.description,
                time_detect,
                model_id,
                phase.idPhase
            )

            self.db_util.execute_query(query, params, commit=True)

            # Cập nhật các DetectResult
            if phase.result:
                from dao.detect_result_dao import DetectResultDAO
                result_dao = DetectResultDAO()

                # Xóa tất cả các DetectResult cũ
                result_dao.delete_by_phase_id(phase.idPhase)

                # Tạo lại các DetectResult mới
                for result in phase.result:
                    result.phaseId = phase.idPhase
                    result_dao.create(result)

            return True
        except Exception as e:
            logging.error(f"Error in PhaseDetectionDAO.update: {str(e)}")
            raise

    def delete(self, phase_id):
        """
        Xóa phiên nhận dạng theo ID

        Args:
            phase_id (int): ID của phiên nhận dạng cần xóa

        Returns:
            bool: True nếu xóa thành công, False nếu không
        """
        try:
            # Xóa tất cả các DetectResult liên quan
            from dao.detect_result_dao import DetectResultDAO
            result_dao = DetectResultDAO()
            result_dao.delete_by_phase_id(phase_id)

            # Xóa PhaseDetection
            query = "DELETE FROM PhaseDetection WHERE idPhase = %s"
            self.db_util.execute_query(query, (phase_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in PhaseDetectionDAO.delete: {str(e)}")
            raise