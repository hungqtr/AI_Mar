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


@app.post("/image/")
async def generate_image_api( request: Request):
    # 1.1.5    Nhận mô tả của người dùng
    prompt = request.prompt
    logger.debug(f"Prompt: {prompt}")
    #1.1.6    Gọi hàm generate_image(prompt) với mô tả của người dùng.
    response = generate_image(prompt) #1.1.13    generate_image() trả URL về cho generate_image_api
    if "Error" in response:
        raise HTTPException(status_code=400, detail=response)
    # 1.1.14    generate_image_api trả về kết quả (URL) cho index.js
    return {"data": response}

def generate_image(prompt):
    # 1.1.7    Chuẩn bị request để gửi yêu cầu đến ImageRouter
    url = "https://ir-api.myqa.cc/v1/openai/images/generations"
    headers = {
        "Authorization": "Bearer f710984a37f3e81d39ff9efdee2d3150bce926a16a920e22bfc32a9098ca9c58",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "model": "black-forest-labs/FLUX-1-schnell:free"
    }
    # 1.1.8	Gửi request đến ImageRouter
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 1.1.9	ImageRouter gửi phản hồi về
    if response.status_code == 200:
        # 1.1.10	Xử lý phản hồi từ ImageRouter gửi về
        data = response.json()
        # 1.1.10.1	Lấy chuỗi Base64 từ phản hồi gửi về.
        base64_image =  data["data"][0]["b64_json"]
        # 1.1.10.2	Gọi hàm upload_base64_to_s3(base64_image, "image-bluetech") nếu lấy được chuỗi Base64 từ phản hồi.
        if base64_image:
            return upload_base64_to_s3(base64_image, "image-bluetech") #1.1.12     generate_image() nhận URL từ hàm upload_base64_to_s3(base64_image, "image-bluetech")
        # 1.4.1. ImageRouter được gọi trong generate_image trả lỗi về cho generate_image_api.
        elif response.status_code == 307:
          return f"❌ Redirect: {response.headers.get('Location')}"
        else:
            return "❌ Error: Không tìm thấy hình ảnh trong response."
    else:
        return f"❌ Error {response.status_code}: {response.text}"
# 1.1.11    Thực hiện hàm upload_base64_to_s3(base64_image, "image-bluetech")   
def upload_base64_to_s3(base64_data, bucket_name, region_name='ap-southeast-1'):
    # 1.1.11.1	Giải mã chuỗi Base64.
    image_data = base64.b64decode(base64_data)
    # 1.1.11.2	Tạo tên file
    filename = f"CNPM/image_{uuid.uuid4().hex}.png"
    # 1.1.11.3	Khởi tạo S3 Client
    s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)
    # 1.1.11.4	Đẩy ảnh lên S3
    s3.put_object(
        Bucket="image-bluetech",
        Key=filename,
        Body=image_data,
        ContentType='image/png',
    )
    # 1.1.11.5	Lấy về URL sau khi ảnh đã được lưu trên S3.
    return f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{filename}"
