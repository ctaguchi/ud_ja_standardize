# import convert
import pytest

print("Reading tested.conllu ...")
with open("tested.conllu", "r") as f:
    lines = f.readlines()

sents = [[]]
for l in lines:
    if l.startswith("#"):
        continue
    i = 0
    if l[0].isdigit():
        sents[i].append(l)
    if l == "\n" and l != lines[-1]:
        sents.append([])
        i += 1
print("File read complete!")

def test_head():
    print(sents)
    for i, s in enumerate(sents):
        heads = []
        ids = ["0"]
        for w in s:
            w = w.split("\t")
            print(w)
            head = w[6]
            idx = w[0]
            heads.append(head)
            ids.append(idx)
        for j in range(len(heads)):
            assert heads[j] in ids, "Error in sentence {} index {}".format(i, j) 