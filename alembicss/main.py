from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from alembicss import crud, models, schemas, database

app = FastAPI()

# Dependency
async def get_db():
    async with database.SessionLocal() as db:
        yield db

@app.post("/items/", response_model=schemas.ItemResponse)
async def create_item(
    item: schemas.ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    return await crud.create_item(db=db, item=item)

@app.get("/items/", response_model=list[schemas.ItemResponse])
async def read_items(
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_items(db)
