import os
import cv2
import numpy as np
from deepface import DeepFace

#https://github.com/kb22/Create-Face-Data-from-Images
PADDING = 25

MODELS = ["VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib"]
METRICS = ["cosine", "euclidean", "euclidean_l2"]
BACKENDS = ['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface']

MODEL = MODELS[1]
METRIC = METRICS[2]
BACKEND = BACKENDS[3]

class faceOperator():

	def __init__(self,model_data_path):
		self.deepFace_model = DeepFace.build_model(MODELS[2])
		self.openCV_model = cv2.dnn.readNetFromCaffe(model_data_path+'deploy.prototxt', model_data_path+'weights.caffemodel')

	def export_similar(self,faces,output_path):
		
		#Remove non recognizable faces
		i = 0
		while i < len(faces):
			img_name, face = faces[i]
			try:
				DeepFace.detectFace(face, detector_backend=BACKEND) # ,detector_backend=BACKEND
				i=i+1
			except Exception:
				faces.pop(i)
		recognizableFaces = len(faces)

		#Export similar faces
		suspectID = 0
		while 0 < len(faces):
			suspect = 'suspect-'+str(suspectID)
			if not os.path.exists(output_path+'/'+suspect):
				os.makedirs(output_path+'/'+suspect)
			j = 0
			img_name1, face1 = faces[0]
			while j < len(faces):
				img_name2, face2 = faces[j]
				result = DeepFace.verify(face1, face2, model_name=MODEL, distance_metric=METRIC, model=self.deepFace_model, detector_backend=BACKEND, prog_bar=True)
				if result['verified']:
					cv2.imwrite(output_path+'/'+suspect+'/'+img_name2, face2)
					faces.pop(j)
				else:
					j = j+1
			suspectID = suspectID+1
		return recognizableFaces
	def find_faces(self,byteImg,img_name):
		image = cv2.imdecode(np.frombuffer(byteImg, np.uint8), -1)
		(h, w) = image.shape[:2]
		blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
		self.openCV_model.setInput(blob)
		detections = self.openCV_model.forward()
		facesTuples = []
		faceCount = 0
		# Identify each face
		for i in range(0, detections.shape[2]):
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")
			confidence = detections[0, 0, i, 2]
			# If confidence > 0.5, save it as a separate file
			if (confidence > 0.5):
				faceCount=faceCount+1
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
				face_img_name = 'face_'+str(faceCount)+'_'+img_name
				facesTuples.append([face_img_name, image[startY:endY, startX:endX]]) #e.g tuple [123456789.jpg , [ndarray]]
		return facesTuples