from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, Float, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from models import ItemSchema, UserSchema  # Updated imports for Pydantic schemas
from passlib.context import CryptContext

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./db.sqlite"  # Async SQLite database URL
Base = declarative_base()

# ORM Models
class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    category = Column(String, nullable=True)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database class for operations
class Database:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=True)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize the database and create tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def clear_data(self):
        """Truncate all data from tables."""
        async with self.engine.begin() as conn:
            await conn.execute("PRAGMA foreign_keys = OFF;")  # Disable foreign keys (SQLite specific)
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(f"DELETE FROM {table.name};")
            await conn.execute("PRAGMA foreign_keys = ON;")  # Re-enable foreign keys

    async def reset_database(self):
        """Drop all tables and recreate the schema."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def create_item(self, item: ItemSchema):
        """Create a new item."""
        async with self.SessionLocal() as session:
            try:
                db_item = ItemModel(**item.dict())
                session.add(db_item)
                await session.commit()
                await session.refresh(db_item)
                return db_item
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500, detail=f"Error creating item: {str(e)}"
                )

    async def get_item(self, item_id: int):
        """Retrieve an item by ID."""
        async with self.SessionLocal() as session:
            result = await session.execute(select(ItemModel).where(ItemModel.id == item_id))
            item = result.scalars().first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return item

    async def get_all_items(self):
        """Retrieve all items."""
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(select(ItemModel))
                return result.scalars().all()
            except SQLAlchemyError as e:
                raise HTTPException(
                    status_code=500, detail=f"Database error: {str(e)}"
                )

    async def update_item(self, item_id: int, item_data: ItemSchema):
        async with self.SessionLocal() as session:  # New session for the update
            item = await self.get_item_by_id(item_id)  # Get the item within this session
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")

            # Update item properties
            item.name = item_data.name
            item.price = item_data.price
            item.description = item_data.description
            item.stock = item_data.stock
            item.category = item_data.category

            session.add(item)  # Add the updated item back to the session
            await session.commit()  # Commit the changes
            return item

    async def get_item_by_id(self,item_id: int):
        async with self.SessionLocal() as session:  # Ensure session is used properly
            result = await session.execute(select(ItemModel).where(ItemModel.id == item_id))
            item = result.scalars().first()  # Get the item from the result
            return item

    async def delete_item(self, item_id: int):
        """Delete an item."""
        async with self.SessionLocal() as session:
            db_item = await self.get_item(item_id)
            if db_item:
                await session.delete(db_item)
                await session.commit()
                return db_item
            raise HTTPException(status_code=404, detail="Item not found")

    async def create_user(self, user: UserSchema):
        async with self.SessionLocal() as session:
            try:
                # Check if the user already exists before adding
                existing_user = await self.get_user_by_email(user.email)
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")

                db_user = UserModel(email=user.email, hashed_password=pwd_context.hash(user.password))
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                return db_user
            except SQLAlchemyError as e:
                print(f"Error creating user: {e}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Could not create user")

    async def get_user(self, user_id: int):
        """Retrieve a user by ID."""
        async with self.SessionLocal() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user

    async def get_user_by_email(self, email: str):
        """Retrieve a user by email."""
        async with self.SessionLocal() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            user = result.scalars().first()
            return user

    async def verify_password(self, plain_password: str, hashed_password: str):
        """Verify if the password matches the stored hash."""
        return pwd_context.verify(plain_password, hashed_password)


