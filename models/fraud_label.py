from utils.enums import TypeLabel


class FraudLabel:
    def __init__(self, idLabel=None, description=None, typeLabel=None):
        self.idLabel = idLabel
        self.description = description
        self.typeLabel = typeLabel

    def to_dict(self):
        label_dict = {
            'idLabel': self.idLabel,
            'description': self.description,
            'typeLabel': self.typeLabel.value if isinstance(self.typeLabel, TypeLabel) else self.typeLabel
        }

        return label_dict

    @classmethod
    def from_dict(cls, data):
        label = cls()
        label.idLabel = data.get('idLabel')
        label.description = data.get('description')

        type_label = data.get('typeLabel')
        if type_label:
            try:
                label.typeLabel = TypeLabel(type_label)
            except ValueError:
                label.typeLabel = type_label

        return label
