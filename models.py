from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy base model
Base = declarative_base()

### SQLAlchemy Models ###

# SQLAlchemy Item Model
class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=True)

# SQLAlchemy User Model
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Store hashed passwords!

### Pydantic Models ###

# Pydantic Item Model (Request/Response)
class ItemSchema(BaseModel):
    id: Optional[int]
    name: str = Field(..., example="Laptop")
    price: float = Field(..., gt=0, example=999.99)
    description: Optional[str] = Field(None, example="A high-end laptop")
    stock: int = Field(..., ge=0, example=10)
    category: Optional[str] = Field(None, example="Electronics")

    class Config:
        orm_mode = True  # Allows SQLAlchemy models to be serialized

# Pydantic User Model (Request/Response)
class UserSchema(BaseModel):
    email: EmailStr
    password: str  # For demo only! Use hashed passwords in production.

    class Config:
        orm_mode = True  # Allows SQLAlchemy models to be serialized
