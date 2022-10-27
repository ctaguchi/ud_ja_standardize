import pykakasi
import sys

filename = sys.argv[1]
kks = pykakasi.kakasi()

class Romaji:
    def read(self, filename: str) -> list:
        with open(filename, "r") as f:
            lines = f.readlines()
        return lines

    def extract(self, lines: list) -> list:
        """
        Extract lines (tokens) that are to be romanized.
        i.e., metadata lines starting with # are stripped.
        """
        sents = []
        tokens = []
        for l in lines:
            if l.startswith("#"):
                continue
            elif l == "\n":
                sents.append(tokens)
                tokens = [] # re-initialization
            else:
                row = l.split("\t")
                elems = {"ID": row[0],
                        "FORM": row[1],
                        "LEMMA": row[2],
                        "UPOS": row[3],
                        "XPOS": row[4],
                        "FEATS": [],
                        "HEAD": row[6],
                        "DEPREL": row[7],
                        "DEPS": row[8],
                        "MISC": row[9],
                        "COMBINED": False,
                        "reduced_ID": row[0] # init
                        }
                tokens.append(elems)
        return sents

    def romanize(self, token: str) -> str:
        """
        Romanize a token from kana/kanji to romaji.
        """
        romanized = kks.convert(token)
        romanized = [r["kunrei"] for r in romanized]
        romanized = "".join(romanized)
        return romanized
    
    def conversion(self, elems: list) -> list:
        form = elems["FORM"]
        lemma = elems["LEMMA"]
        misc = elems["MISC"].split("|")
        form_romaji = self.romanize(form)
        form_translit = "FORMTranslit=" + form_romaji
        lemma_romaji = self.romanize(lemma)
        lemma_translit = "LEMMATranslit=" + lemma_romaji
        misc += [form_translit, lemma_translit]
        misc.sort()
        misc = "|".join(misc) 
        elems["MISC"] = misc # for "__main__"
        return misc # for using a package

if __name__ == "__main__":
    romaji = Romaji()
    lines = romaji.read(filename)
    sents = romaji.extract(lines)
    for s in sents:
        for elems in s:
            romaji.conversion(elems)
    romaji.conversion(sents)
    for i in range(10):
        print(sents[i])