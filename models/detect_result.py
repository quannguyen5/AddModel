
class DetectResult:
    def __init__(self, idResult=None, description=None, imageUrl=None, phaseId=None, frauds=None):
        self.idResult = idResult
        self.description = description
        self.imageUrl = imageUrl
        self.phaseId = phaseId
        self.frauds = frauds if frauds else []

    def to_dict(self):
        detect_result_dict = {
            'idResult': self.idResult,
            'description': self.description,
            'imageUrl': self.imageUrl,
            'phaseId': self.phaseId
        }
        
        if self.frauds:
            detect_result_dict['frauds'] = [
                fraud.to_dict() if hasattr(fraud, 'to_dict') else fraud
                for fraud in self.frauds
            ]
            
        return detect_result_dict

    @classmethod
    def from_dict(cls, data):
        from .fraud import Fraud
        
        detect_result = cls()
        detect_result.idResult = data.get('idResult')
        detect_result.description = data.get('description')
        detect_result.imageUrl = data.get('imageUrl')
        detect_result.phaseId = data.get('phaseId')
        
        frauds_data = data.get('frauds')
        if frauds_data:
            detect_result.frauds = [
                Fraud.from_dict(fraud) if isinstance(fraud, dict) else fraud
                for fraud in frauds_data
            ]
            
        return detect_result