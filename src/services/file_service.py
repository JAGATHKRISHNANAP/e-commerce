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
        self.base_url = "http://65.1.248.179:8000"  # Your FastAPI server URL
        
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
        # This creates a URL like: http://65.1.248.179:8000/uploads/products/123/filename.jpg
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
#         self.base_url = "http://65.1.248.179:8000"  # Your FastAPI server URL
        
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
#         # This creates a URL like: http://65.1.248.179:8000/uploads/products/123/filename.jpg
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