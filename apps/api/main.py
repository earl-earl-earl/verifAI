from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def welcome():
  return {"response": "Hello World!"}

@app.get("/index")
def something():
  return {"item": "cake"}