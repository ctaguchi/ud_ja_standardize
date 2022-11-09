import sys

def token_count(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
        c = 0 
        for l in lines:
            if l.startswith("#"):
                continue
            elif l == "\n":
                continue
            elif l[0].isdigit():
                c += 1
            else:
                print("Unknown line")
    return c

if __name__ == "__main__":
    filename = sys.argv[1]
    c = token_count(filename)
    print("# of Tokens: {}".format(c))