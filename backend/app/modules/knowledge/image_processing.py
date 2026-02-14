from pdf2image import convert_from_path
import psutil
from multiprocessing import Pool
from app.modules.knowledge.main import Ingestion
import cv2
import numpy as np
import pytesseract

POPPLER_PATH = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
CONFIG = r"""
--psm 6
-c preserve_interword_spaces=1
"""


def read_pdf_with_ocr(self: Ingestion) -> list[tuple[int, str]]:
    print("Converting PDF to images...")
    pages = convert_from_path(
        self.file_path,
        poppler_path=POPPLER_PATH,
        dpi=400,
    )
    print(f"Processing {len(pages)} pages with OCR...")
    cores = psutil.cpu_count(logical=False)
    print(f"This machine has {cores} cores")

    with Pool(processes=cores) as pool:
        result = pool.map(process_image, [(i, page)
                          for i, page in enumerate(pages)])
        result = sorted(result, key=lambda r: r[0])
        return " ".join([page for _, page in result])


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
        img,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    # 5. Morphological Operations (เชื่อมตัวอักษรที่ขาด)
    # ถ้าตัวหนังสือห่างหรือเส้นบาง เราจะใช้ 'Dilation' เพื่อให้เส้นหนาขึ้นเล็กน้อย
    kernel = np.ones((2, 2), np.uint8)
    # ใช้ Morphological Close เพื่อปิดช่องว่างเล็กๆ ในตัวอักษร
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

    return img


def preprocess_for_easyocr(img):
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


def process_image(page):
    i, p = page
    img = np.array(p)
    img = preprocess_for_tesseract(img)
    text = pytesseract.image_to_string(img, lang="tha+eng", config=CONFIG)

    return (i, text)


def crop_content_only(cv_img):
    # 1. กลับสีภาพ (ให้พื้นหลังเป็นดำ ตัวอักษรเป็นขาว เพื่อหาขอบเขต)
    inverted = cv2.bitwise_not(cv_img)

    # 2. หาจุดที่มีสีขาว (ซึ่งก็คือตัวหนังสือ)
    points = cv2.findNonZero(inverted)

    # 3. สร้างสี่เหลี่ยมล้อมรอบจุดทั้งหมด
    x, y, w, h = cv2.boundingRect(points)

    # 4. Crop โดยเผื่อขอบ (Padding) ไว้สัก 20-40 pixels ไม่ให้ชิดเกินไป
    padding = 30
    crop = cv_img[
        max(0, y - padding): min(cv_img.shape[0], y + h + padding),
        max(0, x - padding): min(cv_img.shape[1], x + w + padding),
    ]

    return crop
