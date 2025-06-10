from datetime import datetime


class FraudTemplate:
    def __init__(self, idTemplate=None, description=None, imageUrl=None, timeUpdate=None, labels=None, boundingBox=None):
        self.idTemplate = idTemplate
        self.description = description
        self.imageUrl = imageUrl
        self.timeUpdate = timeUpdate if timeUpdate else datetime.now()
        self.labels = labels or []
        self.boundingBox = boundingBox or []

    def to_dict(self):
        return {
            'idTemplate': self.idTemplate,
            'description': self.description,
            'imageUrl': self.imageUrl,
            'timeUpdate': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else str(self.timeUpdate),
            'labels': [label.to_dict() if hasattr(label, 'to_dict') else label for label in self.labels],
            'boundingBox': [box.to_dict() if hasattr(box, 'to_dict') else box for box in self.boundingBox]
        }
