import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
import base64
import boto3
import uuid
import os
from dotenv import load_dotenv
import logging

# Khởi tạo FastAPI
app = FastAPI()
load_dotenv()


logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)  # Set mức độ log, có thể là INFO, DEBUG, ERROR, ...

# Handler để ghi log vào terminal hoặc file
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Bạn có thể sử dụng logger trong mã
logger.debug("Logger initialized successfully")




app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các domain
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, v.v.)
    allow_headers=["*"],  # Cho phép tất cả các header
)

class Request(BaseModel):
  prompt: str


@app.post("/test/")
async def generate_slogan_api():
    return {"data": "Hello, I'm AImar "}



@app.post("/slogan/") # 'http://47.84.52.44:8000/slogan'
async def generate_slogan_api( request: Request):
    prompt =  request.prompt
    slogan = generate_slogan(prompt)
    if "Error" in slogan:
        raise HTTPException(status_code=400, detail=slogan)
    return {"data": slogan}


@app.post("/content/")
async def generate_content_api(request: Request):
    prompt =  request.prompt
    logger.debug(f"Prompt for content: {prompt}")

    content = generate_content(prompt)
    if "Error" in content:
        raise HTTPException(status_code=400, detail=content)
    return {"data" : content}


@app.post("/image/")
async def generate_image_api( request: Request):
    prompt = request.prompt
    logger.debug(f"Prompt: {prompt}")
    response = generate_image(prompt)
    if "Error" in response:
        raise HTTPException(status_code=400, detail=response)
    return {"data": response}



def generate_slogan(prompt):
  response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "deepseek/deepseek-chat:free",
    "messages": [
      {"role": "system",   "content": "Bạn là một chuyên gia hàng đầu trong lĩnh vực xây dựng thương hiệu và marketing. Khách hàng của bạn là những người kinh doanh đa dạng sản phẩm. Nhiệm vụ của bạn là tạo ra những slogan ngắn gọn, sắc sảo, dễ nhớ và truyền cảm hứng, giúp sản phẩm ghi dấu ấn mạnh mẽ trong tâm trí khách hàng mục tiêu." },
      {"role": "user", "content": prompt }

    ]
 }
)
  )
  if response.status_code == 200:
    result = response.json()
    return result["choices"][0]["message"]["content"]


def generate_content(prompt):
  response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "deepseek/deepseek-chat:free",
    "messages": [
      {"role": "system",   "content": "Bạn là một chuyên gia hàng đầu trong lĩnh vực xây dựng thương hiệu và marketing. Khách hàng của bạn là những người kinh doanh đa dạng ngành hàng. Nhiệm vụ của bạn là tạo ra những nội dung hấp dẫn, thuyết phục và phù hợp với mục tiêu tiếp thị của họ." },
      {"role": "user", "content": prompt }

    ]
 }
)
  )
  if response.status_code == 200:
    result = response.json()
    return result["choices"][0]["message"]["content"]
  else:
    return f"❌ Error {response.status_code}: {response.text}"




def generate_image(prompt):
    url = "https://ir-api.myqa.cc/v1/openai/images/generations"
    headers = {
        "Authorization": "Bearer f710984a37f3e81d39ff9efdee2d3150bce926a16a920e22bfc32a9098ca9c58",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "model": "black-forest-labs/FLUX-1-schnell:free"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        # Giả sử response có trường `b64_json`
        data = response.json()
        base64_image =  data["data"][0]["b64_json"]

        if base64_image:
            return upload_base64_to_s3(base64_image, "image-bluetech")
        
        elif response.status_code == 307:
          return f"❌ Redirect: {response.headers.get('Location')}"
    
        else:
            return "❌ Error: Không tìm thấy hình ảnh trong response."
    else:
        return f"❌ Error {response.status_code}: {response.text}"
   


def upload_base64_to_s3(base64_data, bucket_name, region_name='ap-southeast-1'):
    image_data = base64.b64decode(base64_data)

    filename = f"CNPM/image_{uuid.uuid4().hex}.png"

    s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

    s3.put_object(
        Bucket="image-bluetech",
        Key=filename,
        Body=image_data,
        ContentType='image/png',
    )
    return f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{filename}"
