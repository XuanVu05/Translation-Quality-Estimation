from pathlib import Path

folder = Path("original_outputs")

for path in sorted(folder.glob("*.txt")):
    print("\n" + "=" * 80)
    print("FILE:", path.name)

    with path.open("r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    print("Physical lines:", len(lines))
    for i, line in enumerate(lines[:3], start=1):
        print(f"Line {i}: {line[:300]!r}")
