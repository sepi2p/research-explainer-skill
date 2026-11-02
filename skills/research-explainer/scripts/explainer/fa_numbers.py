"""Persian for the narrator: numbers as words and Latin names as they are said. The caption keeps the digits.
Project-specific pronunciations come from project.json -> "pronounce": {"fa": {"CIFAR-10": "سیفار ده"}}."""
import re

ONES = ["صفر", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه", "ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده",
        "شانزده", "هفده", "هجده", "نوزده"]
TENS = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
HUND = ["", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
FRAC = {1: "دهم", 2: "صدم", 3: "هزارم"}


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " و " + ONES[n % 10])
    if n < 1000:
        return HUND[n // 100] + ("" if n % 100 == 0 else " و " + words(n % 100))
    if n < 1_000_000:
        th = "هزار" if n // 1000 == 1 else words(n // 1000) + " هزار"
        return th + ("" if n % 1000 == 0 else " و " + words(n % 1000))
    if n < 1_000_000_000:
        m = words(n // 1_000_000) + " میلیون"
        return m + ("" if n % 1_000_000 == 0 else " و " + words(n % 1_000_000))
    raise ValueError(n)


def number(tok: str) -> str:
    t = tok.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace("٬", "").replace(",", "").replace("٫", ".")
    if "." in t:
        a, b = t.split(".")
        return words(int(a)) + " ممیز " + words(int(b))
    return words(int(t))


def spoken(text: str, names=None) -> str:
    for k, v in sorted((names or {}).items(), key=lambda kv: -len(kv[0])):   # longest first: "GWAD+" before "GWAD"
        text = text.replace(k, v)
    text = re.sub(r"[0-9۰-۹][0-9۰-۹٬,]*(?:[٫.][0-9۰-۹]+)?", lambda m: number(m.group(0)), text)
    return text.replace("٪", " درصد").replace("%", " درصد")


if __name__ == "__main__":
    for s in ["۵۱۱ پرسش", "۷٫۱ به ۸٫۴", "۳٬۰۷۲ مقدار", "۲۰۰ پرسش از ۵۱۱", "1,250,000"]:
        print(s, "->", spoken(s))
