from fastapi import FastAPI , HTTPException
from pydantic import BaseModel , Field
from uuid import UUID

app = FastAPI()
