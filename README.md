# API de Processamento de Recibos 

Esta é uma função Python HTTP trigger que recupera uma imagem de recibo de uma URL, pré-processa a imagem e extrai informações do recibo usando o serviço Azure Form Recognizer. As informações extraídas são retornadas como uma resposta JSON.

Pré-requisitos Para usar esta função, você precisará de:

* Uma assinatura do Azure
* Um recurso Azure Form Recognizer
* Um ambiente de desenvolvimento Python com os seguintes pacotes instalados:
  * ``azure-functions``
  * ``azure-ai-formrecognizer``
  * ``azure-core``
  * ``opencv-python-headless``
  * ``numpy``
  * ``requests``

## Uso
Para usar a função, envie uma solicitação HTTP para a URL da função com os seguintes parâmetros:

* ``imgUrl``: A URL da imagem do recibo a ser processada.



# Receipt Processing API
This is a Python HTTP trigger function that retrieves a receipt image from a URL, preprocesses the image, and extracts information from the receipt using the Azure Form Recognizer service. The extracted information is returned as a JSON response.

Prerequisites
To use this function, you will need:

* An Azure subscription
* An Azure Form Recognizer resource
* A Python development environment with the following packages installed:
  * ``azure-functions``
  * ``azure-ai-formrecognizer``
  * ``azure-core``
  * ``opencv-python-headless``
  * ``numpy``
  * ``requests``

## Usage
To use the function, send an HTTP request to the function URL with the following parameters:

* ``imgUrl``: The URL of the receipt image to process.

