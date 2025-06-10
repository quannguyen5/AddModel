class BoundingBox:
    def __init__(self, idBox=None, xCenter=None, yCenter=None, width=None, height=None,
                 xPixel=None, yPixel=None, widthPixel=None, heightPixel=None,
                 fraudTemplateId=None, fraudLabelId=None):
        self.idBox = idBox
        self.xCenter = xCenter
        self.yCenter = yCenter
        self.width = width
        self.height = height
        self.xPixel = xPixel
        self.yPixel = yPixel
        self.widthPixel = widthPixel
        self.heightPixel = heightPixel
        self.fraudTemplateId = fraudTemplateId
        self.fraudLabelId = fraudLabelId

    def to_dict(self):
        box_dict = {
            'idBox': self.idBox,
            'xCenter': self.xCenter,
            'yCenter': self.yCenter,
            'width': self.width,
            'height': self.height,
            'xPixel': self.xPixel,
            'yPixel': self.yPixel,
            'widthPixel': self.widthPixel,
            'heightPixel': self.heightPixel,
            'fraudTemplateId': self.fraudTemplateId,
            'fraudLabelId': self.fraudLabelId
        }
        return box_dict

    @classmethod
    def from_dict(cls, data):
        box = cls()
        box.idBox = data.get('idBox')
        box.xCenter = data.get('xCenter')
        box.yCenter = data.get('yCenter')
        box.width = data.get('width')
        box.height = data.get('height')
        box.xPixel = data.get('xPixel')
        box.yPixel = data.get('yPixel')
        box.widthPixel = data.get('widthPixel')
        box.heightPixel = data.get('heightPixel')
        box.fraudTemplateId = data.get('fraudTemplateId')
        box.fraudLabelId = data.get('fraudLabelId')
        return box