import cv2
import cv2.dnn
import numpy as np

from network.config import *

faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)

padding = 20


def faceBox(faceNet, frame: np.array) -> np.array:
    frameWidth = frame.shape[1]
    frameHeight = frame.shape[0]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (227, 227), [104, 117, 123], swapRB=False)
    faceNet.setInput(blob)
    detection = faceNet.forward()
    bboxs = []
    for i in range(detection.shape[2]):
        confidence = detection[0, 0, i, 2]
        if confidence > 0.7:
            x1 = int(detection[0, 0, i, 3] * frameWidth)
            y1 = int(detection[0, 0, i, 4] * frameHeight)
            x2 = int(detection[0, 0, i, 5] * frameWidth)
            y2 = int(detection[0, 0, i, 6] * frameHeight)
            bboxs.append([x1, y1, x2, y2])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

    return frame, bboxs


def transform(frame: np.array, facenet: cv2.dnn_Net, gendernet: cv2.dnn_Net, agenet: cv2.dnn_Net) -> np.array:
    frame, bboxs = faceBox(facenet, frame)
    if not bboxs:
        return frame

    for bbox in bboxs:
        face = frame[max(0, bbox[1] - padding):min(bbox[3] + padding, frame.shape[0] - 1),
               max(0, bbox[0] - padding):min(bbox[2] + padding, frame.shape[1] - 1)]
        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227),
                                     MODEL_MEAN_VALUES, swapRB=False)

        gendernet.setInput(blob)
        genderPred = gendernet.forward()
        gender = genderList[genderPred[0].argmax()]

        agenet.setInput(blob)
        agePred = agenet.forward()
        age = ageList[agePred[0].argmax()]

        label = "{}, {}".format(gender, age)
        cv2.rectangle(frame, (bbox[0], bbox[1] - 30), (bbox[2], bbox[1]),
                      (0, 255, 0), -1)
        cv2.putText(frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_PLAIN,
                    0.8, (255, 255, 255), 2)

        return frame

# img = cv2.imread('weights/1.jpg', 1)
# cv2.imwrite('weights/2.jpg', transform(img))
