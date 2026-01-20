import hashlib
from fastapi import UploadFile
from pypdf import PdfReader
from app.core.models import Document, Chunk
from app.api.deps import SessionDep
from pathlib import Path
from typing import Any, BinaryIO
from app.api.deps import SessionDep
from pdf2image import convert_from_path
import re
import numpy as np
import cv2
import pytesseract
from multiprocessing import Pool
import psutil
import os
from enum import Enum


THAI_MARKS = "่้๊๋ิีึืุูั็์ํเาะโไแใ์"
POPPLER_PATH = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
CONFIG = r"""
--psm 6
-c preserve_interword_spaces=1
"""


class FileExt(Enum):
    MD = "md"
    PDF = "pdf"


async def create_file(file_path: Path | Any, file: UploadFile) -> None:
    contents = await file.read()  # Await the coroutine to get bytes
    with open(file_path, "wb") as buffer:
        buffer.write(contents)


def ingest_md():
    print("ingest markdown")
    # with open(file_path, 'r') as file:
    #     content = file.read()
    #     print(content)


def ingest_pdf(file_path: Path):
    with open(file_path, "rb") as f:
        print(f)


def read_pdf_with_ocr(file_path: Path | Any) -> str:
    cores = psutil.cpu_count(logical=False)
    print(f"This machine has {cores} cores")

    print("Converting PDF to images...")
    pages = convert_from_path(
        file_path, poppler_path=POPPLER_PATH, dpi=400)
    print(f"Processing {len(pages)} pages with OCR...")

    with Pool(processes=2) as pool:
        result = pool.map(process_image, [(i, page)
                          for i, page in enumerate(pages)])
        result = sorted(result, key=lambda r: r[0])
        return " ".join([page for _, page in result])


def process_image(page):
    i, p = page
    img = np.array(p)
    img = preprocess_for_tesseract(img)
    text = pytesseract.image_to_string(
        img, lang='tha+eng', config=CONFIG)

    return (i, text)


# Define allowed extensions for validation
ALLOWED_EXTENSIONS = {".md", ".pdf"}


def allowed_file(filename):
    # Split the filename into name and extension
    _, extension = os.path.splitext(filename)
    # Check if the extension (in lowercase) is in the allowed set
    return extension.lower() in ALLOWED_EXTENSIONS


def preprocess_for_tesseract(img):
    # 1. Load ภาพแบบ Grayscale
    # img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 2. Upscaling (สำคัญมากสำหรับภาษาไทย)
    # ขยายภาพ 2 เท่าเพื่อให้ Tesseract เห็นหัวตัวอักษรชัดขึ้น
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 3. Denoising (ลบจุดรบกวนเล็กๆ)
    img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

    # 4. Binarization (ทำเป็นขาว-ดำ)
    # ใช้ Otsu's Thresholding เพื่อหาค่าแสงที่เหมาะสมอัตโนมัติ
    _, img = cv2.threshold(
        img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 5. Morphological Operations (เชื่อมตัวอักษรที่ขาด)
    # ถ้าตัวหนังสือห่างหรือเส้นบาง เราจะใช้ 'Dilation' เพื่อให้เส้นหนาขึ้นเล็กน้อย
    kernel = np.ones((2, 2), np.uint8)
    # ใช้ Morphological Close เพื่อปิดช่องว่างเล็กๆ ในตัวอักษร
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

    return img


def crop_content_only(img):
    # 1. กลับสีภาพ (ให้พื้นหลังเป็นดำ ตัวอักษรเป็นขาว เพื่อหาขอบเขต)
    inverted = cv2.bitwise_not(img)

    # 2. หาจุดที่มีสีขาว (ซึ่งก็คือตัวหนังสือ)
    points = cv2.findNonZero(inverted)

    # 3. สร้างสี่เหลี่ยมล้อมรอบจุดทั้งหมด
    x, y, w, h = cv2.boundingRect(points)

    # 4. Crop โดยเผื่อขอบ (Padding) ไว้สัก 20-40 pixels ไม่ให้ชิดเกินไป
    padding = 30
    crop = img[max(0, y-padding):min(img.shape[0], y+h+padding),
               max(0, x-padding):min(img.shape[1], x+w+padding)]

    return crop


class Knowledge:
    file_path: str
    file: BinaryIO
    session: SessionDep

    def __init__(self, file: UploadFile, session: SessionDep):
        self.file_path = UPLOAD_DIR / file.filename
        self.file = file.file
        self.session = session

    def __get_hashed_doc(self) -> str:
        reader = PdfReader(self.file)
        pages = [page.extract_text() for _, page in enumerate(reader.pages)]
        print(pages)
        doc_hash = self.__sha256("".join(pages))
        return doc_hash

    def __sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def read_pdf_with_ocr(self):
        print("Converting PDF to images...")
        pages = convert_from_path(
            self.file_path, poppler_path=poppler_path, dpi=400)
        print(f"Processing {len(pages)} pages with OCR...")
        # reader = easyocr.Reader(['th', 'en'], gpu=True)

        threads = []
        full_text = ""

        # with concurrent.futures.ThreadPoolExecutor(max_workers=len(pages)) as executor:
        #     future_to_pages = {executor.submit(
        #         self.read_pdf, page): i for i, page in enumerate(pages)}
        #     for future in concurrent.futures.as_completed(future_to_pages):
        #         text = future.result()
        #         full_text += text

        # for _, page in enumerate(pages):
        #     img = np.array(page)

        # img = self.preprocess_for_easyocr(img)
        # img = self.crop_content_only(img)
        # result = reader.readtext(img, detail=0)
        # text = " ".join(result)

        # img = self.preprocess_for_tesseract(img)
        # img = self.crop_content_only(img)
        # text = pytesseract.image_to_string(
        #     img, lang='tha+eng', config=config)

        # full_text += text

        return full_text

    def preprocess_for_tesseract(self, img):
        # 1. Load ภาพแบบ Grayscale
        # img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # 2. Upscaling (สำคัญมากสำหรับภาษาไทย)
        # ขยายภาพ 2 เท่าเพื่อให้ Tesseract เห็นหัวตัวอักษรชัดขึ้น
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 3. Denoising (ลบจุดรบกวนเล็กๆ)
        img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

        # 4. Binarization (ทำเป็นขาว-ดำ)
        # ใช้ Otsu's Thresholding เพื่อหาค่าแสงที่เหมาะสมอัตโนมัติ
        _, img = cv2.threshold(
            img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. Morphological Operations (เชื่อมตัวอักษรที่ขาด)
        # ถ้าตัวหนังสือห่างหรือเส้นบาง เราจะใช้ 'Dilation' เพื่อให้เส้นหนาขึ้นเล็กน้อย
        kernel = np.ones((2, 2), np.uint8)
        # ใช้ Morphological Close เพื่อปิดช่องว่างเล็กๆ ในตัวอักษร
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

        return img

    def preprocess_for_easyocr(self, img):
        # 1. โหลดภาพ
        # img = cv2.imread(image_path)
        # 2. แปลงเป็นขาวดำ (Grayscale)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 3. ลด Noise ด้วย Gaussian Blur (เบาๆ)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        # 4. ทำ Adaptive Thresholding
        # ช่วยให้ตัวอักษรชัดขึ้นแม้แสงในภาพจะไม่เท่ากัน
        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        return thresh

    def read_pdf(self, page):
        img = np.array(page)
        img = self.preprocess_for_tesseract(img)
        img = self.crop_content_only(img)
        text = pytesseract.image_to_string(
            img, lang='tha+eng', config=config)
        return text

    def clean_thai_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u200b", "")
        text = re.sub(r"([ก-ฮ])\s+([ก-ฮ])", r"\1\2", text)
        text = re.sub(rf"([ก-ฮ])\s+([{THAI_MARKS}])", r"\1\2", text)
        text = re.sub(rf"([{THAI_MARKS}])\s+([ก-ฮ])", r"\1\2", text)
        text = re.sub(
            rf"([{THAI_MARKS}])\s+([{THAI_MARKS}])", r"\1\2", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def crop_content_only(self, cv_img):
        # 1. กลับสีภาพ (ให้พื้นหลังเป็นดำ ตัวอักษรเป็นขาว เพื่อหาขอบเขต)
        inverted = cv2.bitwise_not(cv_img)

        # 2. หาจุดที่มีสีขาว (ซึ่งก็คือตัวหนังสือ)
        points = cv2.findNonZero(inverted)

        # 3. สร้างสี่เหลี่ยมล้อมรอบจุดทั้งหมด
        x, y, w, h = cv2.boundingRect(points)

        # 4. Crop โดยเผื่อขอบ (Padding) ไว้สัก 20-40 pixels ไม่ให้ชิดเกินไป
        padding = 30
        crop = cv_img[max(0, y-padding):min(cv_img.shape[0], y+h+padding),
                      max(0, x-padding):min(cv_img.shape[1], x+w+padding)]

        return crop

    def insert_document(self) -> None:
        doc = Document(
            source=f"{self.file_path}",
            source_type="pdf",
            checksum=self.__get_hashed_doc(),
            chunks=[
                Chunk(
                    content="content....",
                    content_hash="2f2fj2fjlfjljwelf",
                    token_count=2
                )
            ]
        )

        self.session.add(doc)
        self.session.commit()
