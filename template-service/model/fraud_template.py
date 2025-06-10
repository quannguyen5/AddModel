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

    @classmethod
    def from_dict(cls, data):
        from .fraud_label import FraudLabel
        from .bounding_box import BoundingBox
        template = cls()
        template.idTemplate = data.get('idTemplate')
        template.description = data.get('description')
        template.imageUrl = data.get('imageUrl')
        time_update = data.get('timeUpdate')
        if time_update and isinstance(time_update, str):
            try:
                template.timeUpdate = datetime.strptime(
                    time_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                template.timeUpdate = time_update
        else:
            template.timeUpdate = time_update

        labels_data = data.get('labels')
        if labels_data:
            template.labels = [
                FraudLabel.from_dict(label) if isinstance(label, dict) else label
                for label in labels_data
            ]

        boxes_data = data.get('boundingBox')
        if boxes_data:
            template.boundingBox = [
                BoundingBox.from_dict(box) if isinstance(box, dict) else box
                for box in boxes_data
            ]

        return template