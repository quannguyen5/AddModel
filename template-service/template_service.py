from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import time
from pathlib import Path

# Import existing DAOs
from dao.fraud_template_dao import FraudTemplateDAO
from dao.fraud_label_dao import FraudLabelDAO
from dao.bounding_box_dao import BoundingBoxDAO

app = FastAPI(title="Template Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    print(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"Response: {response.status_code} in {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        print(f"Error: {str(e)} in {process_time:.3f}s")
        raise

# Initialize DAOs
fraud_template_dao = FraudTemplateDAO()
fraud_label_dao = FraudLabelDAO()
bounding_box_dao = BoundingBoxDAO()

# Static files directory
STATIC_DIR = "static"
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

# Tạo directories nếu chưa có
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Mount static files directory for direct file access
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Pydantic models


class TemplateResponse(BaseModel):
    idTemplate: int
    description: Optional[str]
    imageUrl: str
    timeUpdate: str
    labels: List[dict] = []
    boundingBox: List[dict] = []


class TemplateCreateRequest(BaseModel):
    description: Optional[str] = ""
    imageUrl: str
    labels: List[dict] = []
    boundingBox: List[dict] = []


@app.get("/")
async def root():
    return {"message": "Template Service is running"}


@app.get("/templates", response_model=List[TemplateResponse])
async def get_all_templates():
    """Lấy danh sách tất cả fraud templates với image URLs đã được chuẩn hóa"""
    try:
        templates = fraud_template_dao.get_all()
        template_list = []

        for template in templates:
            template_dict = template.to_dict()

            # Chuẩn hóa image URL để trỏ về template service
            original_url = template_dict["imageUrl"]
            normalized_url = normalize_image_url(original_url)

            template_response = TemplateResponse(
                idTemplate=template_dict["idTemplate"],
                description=template_dict.get("description", ""),
                imageUrl=normalized_url,
                timeUpdate=template_dict["timeUpdate"],
                labels=template_dict.get("labels", []),
                boundingBox=template_dict.get("boundingBox", [])
            )
            template_list.append(template_response)

        return template_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/{template_id}")
async def get_template(template_id: int):
    """Lấy thông tin chi tiết một template"""
    try:
        template = fraud_template_dao.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        template_dict = template.to_dict()
        # Chuẩn hóa image URL
        template_dict["imageUrl"] = normalize_image_url(
            template_dict["imageUrl"])

        return template_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve image files từ static directory"""
    try:
        print(f"Image request for: {filename}")

        # URL decode filename to handle spaces and special characters
        import urllib.parse
        decoded_filename = urllib.parse.unquote(filename)
        print(f"Decoded filename: {decoded_filename}")

        # Validate filename to prevent directory traversal (allow spaces)
        if ".." in decoded_filename or "/" in decoded_filename or "\\" in decoded_filename:
            raise HTTPException(
                status_code=400, detail="Invalid filename - directory traversal not allowed")

        # Tìm file trong static directory
        file_path = find_image_file(decoded_filename)

        if not file_path or not os.path.exists(file_path):
            print(f"Image not found: {decoded_filename}, tried: {file_path}")
            # Trả về placeholder image nếu không tìm thấy
            return create_placeholder_response()

        print(f"Serving image: {file_path}")
        return FileResponse(
            file_path,
            media_type=get_media_type(file_path),
            headers={
                "Cache-Control": "max-age=3600",
                "Accept-Ranges": "bytes"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving image {filename}: {str(e)}")
        return create_placeholder_response()


@app.get("/images/template/{template_id}")
async def get_template_image(template_id: int):
    """Lấy ảnh của template theo ID"""
    try:
        template = fraud_template_dao.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Lấy đường dẫn ảnh từ database
        image_url = template.imageUrl

        # Tìm file thực tế
        file_path = resolve_image_path(image_url)

        if not file_path or not os.path.exists(file_path):
            return create_placeholder_response()

        return FileResponse(
            file_path,
            media_type=get_media_type(file_path),
            headers={"Cache-Control": "max-age=3600"}
        )

    except Exception as e:
        print(f"Error serving template image {template_id}: {str(e)}")
        return create_placeholder_response()


def normalize_image_url(original_url: str) -> str:
    """Chuẩn hóa image URL để trỏ về template service"""
    if not original_url:
        return "http://localhost:8003/images/placeholder.png"

    # Nếu là URL đầy đủ, giữ nguyên
    if original_url.startswith("http"):
        return original_url

    # Trích xuất filename từ path
    filename = os.path.basename(original_url)

    # Trả về URL của template service
    return f"http://localhost:8003/images/{filename}"


def find_image_file(filename: str) -> Optional[str]:
    """Tìm file ảnh trong các thư mục có thể"""
    # Các thư mục có thể, bao gồm cả images subdirectory
    base_dirs = [
        os.path.join(STATIC_DIR, "images"),      # static/images/
        os.path.join("static", "images"),        # static/images/
        os.path.join("..", "static", "images"),  # ../static/images/
        os.path.join(".", "static", "images"),   # ./static/images/
        STATIC_DIR,                              # static/
        "static",                                # static/
        os.path.join("..", "static"),            # ../static/
        os.path.join(".", "static"),             # ./static/
        "."                                      # current directory
    ]

    # Các extensions có thể nếu không có extension
    extensions = ["", ".jpg", ".jpeg", ".png", ".gif", ".bmp"]

    print(f"Looking for image file: {filename}")

    for base_dir in base_dirs:
        for ext in extensions:
            # Thử với filename gốc
            test_filename = filename + ext if not filename.endswith(
                ('.jpg', '.jpeg', '.png', '.gif', '.bmp')) and ext else filename
            path = os.path.join(base_dir, test_filename)
            print(f"  Checking: {path}")

            if os.path.exists(path):
                print(f"  Found: {path}")
                return path

    print(f"  Not found in any location")
    return None


def resolve_image_path(image_url: str) -> Optional[str]:
    """Resolve đường dẫn ảnh từ URL trong database"""
    if not image_url:
        return None

    # Nếu là URL HTTP, không thể serve local
    if image_url.startswith("http"):
        return None

    # Các định dạng path có thể có trong database
    if image_url.startswith("/static/"):
        relative_path = image_url[8:]  # Remove "/static/"
    elif image_url.startswith("static/"):
        relative_path = image_url[7:]  # Remove "static/"
    elif image_url.startswith("/"):
        relative_path = image_url[1:]  # Remove leading "/"
    else:
        relative_path = image_url

    return find_image_file(relative_path)


def get_media_type(file_path: str) -> str:
    """Xác định media type từ file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')


def create_placeholder_response():
    """Tạo response cho placeholder image - simple approach"""
    try:
        # Thử tạo ảnh placeholder với PIL
        from PIL import Image, ImageDraw
        import io

        # Tạo ảnh placeholder 200x200
        img = Image.new('RGB', (200, 200), color='lightgray')
        draw = ImageDraw.Draw(img)

        # Vẽ border
        draw.rectangle([0, 0, 199, 199], outline='gray', width=2)

        # Vẽ text
        draw.text((70, 90), "NO IMAGE", fill='darkgray')

        # Convert sang bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(img_bytes.getvalue()),
            media_type="image/png",
            headers={"Cache-Control": "max-age=3600"}
        )

    except ImportError:
        # Nếu không có PIL, trả về simple text response
        return JSONResponse(
            status_code=404,
            content={"error": "Image not found",
                     "message": "Please check if the image file exists"}
        )
    except Exception as e:
        print(f"Error creating placeholder: {str(e)}")
        return JSONResponse(
            status_code=404,
            content={"error": "Image not found"}
        )


@app.post("/templates")
async def create_template(template_request: TemplateCreateRequest):
    """Tạo template mới"""
    try:
        from models.fraud_template import FraudTemplate
        from models.fraud_label import FraudLabel
        from models.bounding_box import BoundingBox
        from datetime import datetime

        # Tạo template object
        template = FraudTemplate(
            description=template_request.description,
            imageUrl=template_request.imageUrl,
            timeUpdate=datetime.now()
        )

        # Tạo labels nếu có
        if template_request.labels:
            labels = []
            for label_data in template_request.labels:
                label = FraudLabel(
                    description=label_data.get('description'),
                    typeLabel=label_data.get('typeLabel')
                )
                labels.append(label)
            template.labels = labels

        # Tạo bounding boxes nếu có
        if template_request.boundingBox:
            boxes = []
            for box_data in template_request.boundingBox:
                box = BoundingBox(
                    xCenter=box_data.get('xCenter'),
                    yCenter=box_data.get('yCenter'),
                    width=box_data.get('width'),
                    height=box_data.get('height'),
                    xPixel=box_data.get('xPixel'),
                    yPixel=box_data.get('yPixel'),
                    widthPixel=box_data.get('widthPixel'),
                    heightPixel=box_data.get('heightPixel'),
                    fraudLabelId=box_data.get('fraudLabelId')
                )
                boxes.append(box)
            template.boundingBox = boxes

        template_id = fraud_template_dao.create(template)

        return {"success": True, "template_id": template_id, "message": "Template created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """Xóa template"""
    try:
        success = fraud_template_dao.delete(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"success": True, "message": "Template deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/files")
async def list_static_files():
    """Debug endpoint - list tất cả files trong static directory"""
    try:
        files = []
        static_dirs = [
            STATIC_DIR,
            "static",
            os.path.join("..", "static"),
            os.path.join(STATIC_DIR, "images"),
            os.path.join("static", "images"),
            os.path.join("..", "static", "images")
        ]

        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                try:
                    for file in os.listdir(static_dir):
                        file_path = os.path.join(static_dir, file)
                        if os.path.isfile(file_path):
                            files.append({
                                "directory": static_dir,
                                "filename": file,
                                "full_path": file_path,
                                "size": os.path.getsize(file_path)
                            })
                except PermissionError:
                    continue

        return {"static_files": files, "total": len(files)}
    except Exception as e:
        return {"error": str(e), "static_files": []}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
