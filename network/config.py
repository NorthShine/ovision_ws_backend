MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

faceProto = "network/weights/opencv_face_detector.pbtxt"
faceModel = "network/weights/opencv_face_detector_uint8.pb"

ageProto = "network/weights/age_deploy.prototxt"
ageModel = "network/weights/age_net.caffemodel"

genderProto = "network/weights/gender_deploy.prototxt"
genderModel = "network/weights/gender_net.caffemodel"


