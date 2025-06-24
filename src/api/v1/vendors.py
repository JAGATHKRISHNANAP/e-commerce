# src/api/v1/vendors.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime
import secrets
import string
import os
import shutil
from pathlib import Path

from config.database import get_db
from src.models.vendor import Vendor, BusinessType, VendorStatus
from src.schemas.vendor import (
    VendorRegistrationRequest, 
    VendorRegistrationResponse,
    VendorResponse, 
    VendorDetailResponse,
    VendorListResponse,
    VendorStatusUpdate,
    VendorProfileUpdate,
    VendorSearchFilters
)
from src.api.v1.auth import get_current_user  # Assuming you have admin auth
from src.models.customer import Customer

router = APIRouter()

# Configuration for file uploads
UPLOAD_DIR = Path("uploads/vendor_photos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def generate_vendor_code() -> str:
    """Generate unique vendor code"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(secrets.choice(string.digits) for _ in range(3))
    return f"VND{timestamp}{random_part}"


def save_vendor_photo(file: UploadFile) -> str:
    """Save vendor photo and return file path"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"{secrets.token_hex(16)}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return str(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")


@router.post("/vendors/register", response_model=VendorRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_vendor(
    # Form data fields
    owner_name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    aadhar_number: str = Form(...),
    business_name: str = Form(...),
    business_type: str = Form(...),
    business_description: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    pan_number: Optional[str] = Form(None),
    address_line_1: str = Form(...),
    address_line_2: Optional[str] = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form("India"),
    bank_name: str = Form(...),
    account_number: str = Form(...),
    ifsc_code: str = Form(...),
    account_holder_name: str = Form(...),
    years_in_business: Optional[int] = Form(None),
    annual_turnover: Optional[float] = Form(None),
    number_of_employees: Optional[int] = Form(None),
    website_url: Optional[str] = Form(None),
    business_license_number: Optional[str] = Form(None),
    tax_registration_number: Optional[str] = Form(None),
    terms_accepted: bool = Form(...),
    
    # File upload
    vendor_photo: Optional[UploadFile] = File(None),
    
    db: Session = Depends(get_db)
):
    """Register a new vendor"""
    
    # Validate terms acceptance
    if not terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted"
        )
    
    # Check if vendor already exists
    existing_vendor = db.query(Vendor).filter(
        or_(
            Vendor.email == email.lower(),
            Vendor.phone_number == phone_number,
            Vendor.aadhar_number == aadhar_number
        )
    ).first()
    
    if existing_vendor:
        if existing_vendor.email == email.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A vendor with this email already exists"
            )
        elif existing_vendor.phone_number == phone_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A vendor with this phone number already exists"
            )
        elif existing_vendor.aadhar_number == aadhar_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A vendor with this Aadhar number already exists"
            )
    
    # Handle photo upload
    photo_path = None
    if vendor_photo and vendor_photo.filename:
        # Check file size
        file_content = await vendor_photo.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 5MB limit"
            )
        
        # Reset file pointer and save
        await vendor_photo.seek(0)
        photo_path = save_vendor_photo(vendor_photo)
    
    # Generate vendor code
    vendor_code = generate_vendor_code()
    
    # Ensure vendor code is unique
    while db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first():
        vendor_code = generate_vendor_code()
    
    # Create vendor record
    vendor = Vendor(
        vendor_code=vendor_code,
        owner_name=owner_name,
        vendor_photo=photo_path,
        phone_number=phone_number,
        email=email.lower(),
        aadhar_number=aadhar_number,
        business_name=business_name,
        business_type=BusinessType(business_type),
        business_description=business_description,
        gst_number=gst_number.upper() if gst_number else None,
        pan_number=pan_number.upper() if pan_number else None,
        address_line_1=address_line_1,
        address_line_2=address_line_2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
        bank_name=bank_name,
        account_number=account_number,
        ifsc_code=ifsc_code.upper(),
        account_holder_name=account_holder_name,
        years_in_business=years_in_business,
        annual_turnover=annual_turnover,
        number_of_employees=number_of_employees,
        website_url=website_url,
        business_license_number=business_license_number,
        tax_registration_number=tax_registration_number,
        terms_accepted=terms_accepted,
        terms_accepted_date=datetime.utcnow(),
        vendor_status=VendorStatus.PENDING
    )
    
    try:
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        
        return VendorRegistrationResponse(
            vendor_id=vendor.vendor_id,
            vendor_code=vendor.vendor_code,
            message="Registration submitted successfully! We will review your application and get back to you within 2-3 business days.",
            status=vendor.vendor_status.value
        )
        
    except Exception as e:
        db.rollback()
        # Clean up uploaded file if database operation fails
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.get("/vendors", response_model=VendorListResponse)
async def get_vendors(
    page: int = 1,
    size: int = 10,
    business_type: Optional[str] = None,
    vendor_status: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    # admin: Customer = Depends(get_admin_user),  # Implement admin auth
    db: Session = Depends(get_db)
):
    """Get list of vendors (Admin only)"""
    offset = (page - 1) * size
    
    # Build query
    query = db.query(Vendor)
    
    # Apply filters
    if business_type:
        query = query.filter(Vendor.business_type == business_type)
    
    if vendor_status:
        query = query.filter(Vendor.vendor_status == vendor_status)
    
    if state:
        query = query.filter(Vendor.state.ilike(f"%{state}%"))
    
    if city:
        query = query.filter(Vendor.city.ilike(f"%{city}%"))
    
    if search:
        query = query.filter(
            or_(
                Vendor.business_name.ilike(f"%{search}%"),
                Vendor.owner_name.ilike(f"%{search}%"),
                Vendor.vendor_code.ilike(f"%{search}%"),
                Vendor.email.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total_count = query.count()
    
    # Get paginated results
    vendors = query.order_by(desc(Vendor.registration_date)).offset(offset).limit(size).all()
    
    return VendorListResponse(
        vendors=vendors,
        total_count=total_count,
        page=page,
        size=size
    )


@router.get("/vendors/{vendor_id}", response_model=VendorDetailResponse)
async def get_vendor_details(
    vendor_id: int,
    # admin: Customer = Depends(get_admin_user),  # Implement admin auth
    db: Session = Depends(get_db)
):
    """Get vendor details by ID (Admin only)"""
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    return vendor


@router.patch("/vendors/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: int,
    status_update: VendorStatusUpdate,
    # admin: Customer = Depends(get_admin_user),  # Implement admin auth
    db: Session = Depends(get_db)
):
    """Update vendor status (Admin only)"""
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Update status
    vendor.vendor_status = status_update.status
    vendor.last_updated = datetime.utcnow()
    
    if status_update.admin_notes:
        vendor.admin_notes = status_update.admin_notes
    
    if status_update.status == VendorStatus.APPROVED:
        vendor.approval_date = datetime.utcnow()
        vendor.rejection_reason = None
    elif status_update.status == VendorStatus.REJECTED:
        vendor.rejection_reason = status_update.rejection_reason
        vendor.approval_date = None
    
    try:
        db.commit()
        db.refresh(vendor)
        
        return {
            "message": f"Vendor status updated to {status_update.status.value}",
            "vendor_id": vendor_id,
            "new_status": vendor.vendor_status.value
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor status"
        )


@router.get("/vendors/my-profile", response_model=VendorDetailResponse)
async def get_my_vendor_profile(
    current_vendor: Vendor = Depends(get_current_vendor),  # Implement vendor auth
    db: Session = Depends(get_db)
):
    """Get current vendor's profile"""
    return current_vendor


@router.patch("/vendors/my-profile")
async def update_my_vendor_profile(
    profile_update: VendorProfileUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),  # Implement vendor auth
    db: Session = Depends(get_db)
):
    """Update current vendor's profile"""
    
    # Only allow updates if vendor is approved or pending
    if current_vendor.vendor_status not in [VendorStatus.APPROVED, VendorStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile updates not allowed for vendors with current status"
        )
    
    # Update fields
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(current_vendor, field) and value is not None:
            setattr(current_vendor, field, value)
    
    current_vendor.last_updated = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(current_vendor)
        
        return {
            "message": "Profile updated successfully",
            "vendor_id": current_vendor.vendor_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/vendors/{vendor_id}/verify-email")
async def verify_vendor_email(
    vendor_id: int,
    verification_token: str,
    db: Session = Depends(get_db)
):
    """Verify vendor email"""
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Here you would implement email verification logic
    # For now, just mark as verified
    vendor.is_email_verified = True
    vendor.last_updated = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/vendors/{vendor_id}/verify-phone")
async def verify_vendor_phone(
    vendor_id: int,
    otp: str,
    db: Session = Depends(get_db)
):
    """Verify vendor phone number"""
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Here you would implement OTP verification logic
    # For now, just mark as verified
    vendor.is_phone_verified = True
    vendor.last_updated = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Phone number verified successfully"}


@router.get("/vendors/stats/dashboard")
async def get_vendor_dashboard_stats(
    # admin: Customer = Depends(get_admin_user),  # Implement admin auth
    db: Session = Depends(get_db)
):
    """Get vendor dashboard statistics (Admin only)"""
    
    total_vendors = db.query(Vendor).count()
    pending_vendors = db.query(Vendor).filter(Vendor.vendor_status == VendorStatus.PENDING).count()
    approved_vendors = db.query(Vendor).filter(Vendor.vendor_status == VendorStatus.APPROVED).count()
    rejected_vendors = db.query(Vendor).filter(Vendor.vendor_status == VendorStatus.REJECTED).count()
    
    # Vendors registered this month
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_vendors = db.query(Vendor).filter(
        Vendor.registration_date >= current_month_start
    ).count()
    
    # Recent registrations (last 10)
    recent_vendors = db.query(Vendor).order_by(desc(Vendor.registration_date)).limit(10).all()
    
    return {
        "total_vendors": total_vendors,
        "pending_vendors": pending_vendors,
        "approved_vendors": approved_vendors,
        "rejected_vendors": rejected_vendors,
        "this_month_vendors": this_month_vendors,
        "recent_vendors": [
            {
                "vendor_id": v.vendor_id,
                "vendor_code": v.vendor_code,
                "business_name": v.business_name,
                "owner_name": v.owner_name,
                "status": v.vendor_status.value,
                "registration_date": v.registration_date
            }
            for v in recent_vendors
        ]
    }


# Helper function placeholders - implement these based on your auth system
async def get_current_vendor():
    """Get current authenticated vendor - implement based on your auth system"""
    pass

async def get_admin_user():
    """Get current admin user - implement based on your auth system"""
    pass