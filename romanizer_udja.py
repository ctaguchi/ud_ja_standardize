import sys

from conllu import conllu_sentences

filename = sys.argv[1]
output = sys.argv[2]

def readfile(filename):
    sentences = []
    sentences.extend(conllu_sentences(filename))
    return sentences

def romanize(sentences):
    for sent in sentences:
        nodes = sent.nodes
        for i in range(1, len(nodes)):
            misc = nodes[i].misc
            misc_l = misc.split("|")
            form_romaji = [m for m in misc_l if m.startswith("FORMTranslit=")][0]
            form_romaji = form_romaji.split("=")[1]
            lemma_romaji = [m for m in misc_l if m.startswith("LEMMATranslit=")][0]
            lemma_romaji = lemma_romaji.split("=")[1]
            nodes[i].form = form_romaji
            nodes[i].lemma = lemma_romaji

def writefile(sentences, output):
    with open(output, "w") as f:
        for sent in sentences:
            f.write(str(sent))
            f.write("\n")

sentences = readfile(filename)
romanize(sentences) 
print(sentences[1])
print(sentences[1].nodes[1].form)
writefile(sentences, output)