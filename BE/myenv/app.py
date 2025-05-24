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
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

from dataclasses import dataclass


# Khởi tạo FastAPI
app = FastAPI()
load_dotenv()


logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)  # Set mức độ log, có thể là INFO, DEBUG, ERROR, ...

# Handler để ghi log vào terminal hoặc file
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.debug("Logger initialized successfully")


app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các domain
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, v.v.)
    allow_headers=["*"],  # Cho phép tất cả các header
)




# Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Request(BaseModel):
    prompt: str
    user_id: Optional[int]
    issue_id: Optional[int]

class Response(BaseModel):
    code: int
    message: str
    data: object 

class SubIssueCreate(BaseModel):
    prompt: str
    response: Optional[str] = None
    imageURL: Optional[str] = None



class User(BaseModel):
    id: int
    username: str
    email: str
    password: str
    
class Issues(BaseModel):
    id: int
    title: str
    user_id: int

class SubIssue(BaseModel):
    id: int
    issue_id: int
    type: str
    content: str
    owner: str
 


# API

@app.get("/test/")
async def generate_slogan_api():
    get_db_connection()
    return {"data": "Hello, I'm AImar "}

@app.post("/content/")
async def generate_content_api(request: Request):
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id

    conn = get_db_connection() 
    issue : Issues
 # Người dùng chưa đăng nhập => không cần lưu
    if (not user_id and not issue_id):

      content = generate_content(prompt)

      if "Error" in content:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        
      response = Response(
        code=200,
        message='success',
        data={
            "content": content,
            "issue_id": None
            }
        )
      return response



    # Nếu chỉ có user id thì đang chat trên đoạn chat mới
    if( user_id and not issue_id):
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
      
    logger.debug(f"Prompt for content: {prompt}")

    create_sub_issue(conn, issue_id, prompt, "text", "user")
    
    content = generate_content(prompt)

    if "Error"  in content:
        response = Response(
        code=400,
        message='failed',
        data={}
    ) 
        return response
    

    create_sub_issue(conn, issue_id, content, "text", "bot")

    response = Response(
        code=200,
        message='success',
        data={
            "content": content,
            "issue_id": issue_id
        }
    )
    return response


@app.post("/slogan/")
async def generate_slogan_api(request: Request):
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id
    conn = get_db_connection() 
    issue : Issues


# Người dùng chưa đăng nhập => không cần lưu
    if (not user_id and not issue_id):

      slogan = generate_slogan(prompt)

      if "Error" in slogan:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        
      response = Response(
        code=200,
        message='success',
        data={
            "content": slogan,
            "issue_id": None
            }
        )
      return response



    if( user_id and not issue_id):
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
    
    create_sub_issue(conn, issue_id, prompt, "text", "user")

    logger.debug(f"Prompt for content: {prompt}")

    slogan = generate_slogan(prompt)
    if "Error"  in slogan:
      response = Response(
      code=400,
      message='failed',
      data={}
    ) 
      return response
  
    create_sub_issue(conn, issue_id, slogan, "text", "bot")
    response = Response(
        code=200,
        message='success',
        data={
            "content": slogan,
            "issue_id": issue_id
        }
    )
    return response

    
    


@app.post("/image/")
async def generate_image_api( request: Request):
  
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id
    conn = get_db_connection() 
    issue : Issues


# Người dùng chưa đăng nhập => không cần lưu
    if (not user_id and not issue_id):

      url = generate_image(prompt)

      if "Error" in url:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        

      response = Response(
        code=200,
        message='success',
        data={
            "content": url,
            "issue_id": None
            }
        )
      return response

    
    if( user_id and not issue_id):
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
    
    create_sub_issue(conn, issue_id, prompt, "text", "user")

    
    logger.debug(f"Prompt: {prompt}")
    url = generate_image(prompt)



    # if "Error" in response:
    #     raise HTTPException(status_code=400, detail=response)
    # return {"data": response}


    if "Error" in url:
            response = Response(
            code=400,
            message='failed',
            data={}
        ) 
            return response
        

    create_sub_issue(conn, issue_id, url, "text", "bot")

    response = Response(
        code=200,
        message='success',
        data={
            "content": url,
            "issue_id": issue_id
            }
        )
    return response



# API đăng ký user
@app.post("/register/")
async def register_user(user: UserRegister):
    try:
        hashed_password = hash_password(user.password)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Kiểm tra username hoặc email đã tồn tại
                cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (user.username, user.email))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Tên người dùng hoặc email đã tồn tại.")

                # Thêm user mới vào DB
                cur.execute(
                    """
                    INSERT INTO users (username, email, password, created_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (user.username, user.email, hashed_password)
                )
                conn.commit()
        return {"message": "Đăng ký thành công!"}
    except psycopg2.Error as db_error:
        logger.error(f"PostgreSQL error: {db_error}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống cơ sở dữ liệu.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi trong quá trình đăng ký: {e}")
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình đăng ký.")


# API đăng nhập user
@app.post("/login/")
async def login_user(request: UserLogin):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, email, password FROM users WHERE username = %s ", (request.username, ))
                data =  cur.fetchone()
                if not data:
                    raise HTTPException(status_code=401, detail="Tên đặng nhập hoặc mật khẩu không đúng.")
                
                user= User(id=data[0],username =data[1], email=data[2], password=data[3])

                if check_password(request.password, user.password ):
                  return {
                      "message": "Đăng nhập thành công!",
                      "data": {
                          "id": user.id,
                          "username": user.username,
                          "email": user.email
                      }
                        }
 
                else:
                    raise HTTPException(status_code=401, detail="Tên đặng nhập hoặc mật khẩu không đúng.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi đăng nhập: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình đăng nhập.")





#  Hàm 
def generate_slogan(prompt):
  key=os.getenv('OR_KEY')
  response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer "+key,
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
  else:
   return f"❌ Error {response.status_code}: {response.text}"


def generate_content(prompt):
  key=os.getenv('OR_KEY')
  response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer "+key ,
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
    logger.error(result)
    return result["choices"][0]["message"]["content"]
  else:
    return f"❌ Error {response.status_code}: {response.text}"


 

def generate_image(prompt):
    key=os.getenv('OI_KEY')
    url = "https://ir-api.myqa.cc/v1/openai/images/generations"
    headers = {
        "Authorization": "Bearer "+key ,
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


# Hàm kết nối PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT")),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        print("Kết nối thành công!")
        return conn

    except Exception as e:
        logger.error(f"Không kết nối được tới DB: {e}")
        raise
     


# Hàm băm mật khẩu
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_issues_by_user(conn, user_id: int) -> list[Issues]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, user_id
            FROM issues
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        results = cur.fetchall()
        return [Issues(id=row[0], title=row[1], user_id=row[2]) for row in results]


def create_issue(conn, user_id: int, title: str = "New Conversation") -> Issues:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO issues (title, user_id)
            VALUES (%s, %s )
            RETURNING id, title, user_id
        """, (title, user_id))
        result = cur.fetchone()
        conn.commit()
        return Issues(id=result[0], title=result[1], user_id=result[2])
    


def create_sub_issue(conn, issue_id: int, content: str, type_: str, owner: str) -> SubIssue:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO sub_issues (content, issue_id, type, owner)
            VALUES (%s, %s, %s, %s)
            RETURNING id, content, issue_id, type, owner
        """, (content, issue_id, type_, owner))
        result = cur.fetchone()
        conn.commit()
        return SubIssue(
            id=result[0],
            content=result[1],
            issue_id=result[2],
            type=result[3],
            owner=result[4]
        )

