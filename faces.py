import os
import io
from re import search
from traceback import format_exc
import cv2
from PIL import Image   
import numpy as np
from deepface import DeepFace

#https://github.com/kb22/Create-Face-Data-from-Images
PADDING = 25

MODELS = ["VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib"]
METRICS = ["cosine", "euclidean", "euclidean_l2"]
BACKENDS = ['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface']

MODEL = MODELS[0]
METRIC = METRICS[2]
BACKEND = BACKENDS[0]
PROG_BAR = False

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
	
	def equal_face_profiles(self,profile1,profile2,age_compare_sign):
		if(len(profile1) == len(profile2)):
			if(profile1[0]=='Null' or profile2[0]=='Null' or age_compare_sign=='Null'):
				pass
			elif(age_compare_sign =='==' and int(profile1[0]) == int(profile2[0])):
				pass
			elif(age_compare_sign =='!=' and int(profile1[0]) != int(profile2[0])):
				pass
			elif(age_compare_sign =='<=' and int(profile1[0]) <= int(profile2[0])):
				pass
			elif(age_compare_sign =='>=' and int(profile1[0]) >= int(profile2[0])):
				pass
			elif(age_compare_sign =='<' and int(profile1[0]) < int(profile2[0])):
				pass
			elif(age_compare_sign =='<' and int(profile1[0]) < int(profile2[0])):
				pass
			else:
				return False
			i = 1
			while i < len(profile1):
				if(profile1[i] != profile2[i]):
					if(profile1[i]=='Null' or profile2[i]=='Null'):
						pass
					else:
						return False
				i=i+1
			return True
		return False	
				
	def search_face_profile(self,faces,searchProfiles,output_path):
		#Remove non recognizable faces
		i = 0
		while i < len(faces):
			img_name, face = faces[i]
			try:
				DeepFace.detectFace(face, detector_backend=BACKEND) # ,detector_backend=BACKEND
				i=i+1
			except Exception:
				faces.pop(i)

		recognizableFaces = 0

		#Export similar faces
		for searchProfile in searchProfiles:
			searchProfileFolder = output_path+'/'+str(searchProfile[1:])
			if not os.path.exists(searchProfileFolder):
				os.makedirs(searchProfileFolder)
			i=0
			while i < len(faces):
				img_name, face = faces[i]
				try:
					faceProfile = DeepFace.analyze(face, actions = ['age', 'gender', 'race', 'emotion'], prog_bar=PROG_BAR)
					faceProfile = [str(faceProfile["age"]),faceProfile["dominant_race"],faceProfile["dominant_emotion"],faceProfile["gender"]]
					if(self.equal_face_profiles(searchProfile[1:],faceProfile,searchProfile[0])):
						cv2.imwrite(searchProfileFolder+'/'+img_name, face)
						recognizableFaces = recognizableFaces+1
				except Exception:
					pass
				i=i+1

		return recognizableFaces
		
	def search_faces(self,faces,searchFaces,output_path):
		
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

		#Remove non recognizable search faces
		i = 0
		while i < len(searchFaces):
			img_name, face = searchFaces[i]
			try:
				DeepFace.detectFace(face, detector_backend=BACKEND) # ,detector_backend=BACKEND
				i=i+1
			except Exception:
				searchFaces.pop(i)
		recognizableSearchFaces = len(searchFaces)

		#Export matched faces
		i = 0
		while i < len(searchFaces):
			img_name1, face1 = searchFaces[i]
			j = 0
			while j < len(faces):
				img_name2, face2 = faces[j]
				result = DeepFace.verify(face1, face2, model_name=MODEL, distance_metric=METRIC, model=self.deepFace_model, detector_backend=BACKEND, prog_bar=True)
				if result['verified']:
					if not os.path.exists(output_path+'/'+img_name1):
						os.makedirs(output_path+'/'+img_name1)
					cv2.imwrite(output_path+'/'+img_name1+'/'+img_name2, face2)
				j = j+1
			i= i+1
		return recognizableFaces, recognizableSearchFaces
	
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

	def obtain_faces_from_images_folder(self, path):
		search_face_tuples = []
		valid_images = [".jpg",".gif",".png",".tga"]
		for f in os.listdir(path):
			filename,ext = os.path.splitext(f)
			if ext.lower() not in valid_images:
				continue
			b = io.BytesIO()
			image = Image.open(path+'/'+f)
			image.save(b, format='png')
			search_face_tuples.extend(self.find_faces(b.getvalue(),filename))
		return search_face_tuples
        