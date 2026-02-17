EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:14b"
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
  "agency": null,
  "year": null,
  "intent": null
}}

Field rules:
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
