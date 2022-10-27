import sys

filename = sys.argv[1]

with open(filename, "r") as f:
    lines = f.readlines()
    count = 0 
    for l in lines:
        if l.startswith("#"):
            continue
        elif l == "\n":
            continue
        elif l[0].isdigit():
            count += 1
        else:
            print("Unknown line")

print("# of Tokens: {}".format(count))