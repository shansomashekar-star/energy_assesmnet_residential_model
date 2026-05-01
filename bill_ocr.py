import os
import re
from typing import Dict, Optional

import pymupdf
import pytesseract
from PIL import Image
from datetime import datetime


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
        r"this\s+month[’'`s]*\s+charges\s+and\s+credits\s*\$?\s*([0-9,]+\.\d{2})",
        r"current\s+charges\s*\$?\s*([0-9,]+\.\d{2})",
        r"new\s+charges\s*\$?\s*([0-9,]+\.\d{2})",
        r"electric\s+charges\s*\$?\s*([0-9,]+\.\d{2})",
        r"total\s+amount\s+due(?:\s+by\s+[A-Za-z]+\s+\d{1,2},\s+\d{4})?\s*\$?\s*([0-9,]+\.\d{2})",
        r"amount\s+due\s*\$?\s*([0-9,]+\.\d{2})",
        r"total\s+due\s*\$?\s*([0-9,]+\.\d{2})",
    ]

    cleaned_text = text.replace("", "'").replace("’", "'")

    for pattern in patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
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


def normalize_date(date_text: str) -> str:
    date_text = date_text.strip()

    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_text


def find_dates(text: str):
    period_pattern = (
        r"for\s+the\s+period[:\s]+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        r"\s+to\s+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})"
    )

    period_match = re.search(period_pattern, text, re.IGNORECASE)
    if period_match:
        return [
            normalize_date(period_match.group(1)),
            normalize_date(period_match.group(2)),
        ]

    date_patterns = [
        r"\b[A-Za-z]+\s+\d{1,2},\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]

    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text))

    return [normalize_date(d) for d in dates]


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