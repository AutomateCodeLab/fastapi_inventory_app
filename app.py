from fastapi import FastAPI, HTTPException, Response, status, Depends
from fastapi.logger import logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
import yaml
from models import ItemSchema, UserSchema  # Import Pydantic schemas
from database import Database
from middleware import log_request_data

# Load configuration from YAML
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Create FastAPI instance
app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"]
)

# Initialize database
database = Database()


# Initialize the database on startup
@app.on_event("startup")
async def startup():
    await database.init_db()

# Clear all data on shutdown
@app.on_event("shutdown")
async def shutdown():
    await database.clear_data()

# Middleware for logging request data
app.middleware("http")(log_request_data)

# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Root endpoint - Introduction
@app.get("/", response_model=dict)
def read_root():
    return {"message": "Welcome to the Web Development Basics API using FastAPI!"}

# User registration
@app.post("/register/")
async def register(user: UserSchema):
    print("User email"+user.email)
    # Check if the user already exists
    existing_user = await database.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the new user
    db_user = await database.create_user(user)
    return db_user


# Token generation and user authentication
@app.post("/token")
async def login(form_data: UserSchema):
    user = await database.get_user_by_email(form_data.email)
    logger.debug(f"Retrieved user: {user}")
    if not user:
        logger.error("User not found")
        raise HTTPException(status_code=404, detail="User not found")
    if not await database.verify_password(form_data.password, user.hashed_password):
        logger.error("Incorrect password for user: %s", form_data.email)
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"access_token": user.email, "token_type": "bearer"}

# Create an item - POST request
@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemSchema):
    return await database.create_item(item)

# Retrieve an item - GET request
@app.get("/items/{item_id}", response_model=ItemSchema)
async def get_item(item_id: int):
    item = await database.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Retrieve all items - GET request
@app.get("/items/", response_model=list[ItemSchema])
async def get_all_items():
    return await database.get_all_items()

# Update an item - PUT request
@app.put("/items/{item_id}", response_model=ItemSchema)
async def update_item(item_id: int, item: ItemSchema):
    updated_item = await database.update_item(item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

# Delete an item - DELETE request
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    deleted_item = await database.delete_item(item_id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Route to handle favicon.ico requests
@app.get("/favicon.ico", response_class=Response)
async def favicon():
    return Response(status_code=204)  # No Content

# Reset Database Route
@app.post("/reset-database/")
async def reset_database():
    await database.reset_database()
    return {"detail": "Database reset successfully"}

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config["app"]["host"],
        port=config["app"]["port"]
    )
