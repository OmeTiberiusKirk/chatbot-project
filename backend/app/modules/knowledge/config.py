EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5"
ALPHA = 0.6
TOP_K = 5
CANDIDATE_MULT = 4
NOT_FOUND_THRESHOLD = 0.12
METADATA_PROMPT = """
    You are an NLP system that extracts structured metadata from a user question.
    Return ONLY valid JSON.
    No markdown.
    Thai langquage
        
    Fields:
    - agency: organization or university
    - year: Year of document

    Rules:
    - Only extract what is explicitly stated or clearly implied
    - If missing, use null or empty array

    Question:
    \"\"\"{question}\"\"\"
"""
