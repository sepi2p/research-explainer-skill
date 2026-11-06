"""Spell English numbers as words (for comparing a script with its transcript): 1,536 -> one thousand five hundred
thirty six; 0.56, .56 and "zero point five six" -> point five six (a leading zero is optional when spoken);
99.98 -> ninety nine point nine eight. Digits only (no currency). Years are spelled like other numbers (both sides go
through the same function)."""
import re
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def words(n):
    n = int(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + words(n % 100))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div: return words(n // div) + " " + name + ("" if n % div == 0 else " " + words(n % div))
def spoken(s):
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)
    s = re.sub(r"(?<![\d.])0?\.(\d)", r"@\1", s)   # 0.58 and .58 read the same ("point five eight"), with or without "zero"
    s = re.sub(r"\bzero point\b", "point", s, flags=re.I)
    s = re.sub(r"@(\d+)", lambda m: " point " + " ".join(ONES[int(c)] for c in m.group(1)), s)
    s = re.sub(r"(\d+)\.(\d+)", lambda m: words(m.group(1)) + " point " + " ".join(ONES[int(c)] for c in m.group(2)), s)
    return re.sub(r"\d+", lambda m: " " + words(m.group()) + " ", s)
if __name__ == "__main__":
    for x in ["1,536", "0.56", ".56", "zero point five six", "99.98", "1970", "2,296", "612.40", "E42", "4471", "14 days"]: print(x, "->", spoken(x))
