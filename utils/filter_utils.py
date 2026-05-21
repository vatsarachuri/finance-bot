import re

def is_inappropriate(text):
    bad_words = ["sex", "porn", "kill", "hate", "suicide", "fuck", "bitch","dengey"]
    return any(w in text.lower() for w in bad_words)

def is_gibberish(text):
    return len(text.strip()) < 3 or re.fullmatch(r"[^a-zA-Z0-9 ]+", text)
