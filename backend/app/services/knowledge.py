import hashlib
from fastapi import UploadFile
from pypdf import PdfReader
import shutil
from app.core.models import Document, Chunk
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from app.api.deps import SessionDep
import pytesseract
from pdf2image import convert_from_path
import re
import numpy as np
import cv2

THAI_MARKS = "่้๊๋ิีึืุูั็์ํเาะโไแใ์"
# Create an upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
poppler_path = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
# config = r"""
# --oem 3
# --psm 6
# -c preserve_interword_spaces=1
# """
config = '--psm6'


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

    def create_file(self) -> None:
        with open(self.file_path, "wb") as buffer:
            shutil.copyfileobj(self.file, buffer)

    def read_pdf_with_ocr(self):
        import easyocr

        print("Converting PDF to images...")
        pages = convert_from_path(
            self.file_path, poppler_path=poppler_path, dpi=400)
        print(f"Processing {len(pages)} pages with OCR...")
        reader = easyocr.Reader(['th', 'en'], gpu=True)

        # img = np.array(pages[0])
        # img = self.preprocess_for_easyocr(img)
        # cv2.imwrite(f'prepared_image.jpg', img)
        # result = reader.readtext(img, detail=0)
        # text = "\n".join(result)
        # return text

        full_text = ""
        for i, page in enumerate(pages):
            img = np.array(page)
            # img = self.preprocess_for_tesseract(page)
            # img = self.preprocess_for_easyocr(img)
            img = self.auto_crop(img)
            # text = pytesseract.image_to_string(
            #     img, lang='tha+eng', config=config)

            # cv2.imwrite(f'prepared_image-{i}.jpg', img)
            result = reader.readtext(img, detail=0)
            text = "\n".join(result)

            # Formatting distinct pages
            full_text += f"\n--- Page {i + 1} ---\n"
            full_text += text
        return full_text

    def clean_thai_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u200b", "")
        text = re.sub(r"([ก-ฮ])\s+([ก-ฮ])", r"\1\2", text)
        text = re.sub(rf"([ก-ฮ])\s+([{THAI_MARKS}])", r"\1\2", text)
        text = re.sub(rf"([{THAI_MARKS}])\s+([ก-ฮ])", r"\1\2", text)
        text = re.sub(
            rf"([{THAI_MARKS}])\s+([{THAI_MARKS}])", r"\1\2", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def preprocess_for_tesseract(self, img):
        img = np.array(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(2.0, (8, 8))
        gray = clahe.apply(gray)
        th = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 11
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
        return th

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

    def auto_crop(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # กลับสีภาพเพื่อให้ตัวหนังสือเป็นสีขาว พื้นหลังเป็นสีดำ (สำหรับหา Contour)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # หาขอบเขตของวัตถุทั้งหมดในภาพ
        cnts = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        # รวมทุกจุดเข้าด้วยกันเพื่อหากรอบสี่เหลี่ยมที่ครอบคลุมเนื้อหาทั้งหมด
        all_cnts = np.concatenate(cnts)
        x, y, w, h = cv2.boundingRect(all_cnts)

        return image[y:y+h, x:x+w]

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
