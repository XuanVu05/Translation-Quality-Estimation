from pathlib import Path

path = Path("mqm_newstest2020_ende.tsv")
lines = path.read_text(encoding="utf-8-sig").splitlines()

print("HEADER:")
print(repr(lines[0]))

matches = 0
for line_no, line in enumerate(lines[1:], start=2):
    if "Huoshan_Translate.832" not in line:
        continue
    if "abcnews.363905" not in line:
        continue

    fields = line.split("\t")

    if len(fields) >= 4 and fields[3] == "1129":
        print(f"\nLINE {line_no}, fields={len(fields)}:")
        print(repr(line))
        matches += 1

print("\nTotal matching raw lines:", matches)
