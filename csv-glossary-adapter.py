from csv import reader as csv_reader

fixed = []

with open("resources/Astronomy.csv", "r") as fh:
    r = csv_reader(fh)

    for row in r:
        fixed += ["=:%s:= %s" % (row[0], row[1])]

with open("Astronomy.glossary", "w") as fh:
    for line in fixed:
        fh.write(line)
        fh.write("\n")

