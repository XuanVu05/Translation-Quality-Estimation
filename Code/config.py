"""
Central Path and Configuration Module for Translation-Quality-Estimation.

This module provides unified, robust paths to datasets, model artifacts,
reports, and results regardless of current working directory.
"""
from pathlib import Path

# Project root: Translation-Quality-Estimation/
ROOT = Path(__file__).resolve().parent.parent

# Core Top-Level Directories
DATA_DIR = ROOT / "Data"
CODE_DIR = ROOT / "Code"
RESULTS_DIR = ROOT / "Results"
REPORT_DIR = ROOT / "Report"

# Data Subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
DETAILS_DIR = DATA_DIR / "details"
OFFICIAL_WMT_DIR = DATA_DIR / "official_wmt2020"
ORIGINAL_OUTPUTS_DIR = DATA_DIR / "original_outputs"

# Results Subdirectories
WEEK10_DIR = RESULTS_DIR / "week10"
WEEK11_DIR = RESULTS_DIR / "week11"
DATA_QUALITY_DIR = WEEK10_DIR / "data_quality"
MODEL_DATA_DIR = WEEK10_DIR / "model_data"

# Helper resolvers for resilient path finding
def resolve_mqm_path() -> Path:
    candidates = [
        RAW_DATA_DIR / "mqm_newstest2020_ende.tsv",
        DATA_DIR / "mqm_newstest2020_ende.tsv",
        ROOT / "mqm_newstest2020_ende.tsv",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]

def resolve_mapping_path() -> Path:
    candidates = [
        DETAILS_DIR / "en-de.txt",
        DATA_DIR / "details" / "en-de.txt",
        ROOT / "data" / "details" / "en-de.txt",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]

def resolve_original_outputs_dir() -> Path:
    candidates = [
        ORIGINAL_OUTPUTS_DIR,
        ROOT / "original_outputs",
        DATA_DIR / "original_outputs",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return candidates[0]

MQM_PATH = resolve_mqm_path()
MAPPING_PATH = resolve_mapping_path()
