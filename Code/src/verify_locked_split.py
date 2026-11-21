
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
WEEK10 = ROOT / "results" / "week10"

SOURCE_PATH = WEEK10 / "model_data" / "segments_with_fixed_splits.csv"
SNAPSHOT_PATH = WEEK10 / "locked_split" / "segments_week10_90_20_20.csv"
ASSIGNMENTS_PATH = WEEK10 / "locked_split" / "document_assignments.csv"
MANIFEST_PATH = WEEK10 / "locked_split" / "manifest.json"

SPLIT_NAMES = ["train", "dev", "test"]

failures = []


def check(condition, message):
    if condition:
        print(f"[PASS] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path, dtype=None):
    return pd.read_csv(path, dtype=dtype)


def main():
    print("========== G3.5: STRICT LOCKED SPLIT VERIFICATION ==========")

    required_files = [
        SOURCE_PATH,
        SNAPSHOT_PATH,
        ASSIGNMENTS_PATH,
        MANIFEST_PATH,
        *[
            WEEK10 / "model_data" / f"{name}_segments.csv"
            for name in SPLIT_NAMES
        ],
    ]

    missing = [path for path in required_files if not path.is_file()]

    check(
        len(missing) == 0,
        "All required source, snapshot, manifest and split files exist",
    )

    if missing:
        for path in missing:
            print(f"  Missing: {path}")
        raise FileNotFoundError(
            "Required files are missing. Verification stopped."
        )

    with MANIFEST_PATH.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    dtype = {"doc": str, "system": str}

    source = read_csv(SOURCE_PATH, dtype=dtype)
    snapshot = read_csv(SNAPSHOT_PATH, dtype=dtype)
    assignments = read_csv(ASSIGNMENTS_PATH, dtype={"doc": str})

    print("\n========== 1. HASH VERIFICATION ==========")

    source_hash = sha256(SOURCE_PATH)
    snapshot_hash = sha256(SNAPSHOT_PATH)

    expected_source_hash = manifest["source_sha256"].lower()
    expected_snapshot_hash = manifest["snapshot_sha256"].lower()

    check(
        source_hash == expected_source_hash,
        "Source SHA-256 matches manifest",
    )
    check(
        snapshot_hash == expected_snapshot_hash,
        "Snapshot SHA-256 matches manifest",
    )
    check(
        source_hash == snapshot_hash,
        "Source and snapshot SHA-256 are identical",
    )

    print("Source SHA-256:", source_hash)
    print("Snapshot SHA-256:", snapshot_hash)

    print("\n========== 2. SOURCE-SNAPSHOT VERIFICATION ==========")

    check(
        list(source.columns) == list(snapshot.columns),
        "Source and snapshot have identical columns",
    )
    check(
        source.shape == snapshot.shape,
        "Source and snapshot have identical shapes",
    )
    check(
        source.equals(snapshot),
        "Source and snapshot contain identical data in identical row order",
    )

    required_columns = {
        "doc", "system", "seg_id", "split", "y_primary"
    }

    check(
        required_columns.issubset(source.columns),
        "Source contains all required columns",
    )

    if not required_columns.issubset(source.columns):
        raise AssertionError("Required columns are missing.")

    print("\n========== 3. GLOBAL DATASET VERIFICATION ==========")

    check(
        len(source) == manifest["total_rows"],
        "Total row count matches manifest",
    )
    check(
        source["doc"].nunique() == manifest["total_documents"],
        "Total document count matches manifest",
    )
    check(
        int(source["y_primary"].sum()) == manifest["total_positive"],
        "Total positive label count matches manifest",
    )
    check(
        source[["doc", "system", "seg_id"]].duplicated().sum() == 0,
        "No duplicate system-document-segment keys",
    )
    check(
        source["y_primary"].isin([0, 1]).all(),
        "Labels are binary",
    )

    print("\n========== 4. DOCUMENT ASSIGNMENT VERIFICATION ==========")

    check(
        assignments["doc"].duplicated().sum() == 0,
        "No duplicate document assignments",
    )

    expected_assignments = (
        source[["doc", "split"]]
        .drop_duplicates()
        .sort_values(["doc", "split"])
        .reset_index(drop=True)
    )

    actual_assignments = (
        assignments[["doc", "split"]]
        .sort_values(["doc", "split"])
        .reset_index(drop=True)
    )

    check(
        expected_assignments.equals(actual_assignments),
        "Document assignments match source split assignments",
    )

    doc_split_counts = source.groupby("doc")["split"].nunique()

    check(
        (doc_split_counts <= 1).all(),
        "Every document belongs to exactly one split",
    )

    print("\n========== 5. TRAIN / DEV / TEST VERIFICATION ==========")

    for name in SPLIT_NAMES:
        expected = (
            snapshot[snapshot["split"] == name]
            .drop(columns=["split"])
            .reset_index(drop=True)
        )

        split_path = WEEK10 / "model_data" / f"{name}_segments.csv"
        actual = read_csv(split_path, dtype=dtype).reset_index(drop=True)

        stats = manifest["summary"][name]

        check(
            list(actual.columns) == list(expected.columns),
            f"{name}: columns match snapshot",
        )
        check(
            actual.shape == expected.shape,
            f"{name}: shape matches snapshot",
        )
        check(
            actual.equals(expected),
            f"{name}: data and row order match snapshot",
        )
        check(
            len(actual) == stats["rows"],
            f"{name}: row count matches manifest",
        )
        check(
            actual["doc"].nunique() == stats["docs"],
            f"{name}: document count matches manifest",
        )
        check(
            int(actual["y_primary"].sum()) == stats["positive"],
            f"{name}: positive count matches manifest",
        )

    print("\n========== 6. DOCUMENT OVERLAP VERIFICATION ==========")

    document_sets = {
        name: set(source.loc[source["split"] == name, "doc"])
        for name in SPLIT_NAMES
    }

    pairs = [
        ("train", "dev"),
        ("train", "test"),
        ("dev", "test"),
    ]

    for first, second in pairs:
        overlap = document_sets[first] & document_sets[second]

        check(
            len(overlap) == 0,
            f"No document overlap between {first} and {second}",
        )

    print("\n========== FINAL RESULT ==========")

    if failures:
        print(f"VERIFICATION FAILED: {len(failures)} check(s) failed.")
        for failure in failures:
            print(" -", failure)
        raise AssertionError("Strict split verification failed.")

    print("VERIFICATION PASSED: All checks passed.")


if __name__ == "__main__":
    main()
