"""Turkish text normalisation before synthesis.

The Chatterbox grapheme tokenizer reads characters as they are written: digits, symbols and
acronyms are not verbalised, and Python's ``str.lower()`` turns ``I`` into ``i`` instead of
``ı``. This module rewrites text into speakable Turkish words.
"""
import re

_ONES = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
_SCALES = [(10**12, "trilyon"), (10**9, "milyar"), (10**6, "milyon"), (1000, "bin")]
_MONTHS = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos",
           "eylül", "ekim", "kasım", "aralık"]

# Ordinal suffix by the last word of the cardinal (vowel harmony).
_ORDINAL_SUFFIX = {
    "bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü", "beş": "beşinci",
    "altı": "altıncı", "yedi": "yedinci", "sekiz": "sekizinci", "dokuz": "dokuzuncu",
    "on": "onuncu", "yirmi": "yirminci", "otuz": "otuzuncu", "kırk": "kırkıncı", "elli": "ellinci",
    "altmış": "altmışıncı", "yetmiş": "yetmişinci", "seksen": "sekseninci", "doksan": "doksanıncı",
    "yüz": "yüzüncü", "bin": "bininci", "milyon": "milyonuncu", "milyar": "milyarıncı",
    "trilyon": "trilyonuncu", "sıfır": "sıfırıncı",
}

_ABBREVIATIONS = {
    "s.a.v.": "sallallahu aleyhi ve sellem", "a.s.": "aleyhisselam", "r.a.": "radıyallahu anh",
    "c.c.": "celle celâlühü", "k.s.": "kuddise sirruh", "Hz.": "Hazreti", "Dr.": "Doktor",
    "Prof.": "Profesör", "Doç.": "Doçent", "Av.": "Avukat", "vb.": "ve benzeri", "vs.": "vesaire",
    "örn.": "örneğin", "bkz.": "bakınız", "yy.": "yüzyıl", "No.": "numara",
}

_UNITS = {"km": "kilometre", "kg": "kilogram", "cm": "santimetre", "mm": "milimetre",
          "m": "metre", "lt": "litre", "ml": "mililitre", "gr": "gram"}
_CURRENCY = {"₺": "lira", "TL": "lira", "$": "dolar", "€": "avro"}

# Acronyms read as words, and acronyms spelled letter by letter despite containing vowels.
_WORD_ACRONYMS = {"NATO", "NASA", "UNESCO", "ASELSAN", "TÜBİTAK", "TOKİ", "ÖSYM", "TÜİK", "BOTAŞ",
                  "HAVELSAN", "ROKETSAN", "TUSAŞ", "AFAD", "İSKİ", "OPEC", "YÖK", "ODTÜ", "İTÜ",
                  "İYİ", "DEVA"}
_SPELL_ACRONYMS = {"ABD", "AB", "BM", "AİHM", "AİHS", "AKP", "AÜ", "AVM", "İBB", "ABB"}
_LETTER_NAMES = {
    "A": "a", "B": "be", "C": "ce", "Ç": "çe", "D": "de", "E": "e", "F": "fe", "G": "ge",
    "Ğ": "yumuşak ge", "H": "ha", "I": "ı", "İ": "i", "J": "je", "K": "ka", "L": "le", "M": "me",
    "N": "ne", "O": "o", "Ö": "ö", "P": "pe", "Q": "kü", "R": "re", "S": "se", "Ş": "şe", "T": "te",
    "U": "u", "Ü": "ü", "V": "ve", "W": "ve", "X": "iks", "Y": "ye", "Z": "ze",
}
_VOWELS = set("AEIİOÖUÜ")

_SUFFIX = r"(?:['’]([a-zçğıöşüâîû]+))?"
_NUMBER = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?"


def _under_thousand(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    tens, ones = divmod(rest, 10)
    parts = []
    if hundreds:
        parts.append("yüz" if hundreds == 1 else f"{_ONES[hundreds]} yüz")
    if tens:
        parts.append(_TENS[tens])
    if ones:
        parts.append(_ONES[ones])
    return " ".join(parts)


def int_to_words(n: int) -> str:
    if n == 0:
        return "sıfır"
    if n < 0:
        return f"eksi {int_to_words(-n)}"
    parts = []
    for value, name in _SCALES:
        count, n = divmod(n, value)
        if count:
            parts.append(name if (count == 1 and value == 1000) else f"{int_to_words(count)} {name}")
    if n:
        parts.append(_under_thousand(n))
    return " ".join(parts)


def _fraction_words(digits: str) -> str:
    leading = len(digits) - len(digits.lstrip("0"))
    rest = digits.lstrip("0")
    return " ".join(["sıfır"] * leading + ([int_to_words(int(rest))] if rest else []))


def number_to_words(integer: str, fraction: str | None = None) -> str:
    words = int_to_words(int(integer.replace(".", "")))
    return f"{words} virgül {_fraction_words(fraction)}" if fraction else words


def ordinal_words(n: int) -> str:
    words = int_to_words(n).split(" ")
    words[-1] = _ORDINAL_SUFFIX[words[-1]]
    return " ".join(words)


def _attach(words: str, suffix: str | None) -> str:
    return f"{words}{suffix}" if suffix else words


def _replace_abbreviations(text: str) -> str:
    for abbr, full in _ABBREVIATIONS.items():
        text = re.sub(rf"(?<![\w.]){re.escape(abbr)}", full, text)
    return text


def _replace_dates_and_times(text: str) -> str:
    def date(m: re.Match) -> str:
        day, month, year = int(m[1]), int(m[2]), m[3]
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return m[0]
        return _attach(f"{int_to_words(day)} {_MONTHS[month - 1]} {int_to_words(int(year))}", m[4])

    def clock(m: re.Match) -> str:
        hour, minute = int(m[1]), int(m[2])
        if hour > 24 or minute > 59:
            return m[0]
        minute_words = "" if minute == 0 else (" sıfır " if minute < 10 else " ") + int_to_words(minute)
        words = int_to_words(hour) + minute_words
        return _attach(words, m[3])

    text = re.sub(rf"\b(\d{{1,2}})\.(\d{{1,2}})\.(\d{{4}})\b{_SUFFIX}", date, text)
    text = re.sub(rf"\b(\d{{1,2}}):(\d{{2}})\b{_SUFFIX}", clock, text)
    # "saat 14.30" — Turkish often writes times with a dot
    return re.sub(rf"(?<=[Ss]aat )(\d{{1,2}})\.(\d{{2}})\b{_SUFFIX}", clock, text)


def _replace_money_percent_units(text: str) -> str:
    def money(m: re.Match) -> str:
        lira = number_to_words(m["int"])
        sub = m["frac"]
        unit = _CURRENCY[m["cur"]]
        if sub and unit == "lira" and int(sub):
            return _attach(f"{lira} lira {int_to_words(int(sub.ljust(2, '0')[:2]))} kuruş", m["suf"])
        return _attach(f"{number_to_words(m['int'], sub)} {unit}", m["suf"])

    cur = r"(?P<cur>₺|TL|\$|€)"
    num = r"(?P<int>\d{1,3}(?:\.\d{3})+|\d+)(?:,(?P<frac>\d+))?"
    suf = r"(?:['’](?P<suf>[a-zçğıöşüâîû]+))?"
    text = re.sub(rf"{num}\s?{cur}{suf}", money, text)
    text = re.sub(rf"{cur}\s?{num}{suf}", money, text)

    def percent(m: re.Match) -> str:
        return _attach(f"yüzde {number_to_words(m[1], m[2])}", m[3])

    text = re.sub(rf"%\s?{_NUMBER}{_SUFFIX}", percent, text)
    text = re.sub(rf"{_NUMBER}\s?%{_SUFFIX}", percent, text)

    def unit(m: re.Match) -> str:
        return _attach(f"{number_to_words(m[1], m[2])} {_UNITS[m[3]]}", m[4])

    units = "|".join(sorted(_UNITS, key=len, reverse=True))
    return re.sub(rf"{_NUMBER}\s?({units})\b{_SUFFIX}", unit, text)


def _replace_numbers(text: str) -> str:
    # Ordinals: "3. gün" (number + period + lowercase word)
    text = re.sub(r"\b(\d+)\.(?=\s+[a-zçğıöşü])", lambda m: ordinal_words(int(m[1])), text)
    return re.sub(rf"(?<![\w]){_NUMBER}{_SUFFIX}", lambda m: _attach(number_to_words(m[1], m[2]), m[3]), text)


def _replace_acronyms(text: str) -> str:
    def acronym(m: re.Match) -> str:
        word, suffix = m[1], m[2]
        if word in _WORD_ACRONYMS:
            return _attach(word, suffix)
        if word in _SPELL_ACRONYMS or not (set(word) & _VOWELS):
            # Letter names joined into one word ("abede") flow more naturally than "a be de".
            return _attach("".join(_LETTER_NAMES.get(ch, ch) for ch in word), suffix)
        return m[0]  # emphasised word such as "IŞIK" or "SEN"

    return re.sub(r"\b([A-ZÇĞIİÖŞÜQWX]{2,8})\b" + _SUFFIX, acronym, text)


def _fix_dotted_i(text: str) -> str:
    # Turkish casing: the tokenizer lowercases with str.lower(), which maps I→i and İ→i̇.
    return text.replace("I", "ı").replace("İ", "i")


def normalize_turkish(text: str) -> str:
    text = _replace_abbreviations(text)
    text = _replace_dates_and_times(text)
    text = _replace_money_percent_units(text)
    text = _replace_numbers(text)
    text = _replace_acronyms(text)
    return _fix_dotted_i(text)
