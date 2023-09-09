
import logging
import uuid
import os
import azure.functions as func
import cv2
import numpy as np
import requests
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential


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
        # Call Document AI Receipt API
        endpoint = os.environ["ENDPOINT"]
        key = os.environ["KEY_DI"]
        form_recognizer_client = FormRecognizerClient(endpoint, AzureKeyCredential(key))
        img_data = requests.get(imgUrl).content
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
        poller = form_recognizer_client.begin_recognize_receipts(receipt=image_bytes)
        receipts = poller.result()

        response = {
            "uid": uuid.uuid4(),
        }

        for idx, receipt in enumerate(receipts):
            print("--------Analysis of receipt #{}--------")
            merchant_name = receipt.fields.get("MerchantName")
            if merchant_name:
                response["merchant_name"] = (merchant_name.value, merchant_name.confidence)
            transaction_date = receipt.fields.get("TransactionDate")
            if transaction_date:
                response["transaction_date"] = (transaction_date.value, transaction_date.confidence)
            if receipt.fields.get("Items"):
                response["items"] = []
                print("Receipt items:")
                for idx, item in enumerate(receipt.fields.get("Items").value):
                    iteml = {}
                    item_description = item.value.get("Description")
                    if item_description:
                        iteml["description"] = (item_description.value, item_description.confidence)
                    item_quantity = item.value.get("Quantity")
                    if item_quantity:
                        iteml["quantity"] = (item_quantity.value, item_quantity.confidence)
                    item_price = item.value.get("Price")
                    if item_price:
                        iteml["price"] = (item_price.value, item_price.confidence)
                    item_total_price = item.value.get("TotalPrice")
                    if item_total_price:
                        iteml["total_price"] = (item_total_price.value, item_total_price.confidence)
                    response["items"].append(iteml)
            subtotal = receipt.fields.get("Subtotal")
            if subtotal:
                response["subtotal"] = (subtotal.value, subtotal.confidence)
            tax = receipt.fields.get("TotalTax")
            if tax:
                response["tax"] = (tax.value, tax.confidence)
            tip = receipt.fields.get("Tip")
            if tip:
                response["tip"] = (tip.value, tip.confidence)
            total = receipt.fields.get("Total")
            if total:
                response["total"] = (total.value, total.confidence)

        return func.HttpResponse(f"{response}")
    else:
        return func.HttpResponse(
             f"This HTTP triggered function executed successfully. Pass an imgUrl in the query string or in the request body for a personalized response.\n {os.environ['ENDPOINT']}\n {os.environ['KEY_DI']}",
             status_code=200
        )
