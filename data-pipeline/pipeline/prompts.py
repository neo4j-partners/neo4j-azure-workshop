"""Prompt templates for entity extraction from SEC filings.

Contains custom prompt templates that extend neo4j-graphrag-python's
ERExtractionTemplate for handling financial document conventions.
"""

import csv
from pathlib import Path

from neo4j_graphrag.generation.prompts import ERExtractionTemplate


def load_approved_companies(csv_path: Path) -> set[str]:
    """Load approved company names from CSV file.

    Args:
        csv_path: Path to Company_Filings.csv

    Returns:
        Set of uppercase company names
    """
    approved = set()
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get("name")
            if name:
                approved.add(name.strip().upper())
    return approved


def build_company_instruction(approved_companies: set[str]) -> str:
    """Build the company extraction instruction text.

    Args:
        approved_companies: Set of approved company names

    Returns:
        Instruction text to prepend to the extraction template
    """
    joined_names = "\n".join(f"- {name}" for name in sorted(approved_companies))

    return (
        "Extract only information about the following companies. "
        "If a company is mentioned but is not in this list, ignore it. "
        "When extracting, the company name must match exactly as shown below. "
        "Do not generate or include any company not on this list or an alternate name "
        "for any company on this list. "
        "ONLY USE THE COMPANY NAME EXACTLY AS SHOWN IN THE LIST. "
        "If the text refers to 'the Company', 'the Registrant', or uses a pronoun or "
        "generic phrase instead of a company name, "
        "you MUST look up and use the exact company name from the allowed list based on "
        "context (such as the file being processed). "
        "UNDER NO CIRCUMSTANCES should you output 'the Company', 'the Registrant', or any "
        "generic phrase as a company name. "
        "Only use the exact allowed company name.\n\n"
        f"Allowed Companies (match exactly):\n{joined_names}\n\n"
    )


def create_extraction_template(csv_path: Path) -> ERExtractionTemplate:
    """Create a custom extraction template for SEC filings.

    Loads approved companies from CSV and creates a template that:
    - Restricts extraction to approved companies only
    - Handles SEC pronoun conventions ("the Company", "the Registrant")
    - Uses exact company name matching

    Args:
        csv_path: Path to Company_Filings.csv

    Returns:
        Configured ERExtractionTemplate instance
    """
    approved_companies = load_approved_companies(csv_path)
    company_instruction = build_company_instruction(approved_companies)
    custom_template = company_instruction + ERExtractionTemplate.DEFAULT_TEMPLATE

    return ERExtractionTemplate(template=custom_template)


def get_default_template() -> ERExtractionTemplate:
    """Get the extraction template using the default company filings path.

    Looks for Company_Filings.csv in the financial-data directory
    relative to the project root.

    Returns:
        Configured ERExtractionTemplate instance
    """
    # pipeline/ -> data-pipeline/ -> neo4j-azure-workshop/
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / "financial-data" / "Company_Filings.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Company_Filings.csv not found at {csv_path}. "
            "Ensure the financial-data directory exists with the company list."
        )

    return create_extraction_template(csv_path)
