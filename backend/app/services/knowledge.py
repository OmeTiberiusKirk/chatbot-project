import hashlib
from fastapi import UploadFile, Form
from pypdf import PdfReader
from app.core.models import Document, Chunk
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from app.api.deps import SessionDep
from pdf2image import convert_from_path
import re
import numpy as np
import cv2
import pytesseract
from multiprocessing import Pool
import psutil
import os
from typing import Annotated


THAI_MARKS = "่้๊๋ิีึืุูั็์ํเาะโไแใำ"
POPPLER_PATH = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
CONFIG = r"""
--psm 6
-c preserve_interword_spaces=1
"""
# Define allowed extensions for validation
ALLOWED_EXTENSIONS = {".md", ".pdf"}
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60
WORDS = [
    ("บารุง", "บำรุง"),
    ("ศึกษำ", "ศึกษา"),
    ("เอกสำร", "เอกสาร"),
    ("สัญญำ", "สัญญา"),
    ("งำน", "งาน"),
    ("ข่ำว", "ข่าว"),
    ("อย่ำง", "อย่าง"),
    ("บำท", "บาท"),
    ("อนุญำต", "อนุญาต"),
    ("ควำม", "ความ"),
    ("ชั่วครำว", "ชั่วคราว"),
    ("รักษำ", "รักษา"),
    ("พยำบำล", "พยาบาล"),
    ("วิเครำะห์", "วิเคราะห์"),
    ("เวลำ", "เวลา"),
    ("ถัดจำก", "ถัดจาก"),
    ("บริกำร", "บริการ"),
    ("ตำม", "ตาม"),
    ("รำชกำร", "ราชการ"),
    ("เหมำะสม", "เหมาะสม"),
    ("บริหำร", "บริหาร"),
    ("จัดกำร", "จัดการ"),
    ("บัญชีกลำง", "บัญชีกลาง"),
    ("(คมนำคม)|(คมำคม)", "คมนาคม"),
    ("สำมำรถ", "สามารถ"),
    ("กำรมอบหมำย", "การมอบหมาย"),
    ("ภำรกิจ", "ภารกิจ"),
    ("สำรบรรณ", "สารบรรณ"),
    ("รำคำ", "ราคา"),
    ("กำรประชำสัมพันธ์", "การประชาสัมพันธ์"),
    ("ประกำศ", "ประกาศ"),
    ("กำรบูรณำกำร", "การบูรณาการ"),
    ("พิจำรณำจำก", "พิจารณาจาก"),
    ("ฮำร์ดแวร์", "ฮาร์ดแวร์"),
    ("อัตรำ", "อัตรา"),
    ("ฐำนข้อมูล", "ฐานข้อมูล"),
    ("วิทยำกำร", "วิทยาการ"),
    ("สำขำ", "สาขา"),
    ("ประสบกำรณ์", "ประสบการณ์"),
    ("กำรต่อต้ำน", "การต่อต้าน"),
    ("กำรทุจริต", "การทุจริต"),
    ("กำรบำรุง", "การบำรุง"),
    ("แจ้งจำก", "แจ้งจาก"),
    ("ชำนำญกำร", "ชำนาญการ"),
    ("ปฏิบัติกำร", "ปฏิบัติการ"),
    ("ภำยใน", "ภายใน"),
    ("ค่ำบริการ", "ค่าบริการ"),
    ("จ้ำง", "จ้าง"),
    ("ปัญหำ", "ปัญหา"),
    ("ภำษำ", "ภาษา"),
    ("จานวน", "จำนวน"),
    ("นามา", "นำมา"),
    ("ชาระ", "ชำระ"),
    ("กำรทำงาน", "การทำงาน"),
    ("กำรพัฒนำ", "การพัฒนา"),
    ("สำรสนเทศ", "สารสนเทศ"),
    ("ทิงงาน", "ทิ้งงาน"),
    ("ถ่ำย", "ถ่าย"),
    ("วิชำกำร", "วิชาการ"),
    ("ธนำคำร", "ธนาคาร"),
]


class KnowledgeService:
    session: SessionDep

    def __init__(self, session: SessionDep):
        self.session = session


class Ingestion(KnowledgeService):
    upload_file = UploadFile
    file_path: str
    file: BinaryIO
    doc_meta: dict

    def __init__(
        self,
        session: SessionDep,
        upload_file: UploadFile,
        agency: Annotated[str, Form()],
        year: Annotated[int, Form()],
    ):
        super().__init__(session)
        self.upload_file = upload_file
        self.file_path = UPLOAD_DIR / upload_file.filename
        self.file = upload_file.file
        self.doc_meta = {"agency": agency, "year": year}

    def hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def read_pdf_with_ocr(self):
        print("Converting PDF to images...")
        pages = convert_from_path(self.file_path, poppler_path=POPPLER_PATH, dpi=400)
        print(f"Processing {len(pages)} pages with OCR...")
        cores = psutil.cpu_count(logical=False)
        print(f"This machine has {cores} cores")

        with Pool(processes=cores) as pool:
            result = pool.map(
                self.process_image, [(i, page) for i, page in enumerate(pages)]
            )
            result = sorted(result, key=lambda r: r[0])
            return " ".join([page for _, page in result])

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
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

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
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        return thresh

    def process_image(self, page):
        i, p = page
        img = np.array(p)
        img = self.preprocess_for_tesseract(img)
        text = pytesseract.image_to_string(img, lang="tha+eng", config=CONFIG)

        return (i, text)

    def clean_thai_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u200b", "")
        text = re.sub(rf"([ก-ฮ])\s+([{THAI_MARKS}])", r"\1\2", text)
        text = re.sub(rf"([{THAI_MARKS}])\s+([ก-ฮ])", r"\1\2", text)
        text = re.sub(rf"([{THAI_MARKS}])\s+([{THAI_MARKS}])", r"\1\2", text)
        # text = re.sub(r"\s{2,}", " ", text)
        # text = re.sub(r"\n", "", text)
        for word in WORDS:
            text = re.sub(rf"{word[0]}", word[1], text)
        return text.strip()

    def thai_sentence_split(self, text: str):
        # แบ่งโดยใช้ newline และ punctuation ไทย/สากล เป็นหลัก
        # (ไม่ใช้ tokenizer ชั้นสูงเพื่อหลีกเลี่ยง dependency)
        pieces = re.split(r"([\n]+|[।\.\?\!])+", text)
        # รวมชิ้นที่เป็นเนื้อหา
        out = []
        buffer = ""
        for p in pieces:
            if not p:
                continue
            buffer += p
            # ถ้าจบด้วยเครื่องหมายจบประโยคหรือ newline ให้เป็นประโยค
            if re.search(r"[।\.\?\!]\s*$", p) or "\n" in p:
                s = buffer.strip()
                if s:
                    out.append(s)
                buffer = ""
        if buffer.strip():
            out.append(buffer.strip())
        return out

    def crop_content_only(self, cv_img):
        # 1. กลับสีภาพ (ให้พื้นหลังเป็นดำ ตัวอักษรเป็นขาว เพื่อหาขอบเขต)
        inverted = cv2.bitwise_not(cv_img)

        # 2. หาจุดที่มีสีขาว (ซึ่งก็คือตัวหนังสือ)
        points = cv2.findNonZero(inverted)

        # 3. สร้างสี่เหลี่ยมล้อมรอบจุดทั้งหมด
        x, y, w, h = cv2.boundingRect(points)

        # 4. Crop โดยเผื่อขอบ (Padding) ไว้สัก 20-40 pixels ไม่ให้ชิดเกินไป
        padding = 30
        crop = cv_img[
            max(0, y - padding) : min(cv_img.shape[0], y + h + padding),
            max(0, x - padding) : min(cv_img.shape[1], x + w + padding),
        ]

        return crop

    def insert_document(
        self,
        pages: list[tuple[int, str]],
        chunks: list[tuple[int, str]],
    ) -> None:
        doc = Document(
            source=f"{self.file_path}",
            source_type=self.get_file_ext()[1:],
            checksum=self.hash_text("".join([page[1] for page in pages])),
            doc_metadata=self.doc_meta,
            chunks=[
                Chunk(
                    content=chunk[1],
                    content_hash=self.hash_text(chunk[1]),
                    token_count=1,
                )
                for chunk in chunks
            ],
        )

        self.session.add(doc)
        self.session.commit()

    def allowed_file(self):
        # Split the filename into name and extension
        _, extension = os.path.splitext(self.upload_file.filename)
        # Check if the extension (in lowercase) is in the allowed set
        return extension.lower() in ALLOWED_EXTENSIONS

    def ingest_md():
        print("ingest markdown")
        # with open(file_path, 'r') as file:
        #     content = file.read()
        #     print(content)

    def ingest_pdf(self):
        with open(self.file_path, "rb") as byte:
            reader = PdfReader(byte)
            pages: list[tuple[int, str]] = []

            for pageno, page in enumerate(reader.pages):
                t = page.extract_text() or ""
                t = self.clean_thai_text(t)
                pages.append((pageno, t))

            chunks = self.chunk_texts(pages)
            self.insert_document(pages, chunks)
            return chunks

    def chunk_texts(self, pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
        chunks = []
        chunk_id = 0
        for pageno, text in pages:
            sentences = self.thai_sentence_split(text)
            # join sentences into windows of approx chunk_size words (word ~ token)
            words = " ".join(sentences).split()
            i = 0
            while i < len(words):
                chunk_words = words[i : i + CHUNK_SIZE]
                chunk_text = " ".join(chunk_words).strip()

                if chunk_text:
                    chunks.append(
                        (
                            pageno,
                            # "metadata": METADATA,
                            chunk_text,
                        )
                    )
                    chunk_id += 1

                i += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    async def create_file(self) -> None:
        contents = await self.upload_file.read()
        with open(self.file_path, "wb") as buffer:
            buffer.write(contents)

    def get_file_ext(self):
        _, extension = os.path.splitext(self.upload_file.filename)
        return extension
