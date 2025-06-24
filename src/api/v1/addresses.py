# # src/api/v1/addresses.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# from config.database import get_db
# from src.models.address import CustomerAddress
# from src.schemas.address import CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressResponse, AddressListResponse
# # from src.services.auth_service import get_current_user
# from src.api.v1.auth import get_current_user

# router = APIRouter()

# @router.get("/addresses", response_model=AddressListResponse)
# async def get_customer_addresses(
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all addresses for the current customer"""
#     addresses = db.query(CustomerAddress).filter(
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).order_by(CustomerAddress.is_default.desc(), CustomerAddress.created_at.desc()).all()
    
#     return AddressListResponse(
#         addresses=addresses,
#         total_count=len(addresses)
#     )

# @router.post("/addresses", response_model=CustomerAddressResponse, status_code=status.HTTP_201_CREATED)
# async def create_address(
#     address_data: CustomerAddressCreate,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Create a new address for the customer"""
    
#     # If this is set as default, unset other default addresses
#     if address_data.is_default:
#         db.query(CustomerAddress).filter(
#             CustomerAddress.customer_id == customer_id,
#             CustomerAddress.is_default == True
#         ).update({CustomerAddress.is_default: False})
    
#     # If this is the first address, make it default
#     existing_count = db.query(CustomerAddress).filter(
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).count()
    
#     if existing_count == 0:
#         address_data.is_default = True
    
#     new_address = CustomerAddress(
#         customer_id=customer_id,
#         **address_data.dict()
#     )
    
#     db.add(new_address)
#     db.commit()
#     db.refresh(new_address)
    
#     return new_address

# @router.get("/addresses/{address_id}", response_model=CustomerAddressResponse)
# async def get_address(
#     address_id: int,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get a specific address"""
#     address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()
    
#     if not address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found"
#         )
    
#     return address

# @router.put("/addresses/{address_id}", response_model=CustomerAddressResponse)
# async def update_address(
#     address_id: int,
#     address_data: CustomerAddressUpdate,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Update an address"""
#     address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()
    
#     if not address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found"
#         )
    
#     # If setting as default, unset other defaults
#     if address_data.is_default:
#         db.query(CustomerAddress).filter(
#             CustomerAddress.customer_id == customer_id,
#             CustomerAddress.address_id != address_id,
#             CustomerAddress.is_default == True
#         ).update({CustomerAddress.is_default: False})
    
#     # Update the address
#     update_data = address_data.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(address, field, value)
    
#     db.commit()
#     db.refresh(address)
    
#     return address

# @router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_address(
#     address_id: int,
#     customer_id: int = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Soft delete an address"""
#     address = db.query(CustomerAddress).filter(
#         CustomerAddress.address_id == address_id,
#         CustomerAddress.customer_id == customer_id,
#         CustomerAddress.is_active == True
#     ).first()
    
#     if not address:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found"
#         )
    
#     # Check if address is used in any orders
#     from src.models.order import Order
#     orders_count = db.query(Order).filter(Order.delivery_address_id == address_id).count()
#     if orders_count > 0:
#         # Soft delete instead of hard delete
#         address.is_active = False
#     else:
#         # Hard delete if no orders associated
#         db.delete(address)
    
#     # If this was the default address, make another one default
#     if address.is_default:
#         next_address = db.query(CustomerAddress).filter(
#             CustomerAddress.customer_id == customer_id,
#             CustomerAddress.address_id != address_id,
#             CustomerAddress.is_active == True
#         ).first()
        
#         if next_address:
#             next_address.is_default = True
    
#     db.commit()










# src/api/v1/addresses.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from src.models.address import CustomerAddress
from src.models.customer import Customer
from src.schemas.address import CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressResponse, AddressListResponse
from src.api.v1.auth import get_current_user  # updated import

router = APIRouter()

@router.get("/addresses", response_model=AddressListResponse)
async def get_customer_addresses(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    addresses = db.query(CustomerAddress).filter(
        CustomerAddress.customer_id == current_user.customer_id,
        CustomerAddress.is_active == True
    ).order_by(
        CustomerAddress.is_default.desc(),
        CustomerAddress.created_at.desc()
    ).all()
    
    return AddressListResponse(
        addresses=addresses,
        total_count=len(addresses)
    )

@router.post("/addresses", response_model=CustomerAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: CustomerAddressCreate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if address_data.is_default:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_user.customer_id,
            CustomerAddress.is_default == True
        ).update({CustomerAddress.is_default: False})
    
    existing_count = db.query(CustomerAddress).filter(
        CustomerAddress.customer_id == current_user.customer_id,
        CustomerAddress.is_active == True
    ).count()
    
    if existing_count == 0:
        address_data.is_default = True
    
    new_address = CustomerAddress(
        customer_id=current_user.customer_id,
        **address_data.dict()
    )
    
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    
    return new_address

@router.get("/addresses/{address_id}", response_model=CustomerAddressResponse)
async def get_address(
    address_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id,
        CustomerAddress.is_active == True
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return address

@router.put("/addresses/{address_id}", response_model=CustomerAddressResponse)
async def update_address(
    address_id: int,
    address_data: CustomerAddressUpdate,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id,
        CustomerAddress.is_active == True
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    if address_data.is_default:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_user.customer_id,
            CustomerAddress.address_id != address_id,
            CustomerAddress.is_default == True
        ).update({CustomerAddress.is_default: False})
    
    update_data = address_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    
    return address

@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: int,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(CustomerAddress).filter(
        CustomerAddress.address_id == address_id,
        CustomerAddress.customer_id == current_user.customer_id,
        CustomerAddress.is_active == True
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    from src.models.order import Order
    orders_count = db.query(Order).filter(Order.delivery_address_id == address_id).count()
    if orders_count > 0:
        address.is_active = False
    else:
        db.delete(address)
    
    if address.is_default:
        next_address = db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_user.customer_id,
            CustomerAddress.address_id != address_id,
            CustomerAddress.is_active == True
        ).first()
        
        if next_address:
            next_address.is_default = True
    
    db.commit()
