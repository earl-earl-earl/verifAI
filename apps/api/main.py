from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
  name: str
  price: float
  is_offer: bool = False

items: list[Item] = []

@app.get("/")
def welcome():
  return {"response": "Hello World!"}

@app.post("/items/")
def add_item(item: Item):
    items.append(item)
    return {
      "status": "Success",
      "code": 200,
      "message": f"{item.name} has been added successfully"
    }

@app.get("/items/")
def get_all_items():
  return items