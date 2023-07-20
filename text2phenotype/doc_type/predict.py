import re
from typing import List

from text2phenotype.apm.metrics import text2phenotype_capture_span
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY


@text2phenotype_capture_span()
def get_doc_types(text: str, classifier, stop_words) -> List[dict]:
    if not text:
        return []

    results = []

    start = 0
    for page_text in text.split(OCR_PAGE_SPLITTING_KEY[0]):
        if not page_text:
            start += 1
            continue

        end = start + len(page_text)

        clean_text = clean_ocr_text(page_text, stop_words)

        prediction = classifier.predict(clean_text)
        if text[start:end] != page_text:
            raise Exception('Text location is incorrect!')

        results.append({"label": prediction[0][0][9:],
                        "text": clean_text[:50],
                        "range": (start, end),
                        "prob": prediction[1][0]})

        start = end + 1

    return results


def clean_ocr_text(text, stop_words):
    # Lowercase all text
    text = text.lower()

    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]', ' ', text)

    # Remove special characters
    text = text.translate({ord(c): " " for c in r"!@'#$%^&*()[]{};:,./<>?\|`~-=_+"})

    # Remove multi-space
    text = re.sub(' +', ' ', text)

    # Strip spaces and line returns
    text = text.strip().replace('\n', ' ')

    # Remove stop words ***
    text = " ".join([token for token in text.split() if token not in stop_words])

    # remove URLs
    text = re.sub(r'http\S+', ' ', text)

    # remove hours
    text = re.sub(r'(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]', ' ', text)

    # remove various data formats
    text = re.sub(r'(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]|(?:Jan|Mar|May|Jul|Aug|Oct|Dec)))\1|(?:(?:29|30)(\/|-|\.)'
                  r'(?:0?[1,3-9]|1[0-2]|(?:Jan|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\2))'
                  r'(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)(?:0?2|(?:Feb))\3(?:(?:(?:1[6-9]|[2-9]\d)?'
                  r'(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])'
                  r'(\/|-|\.)(?:(?:0?[1-9]|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep))|(?:1[0-2]|(?:Oct|Nov|Dec)))'
                  r'\4(?:(?:1[6-9]|[2-9]\d)?\d{2})', ' ', text)

    # Remove multi-space
    return re.sub(' +', ' ', text)
