class BoundingBox:
    def __init__(self, idBox=None, xCenter=None, yCenter=None, width=None, height=None,
                 xPixel=None, yPixel=None, widthPixel=None, heightPixel=None, fraudLabelId=None):
        self.idBox = idBox
        self.xCenter = xCenter
        self.yCenter = yCenter
        self.width = width
        self.height = height
        self.xPixel = xPixel
        self.yPixel = yPixel
        self.widthPixel = widthPixel
        self.heightPixel = heightPixel
        self.fraudLabelId = fraudLabelId

    def to_dict(self):
        return {
            'idBox': self.idBox,
            'xCenter': self.xCenter,
            'yCenter': self.yCenter,
            'width': self.width,
            'height': self.height,
            'xPixel': self.xPixel,
            'yPixel': self.yPixel,
            'widthPixel': self.widthPixel,
            'heightPixel': self.heightPixel,
            'fraudLabelId': self.fraudLabelId
        }
