#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
import subprocess
from pathlib import Path
import pandas as pd
import textwrap

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
CUSTOM_DIR = ROOT / "custom_parser"
TESTS_DIR = ROOT / "tests"

CUSTOM_DIR.mkdir(exist_ok=True)
TESTS_DIR.mkdir(exist_ok=True)

PARSER_TEMPLATE = """\
\"\"\"Auto-generated parser for {target}.

Implements parse(pdf_path: str) -> pd.DataFrame.
Simple heuristic: use pdfplumber to extract tables; try to align column names to expected columns.
\"\"\"
from typing import List
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches

EXPECTED_COLUMNS = {expected_columns!r}

def _extract_tables(pdf_path: str) -> List[List[List[str]]]:
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            # try extract_table (may return None)
            t = p.extract_table()
            if t:
                tables.append(t)
            else:
                text = p.extract_text()
                if text:
                    # crude split: each non-empty line -> token list
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    if lines:
                        token_rows = [re.split(r"\\s{2,}|\\t", line) for line in lines]
                        # if first row looks like header (contains words), include
                        tables.append(token_rows)
    return tables

def parse(pdf_path: str) -> pd.DataFrame:
    tables = _extract_tables(pdf_path)
    candidates = []
    for t in tables:
        if not t:
            continue
        # try convert first row as header
        header = t[0]
        rows = t[1:] if len(t) > 1 else []
        try:
            df = pd.DataFrame(rows, columns=header)
        except Exception:
            # fallback: one-column dataframe with joined text
            df = pd.DataFrame({"raw": [" ".join(r) if isinstance(r, list) else str(r) for r in t]})
        # normalize column names
        df.columns = [re.sub(r"\\s+", " ", str(c)).strip() for c in df.columns]
        # try to map close column names to expected columns
        mapping = {}
        for exp in EXPECTED_COLUMNS:
            match = get_close_matches(exp, df.columns, n=1, cutoff=0.6)
            if match:
                mapping[match[0]] = exp
        if mapping:
            df = df.rename(columns=mapping)
        # ensure all expected columns exist
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[EXPECTED_COLUMNS]
        candidates.append(df)
    if candidates:
        result = pd.concat(candidates, ignore_index=True)
        # basic cleanup
        for c in result.select_dtypes(include=['object']).columns:
            result[c] = result[c].astype(str).str.strip()
        return result
    # nothing found -> empty with expected cols
    return pd.DataFrame(columns=EXPECTED_COLUMNS)
"""

TEST_TEMPLATE = """\
import os
import pandas as pd
from custom_parser.{target}_parser import parse

def test_parse_matches_expected():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', '{target}')
    pdf_path = os.path.join(data_dir, 'sample.pdf')
    expected_csv = os.path.join(data_dir, 'expected.csv')
    df_actual = parse(pdf_path)
    df_expected = pd.read_csv(expected_csv)
    # normalize to strings and strip whitespace
    df_actual = df_actual.astype(str).apply(lambda col: col.str.strip())
    df_expected = df_expected.astype(str).apply(lambda col: col.str.strip())
    assert df_actual.equals(df_expected)
"""

def infer_expected_columns(csv_path: Path):
    df = pd.read_csv(csv_path)
    return df.columns.tolist()

def write_parser(target: str, expected_columns: list):
    path = CUSTOM_DIR / f"{target}_parser.py"
    content = PARSER_TEMPLATE.format(target=target, expected_columns=expected_columns)
    path.write_text(content, encoding="utf-8")
    print(f"[agent] wrote parser: {path}")
    return path

def write_test(target: str):
    path = TESTS_DIR / f"test_{target}_parser.py"
    path.write_text(TEST_TEMPLATE.format(target=target), encoding="utf-8")
    print(f"[agent] wrote test: {path}")
    return path

def run_pytest_for_target(target: str) -> bool:
    test_file = TESTS_DIR / f"test_{target}_parser.py"
    if not test_file.exists():
        print("[agent] test file missing, cannot run pytest")
        return False
    cmd = [sys.executable, "-m", "pytest", "-q", str(test_file)]
    try:
        subprocess.run(cmd, check=True)
        print("[agent] pytest passed")
        return True
    except subprocess.CalledProcessError:
        print("[agent] pytest failed")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="target bank folder in data/")
    args = parser.parse_args()
    target = args.target.strip().lower()

    data_folder = DATA_DIR / target
    pdf_path = data_folder / "sample.pdf"
    csv_path = data_folder / "expected.csv"

    if not data_folder.exists():
        print(f"[agent] ERROR: data folder {data_folder} not found.")
        sys.exit(2)
    if not pdf_path.exists() or not csv_path.exists():
        print(f"[agent] ERROR: require sample.pdf and expected.csv inside {data_folder}")
        sys.exit(2)

    expected_cols = infer_expected_columns(csv_path)
    print(f"[agent] expected columns: {expected_cols}")

    # generate test once
    write_test(target)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"[agent] attempt {attempt}/{max_attempts}")
        write_parser(target, expected_cols)
        passed = run_pytest_for_target(target)
        if passed:
            print(f"[agent] SUCCESS: parser passed on attempt {attempt}")
            break
        else:
            print(f"[agent] self-fix: (no-op simple strategy) retrying...")
    else:
        print("[agent] FAILED: parser did not pass after attempts")
        sys.exit(1)

if __name__ == "__main__":
    main()

