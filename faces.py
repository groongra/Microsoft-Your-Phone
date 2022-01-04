import cv2
import numpy as np
from deepface import DeepFace

#https://github.com/kb22/Create-Face-Data-from-Images
PADDING = 25

MODELS = ["VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib"]
METRICS = ["cosine", "euclidean", "euclidean_l2"]
BACKENDS = ['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface']

class face_comparer():

	def __init__(self):
		self.model = DeepFace.build_model(MODELS[2])

class face_extractor():
	# Define paths
	#base_dir = os.path.dirname(__file__)
	#prototxt_path = os.path.join(base_dir + 'model_data/deploy.prototxt')
	#caffemodel_path = os.path.join(base_dir + 'model_data/weights.caffemodel')

	# Read the model
	#model = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)

	def __init__(self,model_data_path):
		self.model = cv2.dnn.readNetFromCaffe(model_data_path+'deploy.prototxt', model_data_path+'weights.caffemodel')

	def find_faces(self,byteImg):
		image = cv2.imdecode(np.frombuffer(byteImg, np.uint8), -1)
		(h, w) = image.shape[:2]
		blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
		self.model.setInput(blob)
		detections = self.model.forward()
		foundFaces = []
		# Identify each face
		for i in range(0, detections.shape[2]):
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			confidence = detections[0, 0, i, 2]
			# If confidence > 0.5, save it as a separate file
			if (confidence > 0.5):
				if(startY-PADDING>=0):
					startY = startY - PADDING
				else: 
					startY = 0
				if(endY+PADDING<=h):
					endY = endY + PADDING
				else:
					endY = h
				if(startX-PADDING>=0):
					startX = startX - PADDING
				else:
					startX = 0
				if(endX+PADDING<=w):
					endX = endX + PADDING
				else: 
					endX = w
				foundFaces.append(image[startY:endY, startX:endX])
		return(foundFaces)

	def extract_face(self, byteImg, output_path, filename):
		facesFound = self.find_faces(byteImg)
		i = 0
		for face in facesFound:
			cv2.imwrite(output_path+'/face_'+str(i)+'_'+filename, face)
			i=i+1