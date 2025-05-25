import os
import json
import base64
import uuid
import bcrypt
import logging
import requests
import boto3
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Load biến môi trường
load_dotenv()

# Khởi tạo logger
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.debug("Logger initialized successfully")

# 4.1.4 Kết nối DB thành công
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

    #4.3.1 Nếu hệ thống không kết nối được đến cơ sở dữ liệu ở bước 4.1.2, hệ thống hiển thị thông báo lỗi “Không kết nối được tới DB”.
    except Exception as e:
        logger.error(f"Không kết nối được tới DB: {e}")
        raise

# Khởi tạo FastAPI và cấu hình CORS
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Hàm băm mật khẩu
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

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
async def login_user(user: UserLogin):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE username = %s", (user.username,))
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=401, detail="Tên đăng nhập không tồn tại.")
                hashed_password = result[0]

                if not check_password(user.password, hashed_password):
                    raise HTTPException(status_code=401, detail="Mật khẩu không chính xác.")
        return {"message": "Đăng nhập thành công!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi đăng nhập: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình đăng nhập.")

# API test đơn giản
@app.post("/test/")
async def test_api():
    return {"data": "Hello, I'm AImar "}

# API tạo slogan
@app.post("/slogan/")
async def generate_slogan_api(request: Request):
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id
    conn = get_db_connection() 
    issue : Issues


# 4.2.1 Nếu người dùng chưa đăng nhập và chưa có issue (user_id == null và issue_id == null)
    if (not user_id and not issue_id):
      # 4.2.1.1 Gọi hàm xử lý tạo slogan
      slogan = generate_slogan(prompt)

      # 4.4.1 Nếu kết quả trả về ở bước 4.2.1.1 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
      if "Error" in slogan:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        
      # 4.2.1.2 Trả về kết quả nội dung slogan với status 200 OK và issue_id trả về là null.
      response = Response(
        code=200,
        message='success',
        data={
            "content": slogan,
            "issue_id": None
            }
        )
      return response


    # 4.2.2 Nếu người dùng đã đăng nhập nhưng chưa có issue_id
    if( user_id and not issue_id):
      
      # 4.2.2.1 FastAPI tạo bản ghi mới trong bảng issues với user_id và tiêu đề mặc định (INSERT INTO issues(user_id, title), nhận được issue_id). (prompt tương ứng với title trong DB)
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
    
    # 4.2.2.2 FastAPI lưu prompt của người dùng vào bảng sub_issues với type=’text’, sender=’user’ và liên kết với issue_id (INSERT INTO sub_issues(prompt, type=’text’, sender=’user’).
    create_sub_issue(conn, issue_id, prompt, "text", "user")

    logger.debug(f"Prompt for content: {prompt}")

    # 4.2.2.3 FastAPI gọi hàm xử lý tạo slogan
    slogan = generate_slogan(prompt)

    # 4.4.1 Nếu kết quả trả về ở bước 4.2.2.3 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
    if "Error"  in slogan:
      response = Response(
      code=400,
      message='failed',
      data={}
    ) 
      return response
  
    # 4.2.2.4 FastAPI lưu phản hồi từ hàm tạo nội dung vào bảng sub_issues với type phù hợp (text), sender=’bot’.
    create_sub_issue(conn, issue_id, slogan, "text", "bot")
    
    # 4.2.2.5 FastAPI trả về kết quả nội dung slogan với status 200 OK và issue_id.
    response = Response(
        code=200,
        message='success',
        data={
            "content": slogan,
            "issue_id": issue_id
        }
    )
    return response

# API tạo content
@app.post("/content/")
async def generate_content_api(request: Request):
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id

    conn = get_db_connection() 
    issue : Issues

    # 4.2.1 Nếu người dùng chưa đăng nhập và chưa có issue (user_id == null và issue_id == null)
    if (not user_id and not issue_id):

      # 4.2.1.1 Gọi hàm xử lý tạo content (nội dung)
      content = generate_content(prompt)

      # 4.4.1 Nếu kết quả trả về ở bước 4.2.1.1 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
      if "Error" in content:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        
      # 4.2.1.2 Trả về kết quả nội dung content với status 200 OK và issue_id trả về là null.
      response = Response(
        code=200,
        message='success',
        data={
            "content": content,
            "issue_id": None
            }
        )
      return response

    # 4.2.2 Nếu người dùng đã đăng nhập nhưng chưa có issue_id
    if( user_id and not issue_id):
      
      # 4.2.2.1 FastAPI tạo bản ghi mới trong bảng issues với user_id và tiêu đề mặc định (INSERT INTO issues(user_id, title), nhận được issue_id). (prompt tương ứng với title trong DB)
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
      
    logger.debug(f"Prompt for content: {prompt}")

    # 4.2.2.2 FastAPI lưu prompt của người dùng vào bảng sub_issues với type=’text’, sender=’user’ và liên kết với issue_id (INSERT INTO sub_issues(prompt, type=’text’, sender=’user’).
    create_sub_issue(conn, issue_id, prompt, "text", "user")
    
    # 4.2.2.3 FastAPI gọi hàm xử lý tạo content
    content = generate_content(prompt)

    # 4.4.1 Nếu kết quả trả về ở bước 4.2.2.3 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
    if "Error"  in content:
        response = Response(
        code=400,
        message='failed',
        data={}
    ) 
        return response
    
    # 4.2.2.4 FastAPI lưu phản hồi từ hàm tạo nội dung vào bảng sub_issues với type phù hợp (text), sender=’bot’.
    create_sub_issue(conn, issue_id, content, "text", "bot")

    # 4.2.2.5 FastAPI trả về kết quả nội dung content với status 200 OK và issue_id.
    response = Response(
        code=200,
        message='success',
        data={
            "content": content,
            "issue_id": issue_id
        }
    )
    return response

# API tạo ảnh
@app.post("/image/")
async def generate_image_api( request: Request):
  
    prompt =  request.prompt
    user_id = request.user_id
    issue_id = request.issue_id
    conn = get_db_connection() 
    issue : Issues


    # 4.2.1 Nếu người dùng chưa đăng nhập và chưa có issue (user_id == null và issue_id == null)
    if (not user_id and not issue_id):

      # 4.2.1.1 Gọi hàm xử lý tạo image (hình ảnh)
      url = generate_image(prompt)

      # 4.4.1 Nếu kết quả trả về ở bước 4.2.1.1 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
      if "Error" in url:
        response = Response(
        code=400,
        message='failed',
        data={}
        ) 
        return response
        
      # 4.2.1.2 Trả về kết quả nội dung image với status 200 OK và issue_id trả về là null.
      response = Response(
        code=200,
        message='success',
        data={
            "content": url,
            "issue_id": None
            }
        )
      return response

    # 4.2.2 Nếu người dùng đã đăng nhập nhưng chưa có issue_id
    if( user_id and not issue_id):
      
      # 4.2.2.1 FastAPI tạo bản ghi mới trong bảng issues với user_id và tiêu đề mặc định (INSERT INTO issues(user_id, title), nhận được issue_id). (prompt tương ứng với title trong DB)
      issue =  create_issue(conn, user_id, prompt)
      issue_id = issue.id
    
    # 4.2.2.2 FastAPI lưu prompt của người dùng vào bảng sub_issues với type=’text’, sender=’user’ và liên kết với issue_id (INSERT INTO sub_issues(prompt, type=’text’, sender=’user’).
    create_sub_issue(conn, issue_id, prompt, "text", "user")

    logger.debug(f"Prompt: {prompt}")

    # 4.2.2.3 FastAPI gọi hàm xử lý tạo image
    url = generate_image(prompt)

    # 4.4.1 Nếu kết quả trả về ở bước 4.2.2.3 chứa chuỗi “Error” hoặc lỗi tương tự thì trả về 400 Bad Request và hiển thị thông báo lỗi lên trang index.html
    if "Error" in url:
            response = Response(
            code=400,
            message='failed',
            data={}
        ) 
            return response
        
    # 4.2.2.4 FastAPI lưu phản hồi từ hàm tạo nội dung vào bảng sub_issues với type phù hợp (imageURL), sender=’bot’.
    create_sub_issue(conn, issue_id, url, "text", "bot")

    # 4.2.2.5 FastAPI trả về kết quả nội dung content với status 200 OK và issue_id.
    response = Response(
        code=200,
        message='success',
        data={
            "content": url,
            "issue_id": issue_id
            }
        )
    return response

#Hàm
def generate_slogan(prompt: str) -> str:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn là một chuyên gia hàng đầu trong lĩnh vực xây dựng thương hiệu và marketing. Khách hàng của bạn là những người kinh doanh đa dạng sản phẩm. Nhiệm vụ của bạn là tạo ra những slogan ngắn gọn, sắc sảo, dễ nhớ và truyền cảm hứng, giúp sản phẩm ghi dấu ấn mạnh mẽ trong tâm trí khách hàng mục tiêu."
                },
                {"role": "user", "content": prompt}
            ]
        })
    )
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"


# Hàm tạo content từ prompt
def generate_content(prompt: str) -> str:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn là một chuyên gia hàng đầu trong lĩnh vực xây dựng thương hiệu và marketing. Khách hàng của bạn là những người kinh doanh đa dạng ngành hàng. Nhiệm vụ của bạn là tạo ra những nội dung hấp dẫn, thuyết phục và phù hợp với mục tiêu tiếp thị của họ."
                },
                {"role": "user", "content": prompt}
            ]
        })
    )
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"


# Hàm upload ảnh base64 lên S3
def upload_base64_to_s3(base64_data: str, bucket_name: str, region_name: str = 'ap-southeast-1') -> str:
    image_data = base64.b64decode(base64_data)
    filename = f"CNPM/image_{uuid.uuid4().hex}.png"

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', region_name)
    )

    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=image_data,
        ContentType='image/png',
    )
    return f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{filename}"


# Hàm tạo ảnh từ prompt
def generate_image(prompt: str) -> str:
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
        data = response.json()
        base64_image = data["data"][0].get("b64_json")

        if base64_image:
            return upload_base64_to_s3(base64_image, "image-bluetech")
        elif response.status_code == 307:
            return f"❌ Redirect: {response.headers.get('Location')}"
        else:
            return "❌ Error: Không tìm thấy hình ảnh trong response."
    else:
        return f"❌ Error {response.status_code}: {response.text}"


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
