import unittest

from backend.app.text_splitter import prepare_chunks, split_chunks, split_sentences, split_text


class SplitSentencesTest(unittest.TestCase):
    def test_basic_turkish_sentences(self):
        text = "Bir zamanlar yaşlı bir adam vardı. Her sabah dua ederdi! Neden mi? Çünkü umut ışıktır."
        self.assertEqual(
            split_sentences(text),
            ["Bir zamanlar yaşlı bir adam vardı.", "Her sabah dua ederdi!", "Neden mi?", "Çünkü umut ışıktır."],
        )

    def test_abbreviations_and_ordinals_do_not_split(self):
        text = "Hz. Ömer bunu duydu. Olay 3. gün yaşandı. Dr. Ali geldi."
        self.assertEqual(split_sentences(text), ["Hz. Ömer bunu duydu.", "Olay 3. gün yaşandı.", "Dr. Ali geldi."])

    def test_paragraph_break_is_boundary_and_turkish_chars_kept(self):
        text = "Şükür ğ ı ö ü ç İ\n\nİkinci paragraf"
        self.assertEqual(split_sentences(text), ["Şükür ğ ı ö ü ç İ", "İkinci paragraf"])

    def test_ellipsis_before_lowercase_continues_sentence(self):
        self.assertEqual(split_sentences("Peki… neden bu kadar? Bitti… Sonra."),
                         ["Peki… neden bu kadar?", "Bitti…", "Sonra."])

    def test_quotes_after_punctuation(self):
        self.assertEqual(split_sentences("“Gel.” dedi. Gitti."), ["“Gel.”", "dedi.", "Gitti."])


class SplitTextTest(unittest.TestCase):
    def test_short_sentences_are_merged(self):
        chunks = split_text("Evet. Hayır. Bu cümle yeterince uzun bir cümledir.", max_chars=280, min_chars=20)
        self.assertEqual(chunks, ["Evet. Hayır. Bu cümle yeterince uzun bir cümledir."])

    def test_long_sentence_split_within_limit(self):
        sentence = ", ".join(["kelime kelime kelime"] * 40) + "."
        chunks = split_text(sentence, max_chars=100)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 100 for c in chunks))
        self.assertEqual(" ".join(chunks).replace(" ", ""), sentence.replace(" ", ""))

    def test_no_text_lost(self):
        text = "Bir. İki üç dört beş altı yedi. Sekiz dokuz on on bir on iki. Son."
        self.assertEqual(" ".join(split_text(text)), text)

    def test_empty(self):
        self.assertEqual(split_text("   \n\n "), [])

    def test_sentences_grouped_up_to_target(self):
        text = "Bir zamanlar yaşlı bir adam vardı. Her sabah dua ederdi. Bir gün çocuk sordu."
        self.assertEqual(split_text(text, target_chars=200), [text])
        self.assertEqual(len(split_text(text, target_chars=40)), 3)

    def test_break_after_ellipsis_with_longer_pause(self):
        chunks = split_chunks("Yapay zekânın geleceği kodla yazılmıyor… Elektrikle yazılıyor ve büyüyor.")
        self.assertEqual([c.text for c in chunks],
                         ["Yapay zekânın geleceği kodla yazılmıyor…", "Elektrikle yazılıyor ve büyüyor."])
        self.assertEqual(chunks[0].pause_factor, 1.6)

    def test_short_ellipsis_fragment_is_merged(self):
        chunks = split_text("Peki… neden bu kadar enerji harcanıyor?")
        self.assertEqual(chunks, ["Peki… neden bu kadar enerji harcanıyor?"])

    def test_paragraph_and_question_pauses(self):
        text = "Bu birinci paragrafın uzun cümlesidir?\n\nBu da ikinci paragrafın uzun cümlesidir."
        chunks = split_chunks(text)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].pause_factor, 2.0)
        q = split_chunks("Neden her sabah dua ediyorsun böyle? Çünkü umut ışıktır ve asla sönmez.", target_chars=40)
        self.assertEqual([c.pause_factor for c in q], [1.25, 1.0])

    def test_prepare_chunks_normalizes_first(self):
        self.assertEqual([c.text for c in prepare_chunks("ABD'de %50 arttı.")], ["abedede yüzde elli arttı."])


if __name__ == "__main__":
    unittest.main()
