import spacy
import sys
import romaji

file = sys.argv[1]
assert file.endswith(".conllu"), "Input file needs to be in the .conllu format."
newfile = sys.argv[2]
assert newfile.endswith(".conllu"), "Output file needs to be in the .conllu format."
stage = sys.argv[3]
assert stage in ["1", "2", "3", "4"], "Stage must be one of 1, 2, 3, and 4."
print("Loading the data...")

casedic = {
        # "は": ["Case=Top"], # No!
           "が": ["Case=Nom"],
           "の": ["Case=Gen"],
           "に": ["Case=Dat"],
           "から": ["Case=Abl"],
           "で": ["Case=Loc"],
           "へ": ["Case=Lat"],
           "を": ["Case=Acc"],
           "と": ["Case=Com"], # "と" in "となる" is probably a SCONJ complementizer
        #    "も": "Case=Top", # difference with "は"??
           }

morphdic = {# 助動詞
            "れる": ["Voice=Pass"],
            "られる": ["Mood=Pot|Voice=Pass"], # need annotator's decision
            "せる": ["Voice=Cau"],
            "させる": ["Voice=Cau"],
            "ない": ["Polarity=Neg"],
            "ず": ["Polarity=Neg"],
            "う": ["Mood=Opt"], # aka hortative
            "よう": ["Mood=Opt"], # conventional UD-ja does not tokenize this
            "まい": ["Mood=Opt", "Polarity=Neg"],
            "たい": ["Mood=Des"], # desiderative; entry exists in UD doc
            "たがる": ["Mood=Des"],
            "た": ["Tense=Past", "VerbForm=Fin"],
            "ます": ["Polite=Form"], # entry exists in UD doc
            "そうだ": ["Aspect=Prosp|Evident=Nfh"], # about to... (shisouda) or hearsay (surusouda)
            "やがる": ["Polite=Impolite"], # not in UD
            "らしい": ["Evident=Nfh"],
            "べし": ["Mood=Nec"], # necessitative,
            "べきだ": ["Mood=Nec"],
            "ようだ": ["Evident=Fh"],
            "だ": ["Tense=Pres"],
            "です": ["Polite=Form"],
            "てる": ["Aspect=Progr"],
            "ながら": ["Aspect=Progr", "VerbForm=Conv"],
            # 文語助動詞
            "り": ["VerbForm=Part"], # おける
            "しめる": ["Voice=Cau"],
            # 接続助詞
            "て": ["VerbForm=Conv"],
            "で": ["VerbForm=Conv"],
            "ば": ["Mood=Cnd"],
            "が": [None], # "しないが", "だが"
            "な": ["Tense=Pres", "VerbForm=Part"],
            "の": ["VerbForm=Vnoun"], # 準体助詞「の」
            "だろう": ["Mood=Irr"], # irrealis; speculation
            "ている": ["Aspect=Prog"],
            "たり": ["VerbForm=Exem"] # not in UD
            }

# 補助名詞
auxnoun = ["事"]

# exceptions (including mistakes in UD)
exceptions = [
            "蛹", #244
            "珍味", #244
                ]

def is_udan(elems: list) -> bool:
    udan = ["う", "く", "ぐ", "す", "ず", "つ", "づ", "ぬ", "ふ", "ぶ",
            "ぶ", "む", "ゆ", "る"]
    verb = elems["FORM"]
    if verb[-1] in udan and not is_opt(elems):
        return True
    else:
        return False

def is_inf(elems: list) -> bool:
    idan = ["い", "き", "ぎ", "し", "じ", "ち", "ぢ", "に", "ひ", "び",
            "み", "り"]
    edan = ["え", "け", "げ", "せ", "ぜ", "て", "で", "ね", "へ", "べ",
            "め", "れ"]
    verb = elems["FORM"]
    if "下一段" in elems["XPOS"].split("-"):
        if verb[-1] in edan:
            return True
        else:
            return False
    else:
        if verb[-1] in idan:
            return True
        else:
            return False

def is_past(verb: str) -> bool:
    past_suf = ["た", "だ"]
    if verb[-1] in past_suf:
        return True
    else:
        return False

def is_opt(elems: list) -> bool:
    verb = elems["FORM"]
    xpos = elems["XPOS"].split("-")
    opt = [("カ行", "こう"),
            ("ガ行", "ごう"),
            ("サ行", "そう"),
            ("タ行", "とう"),
            ("ナ行", "のう"),
            ("バ行", "ぼう"),
            ("マ行", "もう"),
            ("ラ行", "ろう"),
            ("ワ行", "おう")]
    if "下一段" in xpos or "上一段" in xpos:
        if verb[-2:] == "よう":
            return True
        else:
            return False
    elif "五段" in xpos:
        for o, p in opt:
            if o in xpos and verb[-2:] == p:
                return True
            # else:
            #     return False
    elif "サ行変格" in xpos:
        if verb == "しよう":
            return True
        else:
            return False
    elif "カ行変格" in xpos:
        if verb[-2:] == "こう":
            return True
        else:
            return False
    else:
        return False

nlp = spacy.load("ja_ginza")

def read(file):
    """
    Read the specified file (.conllu) and returns its sentences
    in the format of list
    """
    with open(file, "r") as f:
        lines = f.readlines() # list of all lines
        sents = []
        for i, l in enumerate(lines):
            if l.startswith("# newdoc id ="):
                lines[i] = lines[i][:-2] + "_converted\n"
                sents.append([lines[i]])
            if l.startswith("# sent_id ="):
                lines[i] = lines[i][:-2] + "_converted\n"
                if not lines[i-1].startswith("# newdoc id ="):
                    # newdoc line does not exist
                    sents.append([""])
                sents[-1].append(lines[i])
            if l.startswith("# text ="):
                sents[-1].append(l)
            if l.startswith("# text_en ="):
                sents[-1].append(l)
            if l[0].isdigit():
                row = l.split("\t")
                # ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC
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
                sents[-1].append(elems)
            if not l:
                # the line is blank ""
                continue
    return sents

class Combine:
    def __init__(self, table):
        self.table = table

    def compound_noun(self, i, elems: list):
        if elems["DEPREL"] == "compound" and elems["LEMMA"]not in (auxnoun + exceptions) and elems["XPOS"] not in ["接尾辞-名詞的-一般", "接尾辞-形状詞的"]:
            end = int(elems["HEAD"])
            for k in range(i+1, end):
                elems["FORM"] += self.table[k]["FORM"]
                elems["LEMMA"] += self.table[k]["LEMMA"]
                self.table[k]["COMBINED"] = True
            elems["UPOS"] = self.table[end-1]["UPOS"]
            elems["DEPREL"] = self.table[end-1]["DEPREL"]
            elems["HEAD"] = self.table[end-1]["HEAD"]
            elems["XPOS"] = self.table[end-1]["XPOS"]


def convert(sents):
    for n, sent in enumerate(sents):
        sentence = sent[2].split(" = ")[1]
        print("Processing sentence No. {}: {}".format(n+1, sentence))
        table = sent[4:]
        for i, elems in enumerate(table):
            if elems["COMBINED"] == True:
                continue
            prev = table[i-1]
            if i < len(table) - 1:
                next = table[i+1]
            combine = Combine(table)
            combine.compound_noun(i, elems)
            # compound nouns alternative
            # if elems["DEPREL"] == "compound" and elems["LEMMA"] not in (auxnoun + exceptions) and elems["XPOS"] not in ["接尾辞-名詞的-一般", "接尾辞-形状詞的"]:
            #     end = int(elems["HEAD"])
            #     for k in range(i+1, end):
            #         elems["FORM"] += table[k]["FORM"]
            #         elems["LEMMA"] += table[k]["LEMMA"]
            #         table[k]["COMBINED"] = True
            #     elems["UPOS"] = table[end-1]["UPOS"]
            #     elems["DEPREL"] = table[end-1]["DEPREL"]
            #     elems["HEAD"] = table[end-1]["HEAD"]
            #     elems["XPOS"] = table[end-1]["XPOS"]

            # compound nouns
            # if elems["UPOS"] in ["NOUN", "PROPN", "ADJ", "SYM", "NUM"] and elems["DEPREL"] == "compound" and int(elems["HEAD"]) > int(elems["ID"]):
            #     end = int(elems["HEAD"])  # compound-final noun
            #     if i > 0:
            #         if prev["DEPREL"] != "compound":
            #             if next["DEPREL"] != "compound":
            #                 # it's a two-token compound
            #                 elems["FORM"] += next["FORM"]
            #                 elems["LEMMA"] += next["LEMMA"]
            #                 elems["DEPREL"] = next["DEPREL"]
            #                 elems["UPOS"] = next["UPOS"]
            #                 elems["XPOS"] = next["XPOS"]
            #                 elems["HEAD"] = next["HEAD"]
            #                 next["COMBINED"] = True
            #                 next["HEAD"] = elems["ID"]
            #                 continue
            #             else:
            #                 # it's the compound-initial noun, so don't combine
            #                 continue
            #     else:
            #         # it's the first token
            #         continue
            #     j = 1
            #     while table[i-j]["COMBINED"] == True:
            #         j += 1
            #     table[i-j]["FORM"] += elems["FORM"]
            #     table[i-j]["LEMMA"] += elems["LEMMA"]
            #     elems["COMBINED"] = True
            #     elems["HEAD"] = table[i-j]["ID"]
            #     # combine the compound-final noun
            #     if i == end - 2:
            #         table[i-j]["FORM"] += table[i+1]["FORM"]
            #         table[i-j]["LEMMA"] += table[i+1]["LEMMA"]
            #         table[i-j]["DEPREL"] = table[i+1]["DEPREL"]
            #         table[i-j]["UPOS"] = table[i+1]["UPOS"]
            #         table[i-j]["XPOS"] = table[i+1]["XPOS"]
            #         table[i-j]["HEAD"] = table[i+1]["HEAD"]
            #         table[i+1]["COMBINED"] = True
            #         table[i+1]["HEAD"] = table[i-j]["ID"]
            
            # suffix
            if elems["XPOS"] == "接尾辞-名詞的-一般":
                j = 1
                while table[i-j]["COMBINED"] == True:
                    j += 1
                table[i-j]["FORM"] += elems["FORM"]
                table[i-j]["LEMMA"] += elems["LEMMA"]
                table[i-j]["UPOS"] = "NOUN"
                table[i-j]["DEPREL"] = elems["DEPREL"]
                table[i-j]["HEAD"] = elems["HEAD"]
                elems["COMBINED"] = True
            if elems["XPOS"] == "接尾辞-形状詞的":
                j = 1
                while table[i-j]["COMBINED"] == True:
                    j += 1
                table[i-j]["FORM"] += elems["FORM"]
                table[i-j]["LEMMA"] += elems["LEMMA"]
                table[i-j]["UPOS"] = "ADJ"
                table[i-j]["DEPREL"] = "amod"
                # table[i-j]["HEAD"] = elems["HEAD"]
                elems["COMBINED"] = True

            # adp_combine
            if elems["UPOS"] == "ADP":
                if prev["UPOS"] == "PUNCT":
                    # don't combine when e.g., "」と"
                    if elems["FORM"] == "と":
                        elems["DEPREL"] = "mark"
                    continue
                if prev["UPOS"] in ["VERB", "AUX"] and elems["FORM"] == "と":
                    # don't combine quotative と (it is a complementizer); change the DEPREL to mark
                    elems["DEPREL"] = "mark"
                    continue
                elif elems["XPOS"] == "助詞-係助詞":
                    continue
                elif elems["XPOS"] == "助詞-副助詞":
                    continue
                else:
                    # prev["FORM"] += elems["FORM"]
                    try:
                        case = casedic[elems["FORM"]]
                    except:
                        print("There is no case for {} in casedic.".format(elems["FORM"]))
                    j = 1
                    while table[i-j]["COMBINED"] == True:
                        j += 1
                    table[i-j]["FEATS"] += case
                    table[i-j]["FORM"] += elems["FORM"]
                    # prev["FEATS"] += [case]
                    elems["COMBINED"] = True

            # aux_combine
            elif elems["UPOS"] == "AUX":
                # Light verb construction
                if (elems["XPOS"] == "動詞-非自立可能-サ行変格" or elems["XPOS"] == "動詞-非自立可能-上一段-カ行") and prev["XPOS"] in ["名詞-普通名詞-サ変可能", "名詞-普通名詞-サ変形状詞可能"]:
                    elems["UPOS"] = "VERB"
                    elems["DEPREL"] = prev["DEPREL"]
                    elems["HEAD"], prev["HEAD"] = prev["HEAD"], elems["ID"]
                    j = 1
                    while table[i-j]["COMBINED"] == True:
                        j += 1
                    table[i-j]["UPOS"] = "NOUN"
                    table[i-j]["DEPREL"] = "compound:lvc"
                    # change HEAD of any elems modifying lvc noun
                    for word in table:
                        if word["HEAD"] == prev["ID"]:
                            word["HEAD"] = elems["ID"]
                # darou
                if elems["FORM"] == "だろう":
                    elems["FEATS"] += morphdic[elems["FORM"]]
                if elems["FORM"] == "で":
                    elems["FEATS"] += ["VerbForm=Inf"] # renyookei of copula
                # Inflection
                elif elems["XPOS"].startswith("助動詞"):
                    try:
                        feat = morphdic[elems["LEMMA"]]
                    except:
                        print("There is no feature for {} in morphdic (sent {}).".format(elems["LEMMA"], n))
                    if elems["XPOS"] == "助動詞-助動詞-ダ" and (prev["UPOS"] in ["NOUN", "SCONJ", "VERB", "ADJ"]) and elems["FORM"] != "な":
                        if int(stage) == 4:
                            feat = morphdic[elems["FORM"]]
                            print(feat)
                            elems["DEPREL"] = "cop"
                        else:
                            continue
                    if elems["XPOS"] == "助動詞-文語助動詞-ナリ-断定":
                        # early modern japanese copula
                        continue
                    # 形容動詞（形状詞）〜な
                    elif elems["XPOS"] == "助動詞-助動詞-ダ" and elems["FORM"] == "な":
                        feat = morphdic[elems["FORM"]]
                    else:
                        feat = morphdic[elems["LEMMA"]]
                        # annotator's decision
                        if feat == ["Mood=Pot|Voice=Pass"]:
                            print("Specify the feature for the sentence: {}".format(sentence))
                            print("Word: {}{}".format(prev["FORM"], elems["FORM"]))
                            while True:
                                rareru = input("Type m if Mood=Pot or v if Voice=Pass.")
                                if rareru == "m":
                                    feat = ["Mood=Pot"]
                                    break
                                elif rareru == "v":
                                    feat = ["Voice=Pass"]
                                    break
                                else:
                                    print("Input is an invalid character. Try again.")
                        if feat == ["Aspect=Prosp|Evident=Nfh"]:
                            print("Specify the feature for the sentence: {}".format(sentence))
                            souda = input("Type a if Aspect=Prosp or e if Evident=Nfh.")
                            if souda == "a":
                                feat = ["Aspect=Prosp"]
                            elif souda == "e":
                                feat = ["Evident=Nfh"]
                            else:
                                print("Input is an invalid character.")
                    # ない、ん
                    if elems["FORM"] == "ない" and elems["XPOS"] == "助動詞-助動詞-ナイ" or elems["FORM"] == "ん" and elems["XPOS"] == "助動詞-助動詞-ヌ":
                        feat += ["Tense=Pres", "VerbForm=Fin"]
                    # 文語助動詞
                    if elems["LEMMA"] == "べし":
                        feat = ["Mood=Nec"]
                        if elems["FORM"] == "べき":
                            feat += ["VerbForm=Part"]
                            if "VerbForm=Fin" in prev["FEATS"]:
                                prev["FEATS"].remove("VerbForm=Fin")
                    elems["COMBINED"] = True
                    j = 1
                    while table[i-j]["COMBINED"] == True:
                        j += 1
                    table[i-j]["FEATS"] += list(set(feat))
                    table[i-j]["FORM"] += elems["FORM"]
                
            # SCONJ
            elif elems["UPOS"] == "SCONJ":
                try:
                    feat = morphdic[elems["LEMMA"]]
                except:
                    print("There is no feature for {} in morphdic (sent {}).".format(elems["LEMMA"], n))
                indep_sconj = ["が", "せよ"]
                if elems["FORM"] in indep_sconj:
                    # It can be an independent SCONJ 
                    continue
                elems["COMBINED"] = True
                j = 1
                while table[i-j]["COMBINED"] == True:
                    j += 1
                table[i-j]["FEATS"] += feat
                table[i-j]["FORM"] += elems["FORM"]
                # prev["FEATS"] += [morphdic[elems["FORM"]]]
            
            # VERB
            # if (elems["UPOS"] == "VERB" or elems["XPOS"] == "助動詞-助動詞-タ") and next["FORM"] == "。":
            #     # processing "shuushikei" (sentence-final verb form)
            #     j = 0 
            #     while table[i-j]["COMBINED"] == True:
            #         j += 1
            #     table[i-j]["FEATS"] += ["VerbForm=Fin"]
            if elems["UPOS"] in ["VERB", "AUX"]:
                # print(is_opt(elems))
                # optative/hortative
                if is_opt(elems):
                    elems["FEATS"] += ["Mood=Opt", "VerbForm=Fin"]
                elif is_udan(elems) and not [f for f in elems["FEATS"] if f.startswith("VerbForm=")]:
                    # shuushikei and rentaikei of verbs
                    j = 0
                    while table[i-j]["COMBINED"] == True:
                        j += 1
                    table[i-j]["FEATS"] += ["Tense=Pres", "VerbForm=Fin"]
                
                # elif is_opt(elems):
                #     elems["FEATS"] += ["Mood=Opt", "VerbForm=Fin"]


def reduce_id(sents):
    for sent in sents:
        table = sent[4:]
        count = 1
        for elems in table:
            if elems["COMBINED"] == False:
                elems["reduced_ID"] = count
                count += 1

def reduce_head(sents):
    for sent in sents:
        table = sent[4:]
        for elems in table:
            if elems["COMBINED"] == False:
                goal = table[int(elems["HEAD"]) - 1]
                while goal["COMBINED"] == True:
                    goal = table[int(goal["HEAD"]) - 1]
                elems["HEAD"] = goal["reduced_ID"]
            # make sure that the root verb has the head id 0
            if elems["DEPREL"] == "root":
                elems["HEAD"] = str(0)

def reduce_table(sents):
    for i in range(len(sents)):
        sents[i][4:] = [sents[i][j] for j in range(4, len(sents[i])) if sents[i][j]["COMBINED"] == False]

def verbform_check(sents):
    for sent in sents:
        whole_sent = sent[2].split(" = ")[1]
        table = sent[4:]
        for elems in table:
            if elems["UPOS"] == "VERB":
                if not [f for f in elems["FEATS"] if f.startswith("VerbForm") or f == "Mood=Cnd"]:
                    if is_inf(elems):
                        verbform = "VerbForm=Inf" # bare renyookei, tentative annotation
                    else:
                        # manual specification
                        print(whole_sent)
                        while True:
                            print("Specify the VerbForm for token {} in index {} (start with VerbForm=).".format(elems["FORM"], elems["ID"])) 
                            verbform = input()
                            if not verbform.startswith("VerbForm="):
                                print("Wrong format. Try again.")
                                continue
                            else:
                                break
                    elems["FEATS"] += [verbform]
                if "VerbForm=Fin" in elems["FEATS"] and not [f for f in elems["FEATS"] if f.startswith("Tense")] and not "Mood=Opt" in elems["FEATS"]:
                    print(whole_sent)
                    while True:
                        print("Specify the Tense for token {} in index {} (start with Tense=).".format(elems["FORM"], elems["ID"]))
                        tense = input()
                        if not tense.startswith("Tense="):
                            print("Wrong format. Try again.")
                            continue
                        else:
                            break
                    elems["FEATS"] += [tense]

def write(newfile, sents):
    romanize = romaji.Romaji()
    with open(newfile, "w") as f:
        for i, sent in enumerate(sents):
            # sent[0]: newdoc id
            # sent[1]: sent id
            # sent[2]: text
            # sent[3]: translation
            # sent[4]: elems
            if sent[0] != "":
                # starting with newdoc id
                f.write("{}".format(sent[0]))
            f.write("{}".format(sent[1]))
            f.write("{}".format(sent[2]))
            f.write("{}".format(sent[3]))
            for i, elems in enumerate(sent[4:]):
                print("Features: {}".format(elems["FEATS"]))
                # f.write("{}\t".format(elems["ID"])) # just for test
                f.write("{}\t".format(elems["reduced_ID"]))
                f.write("{}\t".format(elems["FORM"]))
                f.write("{}\t".format(elems["LEMMA"]))
                f.write("{}\t".format(elems["UPOS"]))
                f.write("{}\t".format(elems["XPOS"]))
                if len(elems["FEATS"]) == 0:
                    feats = "_"
                else:
                    feats = [f for f in elems["FEATS"] if f != None]
                    feats = "|".join(sorted(feats))
                f.write("{}\t".format(feats))
                f.write("{}\t".format(elems["HEAD"]))
                f.write("{}\t".format(elems["DEPREL"]))
                f.write("{}\t".format(elems["DEPS"]))
                # add romaji transliteration info for morphological complexity metrics
                misc = romanize.conversion(elems)
                # delete all the messy entries in MISC
                misc = elems["MISC"].split("|")
                misc = [m for m in misc if m.startswith("SpaceAfter=") or m.startswith("FORMTranslit=") or m.startswith("LEMMATranslit=")]
                misc = "|".join(misc)
                f.write("{}".format(misc))
                f.write("\n")
            f.write("\n")
    
if __name__ == "__main__":
    sents = read(file)
    convert(sents)
    reduce_id(sents)
    reduce_head(sents)
    reduce_table(sents)
    # verbform_check(sents) 
    write(newfile, sents)