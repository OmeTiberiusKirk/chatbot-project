EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.1:8b"
ALPHA = 0.6
TOP_K = 5
CANDIDATE_MULT = 4
NOT_FOUND_THRESHOLD = 0.12
METADATA_PROMPT = """
You are an NLP system that extracts structured metadata from a Thai user question.

Strict rules:
- Output VALID JSON only
- No explanation
- No markdown
- Do not add or remove fields

Return EXACTLY this JSON structure:
{{
  "contact_number": null,
  "agency": null,
  "year": null,
  "intent": null
}}

Field rules:
- contact_number: number of the contact or TOR(Terms of Reference).
- agency: Name of the agency, organization, or university.
- year: Buddhist year (พ.ศ.) as number if mentioned
- intent MUST be inferred from the question wording

Intent inference rules:
- If the question asks for quantity (e.g. กี่, จำนวนเท่าไหร่) → intent = count
- If the question asks to find or show documents → intent = search
- If the question asks to summarize → intent = summary

If no intent can be inferred, keep intent as null.

Question:
\"\"\"{question}\"\"\"
"""
QUESTION_PROMPT = """
คุณเป็นผู้ช่วยที่ตอบคำถามโดยอ้างอิงจากข้อมูลที่ให้มาเท่านั้น

ข้อบังคับ:
- ตอบเป็นภาษาไทยทั้งหมด
- ใช้ภาษาสุภาพ ชัดเจน และเป็นทางการ
- ห้ามเดา หรือแต่งข้อมูลเพิ่มจากความรู้ภายนอก
- หากข้อมูลใน Context ไม่เพียงพอ ให้ตอบว่า "ไม่พบข้อมูลในเอกสาร"
- อนุญาตให้ใช้ศัพท์เทคนิคภาษาอังกฤษได้เฉพาะกรณีจำเป็น และต้องอธิบายเป็นภาษาไทย

รูปแบบคำตอบ:
- ตอบให้ตรงคำถาม
- หากมีหลายประเด็น ให้ตอบเป็นข้อๆ

### Context
{context}

### Question
{question}

### Answer (ตอบเป็นภาษาไทย):
"""
SEARCH_PROMPT = """
คุณเป็นผู้ช่วยที่ตอบคำถามโดยอ้างอิงจากข้อมูลที่ให้มาเท่านั้น

ข้อบังคับ:
- ตอบเป็นภาษาไทยทั้งหมด
- ใช้ภาษาสุภาพ ชัดเจน และเป็นทางการ
- ห้ามเดา หรือแต่งข้อมูลเพิ่มจากความรู้ภายนอก
- หากข้อมูลใน Context ไม่เพียงพอ ให้ตอบว่า "ไม่พบข้อมูล"
- อนุญาตให้ใช้ศัพท์เทคนิคภาษาอังกฤษได้เฉพาะกรณีจำเป็น และต้องอธิบายเป็นภาษาไทย

รูปแบบคำตอบ:
- ตอบให้ตรงคำถาม
- ให้ตอบเป็นข้อๆ

### Context
{context}

### Question
{question}

### Answer (ตอบเป็นภาษาไทย):
"""
