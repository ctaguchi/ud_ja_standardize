from token_count import token_count

FILES = ["pud_tested_suw_1.conllu",
        "pud_tested_suw_2.conllu",
        "pud_tested_luw_1.conllu",
        "pud_tested_luw_2.conllu"]
    
with open("stats.txt", "w") as f:
    for file in FILES:
        c = token_count(file)
        f.write(file + "\t" + str(c) + "\n")