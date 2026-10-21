import unittest

from backend.app.turkish_normalizer import int_to_words, normalize_turkish, ordinal_words


class NumberWordsTest(unittest.TestCase):
    def test_cardinals(self):
        cases = {0: "sıfır", 1: "bir", 10: "on", 100: "yüz", 101: "yüz bir", 700: "yedi yüz",
                 1000: "bin", 1001: "bin bir", 2030: "iki bin otuz", 21_000: "yirmi bir bin",
                 1_000_000: "bir milyon", 2_500_000_000: "iki milyar beş yüz milyon"}
        for n, words in cases.items():
            self.assertEqual(int_to_words(n), words, n)

    def test_ordinals(self):
        for n, words in {1: "birinci", 3: "üçüncü", 4: "dördüncü", 6: "altıncı", 9: "dokuzuncu",
                         10: "onuncu", 40: "kırkıncı", 21: "yirmi birinci", 100: "yüzüncü"}.items():
            self.assertEqual(ordinal_words(n), words, n)


class NormalizeTurkishTest(unittest.TestCase):
    def check(self, text, expected):
        self.assertEqual(normalize_turkish(text), expected)

    def test_percent_and_suffix(self):
        self.check("Tüketim %50 arttı.", "Tüketim yüzde elli arttı.")
        self.check("%50'si gitti, %2,5 kaldı.", "yüzde ellisi gitti, yüzde iki virgül beş kaldı.")

    def test_numbers_with_suffix_and_thousands(self):
        self.check("2030'da 700 çip.", "iki bin otuzda yedi yüz çip.")
        self.check("1.250 kişi", "bin iki yüz elli kişi")
        self.check("21'inci yüzyıl", "yirmi birinci yüzyıl")

    def test_ordinal_before_lowercase_word(self):
        self.check("Olay 3. gün oldu.", "Olay üçüncü gün oldu.")

    def test_dates_times_money_units(self):
        self.check("14.10.2026", "on dört ekim iki bin yirmi altı")
        self.check("saat 14:30'da", "saat on dört otuzda")
        self.check("saat 09.05'te", "saat dokuz sıfır beşte")
        self.check("1.250,50 ₺", "bin iki yüz elli lira elli kuruş")
        self.check("10 km'lik yol", "on kilometrelik yol")

    def test_religious_and_common_abbreviations(self):
        self.check("Hz. Muhammed (s.a.v.) dedi", "Hazreti Muhammed (sallallahu aleyhi ve sellem) dedi")
        self.check("elma, armut vb. meyveler", "elma, armut ve benzeri meyveler")

    def test_acronyms(self):
        self.check("ABD'de", "abedede")
        self.check("TBMM toplandı", "tebememe toplandı")
        self.check("NATO ve ASELSAN", "NATO ve ASELSAN")

    def test_dotted_and_dotless_capital_i(self):
        # Emphasised words stay words; capital I/İ become ı/i before Python lowercasing.
        self.check("IŞIK İnsan Irmak", "ıŞıK insan ırmak")
        self.assertEqual(normalize_turkish("IŞIK").lower(), "ışık")

    def test_plain_text_unchanged(self):
        text = "Bir zamanlar uzak bir şehirde yaşlı bir adam vardı. Türkiye'nin kalbinde."
        self.check(text, text)


if __name__ == "__main__":
    unittest.main()
