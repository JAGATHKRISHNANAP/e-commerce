# src/models/product_image.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base

class ProductImage(Base):
    __tablename__ = "product_images"

    image_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    image_filename = Column(String(255), nullable=False)  # Stored filename
    image_path = Column(String(500), nullable=False)      # Full file path
    image_url = Column(String(500), nullable=False)       # Accessible URL
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    uploaded_by = Column(String(100), nullable=False)     # Sales user identifier
    file_size = Column(Integer, nullable=True)            # File size in bytes
    mime_type = Column(String(100), nullable=True)        # image/jpeg, image/png, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship back to product
    product = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage(id={self.image_id}, product_id={self.product_id}, filename='{self.image_filename}', primary={self.is_primary})>"