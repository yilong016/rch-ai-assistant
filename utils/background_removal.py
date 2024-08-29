import base64
import io
import json
import logging
import boto3
from PIL import Image
from botocore.exceptions import ClientError

def background_removal_titan(filename):
    """
    Entrypoint for Amazon Titan Image Generator V2 example.
    task: background removal
    """
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")
        model_id = 'amazon.titan-image-generator-v2:0'
        # Read image from file and encode it as base64 string.
        input_image = load_and_resize_image(filename)
        # Build parameters
        body = json.dumps({
            "taskType": "BACKGROUND_REMOVAL",
            "backgroundRemovalParams": {
                "image": input_image,
            }
        })
        image_bytes = generate_image(model_id=model_id,body=body)
        return image_bytes
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " +
              format(message))
    except ImageError as err:
        logger.error(err.message)
        print(err.message)
    else:
        print(
            f"Finished generating image with Amazon Titan Image Generator V2 model {model_id}.")

def load_and_resize_image(image_path, max_size=1408):
    with Image.open(image_path) as img:
        # 如果图片的宽度或高度超过max_size，就进行缩放
        if img.width > max_size or img.height > max_size:
            # 计算缩放比例
            scale = max_size / max(img.width, img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # 将图片转换为PNG格式的字节流
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")

        # 进行base64编码
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return encoded_image


def generate_image(model_id, body):
    """
    Generate an image using Amazon Titan Image Generator V2 model on demand.
    Args:
        model_id (str): The model ID to use.
        body (str) : The request body to use.
    Returns:
        image_bytes (bytes): The image generated by the model.
    """
    logger.info(
        "Generating image with Amazon Titan Image Generator V2 model %s", model_id)
    bedrock = boto3.client(service_name='bedrock-runtime',region_name='us-west-2')
    accept = "application/json"
    content_type = "application/json"
    response = bedrock.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())
    base64_image = response_body.get("images")[0]
    base64_bytes = base64_image.encode('ascii')
    image_bytes = base64.b64decode(base64_bytes)
    finish_reason = response_body.get("error")
    if finish_reason is not None:
        raise ImageError(f"Image generation error.Error is {finish_reason}")
    logger.info(
        "Successfully generated image with Amazon Titan Image Generator V2 model %s", model_id)
    return image_bytes
  
class ImageError(Exception):
    "Custom exception for errors returned by Amazon Titan Image Generator V2"
    def __init__(self, message):
        self.message = message
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
