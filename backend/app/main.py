from fastapi import FastAPI, UploadFile

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/uploadfile")
async def upload_file(file: UploadFile):
    return {"filename": file.filename}
