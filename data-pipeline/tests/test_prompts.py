"""Tests for prompt templates in pipeline.prompts."""

import tempfile
from pathlib import Path

import pytest

from pipeline.prompts import (
    build_company_instruction,
    load_approved_companies,
    create_extraction_template,
)


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample Company_Filings.csv for testing."""
    csv_content = """cusip6,cik,name,cusip,path_Mac_ix,path_Windows,ticker
23135,1018724,AMAZON,23135106,data/sample.pdf,data\\sample.pdf,AMZN
67066,1045810,NVIDIA CORPORATION,067066G104,data/sample2.pdf,data\\sample2.pdf,NVDA
378331,1490054,APPLE INC,3783310,data/sample3.pdf,data\\sample3.pdf,AAPL
"""
    csv_path = tmp_path / "Company_Filings.csv"
    csv_path.write_text(csv_content)
    return csv_path


def test_load_approved_companies(sample_csv: Path):
    """Test loading companies from CSV."""
    companies = load_approved_companies(sample_csv)

    assert len(companies) == 3
    assert "AMAZON" in companies
    assert "NVIDIA CORPORATION" in companies
    assert "APPLE INC" in companies
    # Should be uppercase
    assert all(c.isupper() for c in companies)


def test_build_company_instruction():
    """Test building company instruction text."""
    companies = {"AMAZON", "APPLE INC"}
    instruction = build_company_instruction(companies)

    assert "AMAZON" in instruction
    assert "APPLE INC" in instruction
    assert "the Company" in instruction
    assert "the Registrant" in instruction
    assert "ONLY USE THE COMPANY NAME EXACTLY" in instruction


def test_create_extraction_template(sample_csv: Path):
    """Test creating extraction template."""
    template = create_extraction_template(sample_csv)

    # Template should include company names
    assert "AMAZON" in template.template
    assert "NVIDIA CORPORATION" in template.template
    assert "APPLE INC" in template.template


def test_load_approved_companies_empty_csv(tmp_path: Path):
    """Test handling of CSV with no data."""
    csv_content = """cusip6,cik,name,cusip,path_Mac_ix,path_Windows,ticker
"""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(csv_content)

    companies = load_approved_companies(csv_path)
    assert len(companies) == 0
