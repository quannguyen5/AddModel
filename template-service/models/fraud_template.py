from datetime import datetime


class FraudTemplate:
    def __init__(self, idTemplate=None, description=None, imageUrl=None, timeUpdate=None, labels=None, boundingBox=None):
        self.idTemplate = idTemplate
        self.description = description
        self.imageUrl = imageUrl
        self.timeUpdate = timeUpdate if timeUpdate else datetime.now()
        self.labels = labels if labels else []
        self.boundingBox = boundingBox if boundingBox else []

    def to_dict(self):
        template_dict = {
            'idTemplate': self.idTemplate,
            'description': self.description,
            'imageUrl': self.imageUrl,
            'timeUpdate': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else self.timeUpdate
        }
        if self.labels:
            template_dict['labels'] = [
                label.to_dict() if hasattr(label, 'to_dict') else label
                for label in self.labels
            ]
        if self.boundingBox:
            template_dict['boundingBox'] = [
                box.to_dict() if hasattr(box, 'to_dict') else box
                for box in self.boundingBox
            ]
        return template_dict
