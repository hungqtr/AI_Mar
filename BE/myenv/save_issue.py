import os
import json
import base64
import uuid
import bcrypt
import logging
import requests
import boto3
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Load biến môi trường
load_dotenv()

# Khởi tạo logger
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.debug("Logger initialized successfully")

# Hàm kết nối PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "47.84.52.44"),
            port=int(os.getenv("POSTGRES_PORT", 5433)),
            database=os.getenv("POSTGRES_DB", "aimar"),
            user=os.getenv("POSTGRES_USER", "myuser"),
            password=os.getenv("POSTGRES_PASSWORD", "Password1!")
        )
        return conn
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

class SubIssueCreate(BaseModel):
    prompt: str
    response: Optional[str] = None
    imageURL: Optional[str] = None

class IssueCreate(BaseModel):
    title: str
    user_id: UUID
    sub_issues: List[SubIssueCreate] = []

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

# API tạo issue và sub_issue
@app.post("/issue/")
async def create_issue(issue: IssueCreate):
    issue_uuid = uuid4()
    created_at = datetime.now(timezone.utc)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Insert issue
                cur.execute(
                    "INSERT INTO issue (id, title, user_id, created_at) VALUES (%s, %s, %s, %s)",
                    (str(issue_uuid), issue.title, str(issue.user_id), created_at)
                )

                # Insert sub_issues, nếu có
                if issue.sub_issues:
                    sub_issue_values = []
                    for sub in issue.sub_issues:
                        sub_uuid = uuid4()
                        sub_issue_values.append((
                            str(sub_uuid),
                            str(issue.user_id),
                            str(issue_uuid),
                            sub.prompt,
                            sub.response,
                            sub.imageURL,
                            created_at
                        ))

                    execute_values(
                        cur,
                        """
                        INSERT INTO sub_issue (id, user_id, issue_id, prompt, response, imageURL, created_at)
                        VALUES %s
                        """,
                        sub_issue_values
                    )
                conn.commit()

        return {"message": "Lưu thành công!", "issue_id": str(issue_uuid)}

    except Exception as e:
        logger.error(f"Lỗi khi insert issue hoặc sub_issue: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

# Các hàm sinh slogan, content, ảnh và các API liên quan giữ nguyên, vì chúng không liên quan tới DB.

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
        return f"❌ Error {response.status_code}: {response.text}"


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
        return f"❌ Error {response.status_code}: {response.text}"


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

# API test đơn giản
@app.post("/test/")
async def test_api():
    return {"data": "Hello, I'm AImar "}

# API tạo slogan
@app.post("/slogan/")
async def generate_slogan_api(request: Request):
    prompt = request.prompt
    slogan = generate_slogan(prompt)
    if "Error" in slogan:
        raise HTTPException(status_code=400, detail=slogan)
    return {"data": slogan}

# API tạo content
@app.post("/content/")
async def generate_content_api(request: Request):
    prompt = request.prompt
    logger.debug(f"Prompt for content: {prompt}")
    content = generate_content(prompt)
    if "Error" in content:
        raise HTTPException(status_code=400, detail=content)
    return {"data": content}

# API tạo ảnh
@app.post("/image/")
async def generate_image_api(request: Request):
    prompt = request.prompt
    logger.debug(f"Prompt: {prompt}")
    response = generate_image(prompt)
    if "Error" in response:
        raise HTTPException(status_code=400, detail=response)
    return {"data": response}