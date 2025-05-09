from datetime import datetime


class PhaseDetection:
    def __init__(self, idPhase=None, description=None, timeDetect=None, model=None, result=None):
        self.idPhase = idPhase
        self.description = description
        self.timeDetect = timeDetect if timeDetect else datetime.now()
        self.model = model if model else None
        self.result = result if result else []

    def to_dict(self):
        phase_detect_dict = {
            'idPhase': self.idPhase,
            'description': self.description,
            'timeDetect': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else self.timeUpdate
        }
        if self.model:
            phase_detect_dict['model'] = self.model.to_dict()
        if self.result:
            phase_detect_dict['result'] = [
                res.to_dict() if hasattr(res, 'to_dict') else res
                for res in self.result
            ]
        return phase_detect_dict

    @classmethod
    def from_dict(cls, data):
        from .model import Model
        from .detect_result import DetectResult
        phase = cls()
        phase.idphase = data.get('idPhase')
        phase.description = data.get('description')
        time_update = data.get('timeDetect')
        if time_update and isinstance(time_update, str):
            try:
                phase.timeDetect = datetime.strptime(
                    time_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                phase.timeDetect = time_update
        else:
            phase.timeDetect = time_update

        model = data.get('model')
        if model:
            phase.model = Model.from_dict(
                model) if isinstance(model, dict) else model

        res = data.get('result')
        if res:
            phase.result = [
                DetectResult.from_dict(resu) if isinstance(
                    resu, dict) else resu
                for resu in res
            ]

        return phase
