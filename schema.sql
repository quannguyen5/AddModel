-- Xóa bảng nếu tồn tại để tránh lỗi
DROP TABLE IF EXISTS ModelType;
DROP TABLE IF EXISTS TypeLabel;
DROP TABLE IF EXISTS BoundingBox;
DROP TABLE IF EXISTS FraudLabel;
DROP TABLE IF EXISTS FraudTemplate;
DROP TABLE IF EXISTS TrainingLost;
DROP TABLE IF EXISTS TrainInfo;
DROP TABLE IF EXISTS TrainingData;
DROP TABLE IF EXISTS Model;

-- Bảng ModelType - Enumeration
CREATE TABLE ModelType (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Bảng TypeLabel - Enumeration
CREATE TABLE TypeLabel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Bảng Model
CREATE TABLE Model (
    idModel INT AUTO_INCREMENT PRIMARY KEY,
    modelName VARCHAR(100) NOT NULL,
    modelType VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    lastUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trainInfoId INT NULL,  -- Foreign key tới TrainInfo
    CONSTRAINT UNIQUE_MODEL_NAME_VERSION UNIQUE (modelName, version)
);

-- Bảng TrainInfo
CREATE TABLE TrainInfo (
    idInfo INT AUTO_INCREMENT PRIMARY KEY,
    epoch INT NOT NULL,
    learningRate FLOAT NOT NULL,
    batchSize INT NOT NULL,
    mae FLOAT,
    mse FLOAT,
    trainDuration INT,
    accuracy FLOAT,
    timeTrain VARCHAR(50)
);

-- Bảng TrainingLost
CREATE TABLE TrainingLost (
    idTrainingLost INT AUTO_INCREMENT PRIMARY KEY,
    epoch INT NOT NULL,
    lost FLOAT NOT NULL,
    trainInfoId INT NOT NULL,
    FOREIGN KEY (trainInfoId) REFERENCES TrainInfo(idInfo) ON DELETE CASCADE
);

-- Bảng FraudTemplate
CREATE TABLE FraudTemplate (
    idTemplate INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    imageUrl VARCHAR(255) NOT NULL,
    timeUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng FraudLabel
CREATE TABLE FraudLabel (
    idLabel INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    typeLabel VARCHAR(50) NOT NULL,
    fraudTemplateId INT NOT NULL,
    FOREIGN KEY (fraudTemplateId) REFERENCES FraudTemplate(idTemplate) ON DELETE CASCADE
);

-- Bảng BoundingBox
CREATE TABLE BoundingBox (
    idBox INT AUTO_INCREMENT PRIMARY KEY,
    xCenter FLOAT NOT NULL,
    yCenter FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    xPixel INT,
    yPixel INT,
    widthPixel INT,
    heightPixel INT,
    fraudLabelId INT NOT NULL,
    FOREIGN KEY (fraudLabelId) REFERENCES FraudLabel(idLabel) ON DELETE CASCADE
);

-- Bảng TrainingData
CREATE TABLE TrainingData (
    idTrainingData INT AUTO_INCREMENT PRIMARY KEY,
    timeUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    modelId INT NOT NULL,
    fraudTemplateId INT NOT NULL,
    FOREIGN KEY (modelId) REFERENCES Model(idModel) ON DELETE CASCADE,
    FOREIGN KEY (fraudTemplateId) REFERENCES FraudTemplate(idTemplate) ON DELETE CASCADE
);

-- Thêm dữ liệu vào bảng ModelType
INSERT INTO ModelType (name) VALUES ('HumanDetection'), ('FraudDetection');

-- Thêm dữ liệu vào bảng TypeLabel
INSERT INTO TypeLabel (name) VALUES ('HumanDetect'), ('literal');

-- Thêm dữ liệu mẫu
-- Thêm vào bảng TrainInfo
INSERT INTO TrainInfo (epoch, learningRate, batchSize, mae, mse, trainDuration, accuracy, timeTrain) 
VALUES (100, 0.001, 16, 0.05, 0.02, 120, 0.85, '2025-04-20 10:00:00');

-- Thêm vào bảng Model
INSERT INTO Model (modelName, modelType, version, description, lastUpdate, trainInfoId) 
VALUES ('YOLOv8-Person', 'HumanDetection', 'v1.0.0', 'Model để phát hiện người', '2025-04-20 10:15:00', 1);

-- Thêm vào bảng TrainingLost
INSERT INTO TrainingLost (epoch, lost, trainInfoId)
VALUES (1, 0.7, 1), (50, 0.3, 1), (100, 0.12, 1);

-- Thêm vào bảng FraudTemplate
INSERT INTO FraudTemplate (description, imageUrl, timeUpdate)
VALUES ('Mẫu người', '/static/placeholder-camera.jpg', '2025-04-15 14:30:00'),
       ('Mẫu xe ô tô', '/static/placeholder-camera.jpg', '2025-04-16 09:00:00'),
       ('Mẫu xe đạp', '/static/placeholder-camera.jpg', '2025-04-17 10:30:00');

-- Thêm vào bảng FraudLabel
INSERT INTO FraudLabel (description, typeLabel, fraudTemplateId) 
VALUES ('Nhãn người', 'HumanDetect', 1),
       ('Nhãn xe ô tô', 'literal', 2),
       ('Nhãn xe đạp', 'literal', 3);

-- Thêm vào bảng BoundingBox
INSERT INTO BoundingBox (xCenter, yCenter, width, height, xPixel, yPixel, widthPixel, heightPixel, fraudLabelId) 
VALUES (0.5, 0.5, 0.3, 0.7, 320, 240, 150, 350, 1),
       (0.6, 0.4, 0.4, 0.3, 380, 200, 200, 150, 2),
       (0.3, 0.6, 0.2, 0.2, 150, 300, 100, 100, 3);

-- Thêm vào bảng TrainingData
INSERT INTO TrainingData (description, modelId, fraudTemplateId) 
VALUES ('Dữ liệu huấn luyện cho mô hình phát hiện người', 1, 1);