# # src/services/file_service.py
# import os
# import uuid
# import shutil
# from pathlib import Path
# from typing import List, Optional
# from fastapi import UploadFile, HTTPException
# from PIL import Image
# import aiofiles

# class FileService:
#     def __init__(self):
#         self.base_upload_dir = Path("uploads")
#         self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
#         self.max_file_size = 5 * 1024 * 1024  # 5MB
#         self.max_image_dimension = 2048  # Max width/height in pixels
        
#         # Create base upload directory if it doesn't exist
#         self.base_upload_dir.mkdir(exist_ok=True)

#     def _get_user_upload_dir(self, sales_user: str) -> Path:
#         """Get or create upload directory for a specific sales user"""
#         user_dir = self.base_upload_dir / "sales_users" / sales_user / "products"
#         user_dir.mkdir(parents=True, exist_ok=True)
#         return user_dir

#     def _get_product_upload_dir(self, sales_user: str, product_id: int) -> Path:
#         """Get or create upload directory for a specific product"""
#         product_dir = self._get_user_upload_dir(sales_user) / f"product_{product_id}"
#         product_dir.mkdir(parents=True, exist_ok=True)
#         return product_dir

#     def _validate_file(self, file: UploadFile) -> None:
#         """Validate uploaded file"""
#         if not file.filename:
#             raise HTTPException(status_code=400, detail="No file selected")
        
#         # Check file extension
#         file_ext = Path(file.filename).suffix.lower()
#         if file_ext not in self.allowed_extensions:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}"
#             )
        
#         # Check MIME type
#         if not file.content_type or not file.content_type.startswith('image/'):
#             raise HTTPException(status_code=400, detail="File must be an image")

#     def _generate_unique_filename(self, original_filename: str) -> str:
#         """Generate unique filename while preserving extension"""
#         file_ext = Path(original_filename).suffix.lower()
#         unique_id = str(uuid.uuid4())
#         return f"{unique_id}{file_ext}"

#     def _resize_image_if_needed(self, file_path: Path) -> None:
#         """Resize image if it's too large"""
#         try:
#             with Image.open(file_path) as img:
#                 width, height = img.size
                
#                 if width > self.max_image_dimension or height > self.max_image_dimension:
#                     # Calculate new dimensions maintaining aspect ratio
#                     ratio = min(self.max_image_dimension / width, self.max_image_dimension / height)
#                     new_width = int(width * ratio)
#                     new_height = int(height * ratio)
                    
#                     # Resize and save
#                     resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
#                     resized_img.save(file_path, optimize=True, quality=85)
                    
#         except Exception as e:
#             print(f"Warning: Could not resize image {file_path}: {e}")

#     async def save_product_image(
#         self, 
#         file: UploadFile, 
#         sales_user: str, 
#         product_id: int
#     ) -> dict:
#         """Save a product image and return file info"""
        
#         # Validate file
#         self._validate_file(file)
        
#         # Check file size
#         contents = await file.read()
#         if len(contents) > self.max_file_size:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
#             )
        
#         # Reset file pointer
#         await file.seek(0)
        
#         # Generate unique filename and get upload directory
#         unique_filename = self._generate_unique_filename(file.filename)
#         upload_dir = self._get_product_upload_dir(sales_user, product_id)
#         file_path = upload_dir / unique_filename
        
#         try:
#             # Save file
#             async with aiofiles.open(file_path, 'wb') as f:
#                 await f.write(contents)
            
#             # Resize if needed
#             self._resize_image_if_needed(file_path)
            
#             # Get final file size
#             final_size = file_path.stat().st_size
            
#             # Generate accessible URL (relative to uploads directory)
#             relative_path = file_path.relative_to(self.base_upload_dir)
#             image_url = f"/uploads/{relative_path.as_posix()}"
            
#             return {
#                 "filename": unique_filename,
#                 "original_filename": file.filename,
#                 "file_path": str(file_path),
#                 "image_url": image_url,
#                 "file_size": final_size,
#                 "mime_type": file.content_type
#             }
            
#         except Exception as e:
#             # Clean up file if saving failed
#             if file_path.exists():
#                 file_path.unlink()
#             raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

#     async def save_multiple_product_images(
#         self, 
#         files: List[UploadFile], 
#         sales_user: str, 
#         product_id: int
#     ) -> List[dict]:
#         """Save multiple product images"""
#         if not files:
#             raise HTTPException(status_code=400, detail="No files provided")
        
#         if len(files) > 10:  # Limit to 10 images per upload
#             raise HTTPException(status_code=400, detail="Maximum 10 images allowed per upload")
        
#         saved_files = []
#         failed_files = []
        
#         for file in files:
#             try:
#                 file_info = await self.save_product_image(file, sales_user, product_id)
#                 saved_files.append({**file_info, "status": "success"})
#             except HTTPException as e:
#                 failed_files.append({
#                     "filename": file.filename,
#                     "error": e.detail,
#                     "status": "failed"
#                 })
#             except Exception as e:
#                 failed_files.append({
#                     "filename": file.filename,
#                     "error": str(e),
#                     "status": "failed"
#                 })
        
#         return {
#             "saved_files": saved_files,
#             "failed_files": failed_files,
#             "total_uploaded": len(saved_files),
#             "total_failed": len(failed_files)
#         }

#     def delete_file(self, file_path: str) -> bool:
#         """Delete a file from the filesystem"""
#         try:
#             path = Path(file_path)
#             if path.exists() and path.is_file():
#                 path.unlink()
#                 return True
#             return False
#         except Exception:
#             return False

#     def get_user_storage_info(self, sales_user: str) -> dict:
#         """Get storage information for a sales user"""
#         user_dir = self._get_user_upload_dir(sales_user)
        
#         total_size = 0
#         file_count = 0
        
#         for file_path in user_dir.rglob("*"):
#             if file_path.is_file():
#                 total_size += file_path.stat().st_size
#                 file_count += 1
        
#         return {
#             "sales_user": sales_user,
#             "total_files": file_count,
#             "total_size_bytes": total_size,
#             "total_size_mb": round(total_size / (1024 * 1024), 2),
#             "storage_path": str(user_dir)
#         }



# src/services/file_service.py
import os
import uuid
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
import aiofiles
from PIL import Image
import io

class FileService:
    def __init__(self):
        self.upload_dir = "uploads"
        self.products_dir = os.path.join(self.upload_dir, "products")
        self.base_url = "http://localhost:8000"  # Your FastAPI server URL
        
        # Create directories if they don't exist
        os.makedirs(self.products_dir, exist_ok=True)
    
    async def save_multiple_product_images(
        self, 
        images: List[UploadFile], 
        sales_user: str, 
        product_id: int
    ) -> Dict[str, Any]:
        """Save multiple product images and return file information"""
        
        saved_files = []
        failed_files = []
        
        for image in images:
            try:
                file_info = await self.save_single_product_image(image, sales_user, product_id)
                saved_files.append(file_info)
            except Exception as e:
                failed_files.append({
                    "filename": image.filename,
                    "error": str(e)
                })
        
        return {
            "saved_files": saved_files,
            "failed_files": failed_files,
            "total_uploaded": len(saved_files),
            "total_failed": len(failed_files)
        }
    
    async def save_single_product_image(
        self, 
        image: UploadFile, 
        sales_user: str, 
        product_id: int
    ) -> Dict[str, Any]:
        """Save a single product image"""
        
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_extension = os.path.splitext(image.filename)[1].lower()
        unique_filename = f"product_{product_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Create product-specific directory
        product_dir = os.path.join(self.products_dir, str(product_id))
        os.makedirs(product_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(product_dir, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await image.read()
            await f.write(content)
        
        # Optimize image (optional)
        await self._optimize_image(file_path)
        
        # Generate web-accessible URL
        # This creates a URL like: http://localhost:8000/uploads/products/123/filename.jpg
        relative_path = os.path.join("products", str(product_id), unique_filename)
        image_url = f"{self.base_url}/uploads/{relative_path.replace(os.sep, '/')}"
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            "filename": unique_filename,
            "original_filename": image.filename,
            "file_path": file_path,
            "image_url": image_url,
            "file_size": file_size,
            "mime_type": image.content_type
        }
    
    async def _optimize_image(self, file_path: str, max_size: tuple = (800, 800), quality: int = 85):
        """Optimize image for web display"""
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if image is too large
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(file_path, 'JPEG', quality=quality, optimize=True)
        except Exception as e:
            print(f"Warning: Could not optimize image {file_path}: {e}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from the filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Remove empty directory if it exists
                dir_path = os.path.dirname(file_path)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> str:
        """Convert file path to web-accessible URL"""
        # Convert absolute path to relative path from uploads directory
        relative_path = os.path.relpath(file_path, self.upload_dir)
        return f"{self.base_url}/uploads/{relative_path.replace(os.sep, '/')}"






# # src/services/file_service.py
# import os
# import uuid
# from typing import List, Dict, Any
# from fastapi import UploadFile, HTTPException
# import aiofiles
# from PIL import Image
# import io

# class FileService:
#     def __init__(self):
#         self.upload_dir = "uploads"
#         self.products_dir = os.path.join(self.upload_dir, "products")
#         self.base_url = "http://localhost:8000"  # Your FastAPI server URL
        
#         # Create directories if they don't exist
#         os.makedirs(self.products_dir, exist_ok=True)
    
#     async def save_multiple_product_images(
#         self, 
#         images: List[UploadFile], 
#         sales_user: str, 
#         product_id: int
#     ) -> Dict[str, Any]:
#         """Save multiple product images and return file information"""
        
#         saved_files = []
#         failed_files = []
        
#         for image in images:
#             try:
#                 file_info = await self.save_single_product_image(image, sales_user, product_id)
#                 saved_files.append(file_info)
#             except Exception as e:
#                 failed_files.append({
#                     "filename": image.filename,
#                     "error": str(e)
#                 })
        
#         return {
#             "saved_files": saved_files,
#             "failed_files": failed_files,
#             "total_uploaded": len(saved_files),
#             "total_failed": len(failed_files)
#         }
    
#     async def save_single_product_image(
#         self, 
#         image: UploadFile, 
#         sales_user: str, 
#         product_id: int
#     ) -> Dict[str, Any]:
#         """Save a single product image"""
        
#         # Validate file type
#         if not image.content_type.startswith('image/'):
#             raise HTTPException(status_code=400, detail="File must be an image")
        
#         # Generate unique filename
#         file_extension = os.path.splitext(image.filename)[1].lower()
#         unique_filename = f"product_{product_id}_{uuid.uuid4().hex}{file_extension}"
        
#         # Create product-specific directory
#         product_dir = os.path.join(self.products_dir, str(product_id))
#         os.makedirs(product_dir, exist_ok=True)
        
#         # Full file path
#         file_path = os.path.join(product_dir, unique_filename)
        
#         # Save file
#         async with aiofiles.open(file_path, 'wb') as f:
#             content = await image.read()
#             await f.write(content)
        
#         # Optimize image (optional)
#         await self._optimize_image(file_path)
        
#         # Generate web-accessible URL
#         # This creates a URL like: http://localhost:8000/uploads/products/123/filename.jpg
#         relative_path = os.path.join("products", str(product_id), unique_filename)
#         image_url = f"{self.base_url}/uploads/{relative_path.replace(os.sep, '/')}"
        
#         # Get file size
#         file_size = os.path.getsize(file_path)
        
#         return {
#             "filename": unique_filename,
#             "original_filename": image.filename,
#             "file_path": file_path,
#             "image_url": image_url,
#             "file_size": file_size,
#             "mime_type": image.content_type
#         }
    
#     async def _optimize_image(self, file_path: str, max_size: tuple = (800, 800), quality: int = 85):
#         """Optimize image for web display"""
#         try:
#             with Image.open(file_path) as img:
#                 # Convert RGBA to RGB if necessary
#                 if img.mode in ('RGBA', 'LA', 'P'):
#                     background = Image.new('RGB', img.size, (255, 255, 255))
#                     if img.mode == 'P':
#                         img = img.convert('RGBA')
#                     background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
#                     img = background
                
#                 # Resize if image is too large
#                 img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
#                 # Save optimized image
#                 img.save(file_path, 'JPEG', quality=quality, optimize=True)
#         except Exception as e:
#             print(f"Warning: Could not optimize image {file_path}: {e}")
    
#     def delete_file(self, file_path: str) -> bool:
#         """Delete a file from the filesystem"""
#         try:
#             if os.path.exists(file_path):
#                 os.remove(file_path)
                
#                 # Remove empty directory if it exists
#                 dir_path = os.path.dirname(file_path)
#                 if os.path.exists(dir_path) and not os.listdir(dir_path):
#                     os.rmdir(dir_path)
                
#                 return True
#             return False
#         except Exception as e:
#             print(f"Error deleting file {file_path}: {e}")
#             return False
    
#     def get_file_url(self, file_path: str) -> str:
#         """Convert file path to web-accessible URL"""
#         # Convert absolute path to relative path from uploads directory
#         relative_path = os.path.relpath(file_path, self.upload_dir)
#         return f"{self.base_url}/uploads/{relative_path.replace(os.sep, '/')}"