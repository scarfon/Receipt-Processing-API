
import logging
import uuid
import os
import azure.functions as func
import cv2
import numpy as np
import requests
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient


def main(req: func.HttpRequest) -> func.HttpResponse:
	logging.info('Python HTTP trigger function processed a request.')

	imgUrl = req.params.get('imgUrl')
	if not imgUrl:
		try:
			req_body = req.get_json()
		except ValueError:
			pass
		else:
			imgUrl = req_body.get('imgUrl')
	
	if imgUrl:
		response = {}
		# Get image from URL
		img_data = requests.get(imgUrl).content
		nparr = np.frombuffer(img_data, np.uint8)
		image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
		original_image = image.copy()

		# Preprocess image
		try:
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 101, 1)
			contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			largest_contour = max(contours, key=cv2.contourArea)
			x, y, w, h = cv2.boundingRect(largest_contour)
			x1 = x
			y1 = y
			x2 = x + w
			y2 = y + h
			cropped_image = original_image[y1:y2, x1:x2]
			kernel = np.array([[1,0,0], [0,1.8,0], [0,0,-1]])
			cropped_image = cv2.filter2D(cropped_image, -1, kernel)
			cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
			cropped_image = cv2.equalizeHist(cropped_image)
			cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2BGR)   
		except Exception as e:
			response['error'] = e
			cropped_image = original_image

		# Call Document AI Receipt API
		try:
			endpoint = os.environ["ENDPOINT"]
			key = os.environ["KEY_DI"]
			form_recognizer_client = FormRecognizerClient(endpoint, AzureKeyCredential(key))
			image_bytes = cv2.imencode('.jpg', cropped_image)[1].tobytes()	
			poller = form_recognizer_client.begin_recognize_receipts(receipt=image_bytes)
			receipts = poller.result()
		except Exception as e:
			return func.HttpResponse(f"{e}", status_code=400)

		response['uuid'] = uuid.uuid4()

		try:
			connect_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
			container_name = "imagens"
			blob_name = f"{str(response['uuid'])}.jpg"
			blob_service_client = BlobServiceClient.from_connection_string(connect_str)
			container_client = blob_service_client.get_container_client(container_name)
			blob_client = container_client.get_blob_client(blob_name)
			blob_client.upload_blob(image_bytes, overwrite=True)
			img_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
			response['imgUrl'] = img_url
		except Exception as e:
			response['error'] = e

		# Parse response 
		for idx, receipt in enumerate(receipts):
			print("--------Analysis of receipt #{}--------")
			merchant_name = receipt.fields.get("MerchantName")
			response["merchant_name"] = (merchant_name.value, merchant_name.confidence) if merchant_name else ("", 0.0)
			transaction_date = receipt.fields.get("TransactionDate")
			response["transaction_date"] = (transaction_date.value, transaction_date.confidence) if transaction_date else ("", 0.0)
			if receipt.fields.get("Items"):
				response["items"] = []
				for idx, item in enumerate(receipt.fields.get("Items").value):
					iteml = {}
					item_description = item.value.get("Description")
					iteml["description"] = (item_description.value, item_description.confidence) if item_description else ("", 0.0)
					item_quantity = item.value.get("Quantity")
					iteml["quantity"] = (item_quantity.value, item_quantity.confidence) if item_quantity else ("", 0.0)
					item_price = item.value.get("Price")
					iteml["price"] = (item_price.value, item_price.confidence) if item_price else ("", 0.0)
					item_total_price = item.value.get("TotalPrice")
					iteml["total_price"] = (item_total_price.value, item_total_price.confidence) if item_total_price else ("", 0.0)
					response["items"].append(iteml)
			else :
				response["items"] = []
			subtotal = receipt.fields.get("Subtotal")
			response["subtotal"] = (subtotal.value, subtotal.confidence) if subtotal else ("", 0.0)
			tax = receipt.fields.get("TotalTax")
			response["tax"] = (tax.value, tax.confidence) if tax else ("", 0.0)
			tip = receipt.fields.get("Tip")
			response["tip"] = (tip.value, tip.confidence) if tip else ("", 0.0)
			total = receipt.fields.get("Total") 
			response["total"] = (total.value, total.confidence) if total else ("", 0.0)

		return func.HttpResponse(f"{response}")
	else:
		return func.HttpResponse(
			 f"This HTTP triggered function executed successfully. Pass an imgUrl in the query string or in the request body for a personalized response.\n",
			 status_code=200
		)
