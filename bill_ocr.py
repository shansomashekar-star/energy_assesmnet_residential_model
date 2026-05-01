import os
import re
from typing import Dict, Optional

import pymupdf
import pytesseract
from PIL import Image


def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []

    doc = pymupdf.open(file_path)
    for page in doc:
        text = page.get_text()
        if text:
            text_parts.append(text)

    return "\n".join(text_parts).strip()


def extract_text_from_image(file_path: str) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)

        # If PDF text extraction gives enough content, use it.
        if len(text.strip()) > 100:
            return text

        # Fallback: render first page and OCR it.
        doc = pymupdf.open(file_path)
        if len(doc) == 0:
            return ""

        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        temp_image_path = file_path + "_page1.png"
        pix.save(temp_image_path)

        try:
            return extract_text_from_image(temp_image_path)
        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    return extract_text_from_image(file_path)


def find_first_money_amount(text: str) -> Optional[float]:
    patterns = [
        r"total\s+amount\s+due[:\s$]*([0-9,]+\.\d{2})",
        r"amount\s+due[:\s$]*([0-9,]+\.\d{2})",
        r"total\s+due[:\s$]*([0-9,]+\.\d{2})",
        r"current\s+charges[:\s$]*([0-9,]+\.\d{2})",
    ]

    lower_text = text.lower()

    for pattern in patterns:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    return None


def find_kwh_usage(text: str) -> Optional[float]:
    patterns = [
        r"([0-9,]+(?:\.\d+)?)\s*kwh",
        r"electric(?:ity)?\s+usage[:\s]*([0-9,]+(?:\.\d+)?)",
        r"usage[:\s]*([0-9,]+(?:\.\d+)?)\s*kwh",
    ]

    lower_text = text.lower()

    for pattern in patterns:
        matches = re.findall(pattern, lower_text, re.IGNORECASE)
        if matches:
            values = [float(m.replace(",", "")) for m in matches]
            reasonable_values = [v for v in values if 10 <= v <= 10000]
            if reasonable_values:
                return max(reasonable_values)

    return None


def find_dates(text: str):
    date_patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]

    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text))

    return dates


def find_utility_provider(text: str) -> str:
    known_providers = ["PSE&G", "PSEG", "Con Edison", "National Grid", "Duke Energy", "PG&E"]

    for provider in known_providers:
        if provider.lower() in text.lower():
            return provider

    first_line = text.strip().splitlines()[0] if text.strip() else "Unknown"
    return first_line[:80]


def parse_bill_text(text: str) -> Dict:
    kwh = find_kwh_usage(text)
    amount = find_first_money_amount(text)
    dates = find_dates(text)

    return {
        "electricity_kwh": kwh,
        "bill_amount_usd": amount,
        "billing_period_start": dates[0] if len(dates) >= 1 else None,
        "billing_period_end": dates[1] if len(dates) >= 2 else None,
        "utility_provider": find_utility_provider(text),
        "meter_number": None,
        "ocr_text_preview": text[:1000],
        "ocr_confidence": "needs_review" if not kwh or not amount else "medium"
    }


def extract_bill_data_real(file_path: str) -> Dict:
    text = extract_text_from_file(file_path)
    return parse_bill_text(text)