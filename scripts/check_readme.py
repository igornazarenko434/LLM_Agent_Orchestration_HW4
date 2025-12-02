import argparse
import re
import sys
from pathlib import Path

def check_readme(readme_path: Path):
    """
    Checks the README.md file for structural and content requirements.
    - Ensures a minimum number of sections.
    - Ensures a minimum line count.
    - Optionally checks for specific keywords or links.
    """
    print(f"--- Checking README.md: {readme_path} ---")

    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}")
        sys.exit(1)

    content = readme_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Requirement 1: Minimum line count (e.g., from PRD M8.3)
    min_lines = 300 # Based on PRD M8.3, README >=300 lines
    if len(lines) < min_lines:
        print(f"❌ Line count check failed: {len(lines)} lines found, expected >= {min_lines}.")
        sys.exit(1)
    print(f"✅ Line count check passed: {len(lines)} lines found (expected >= {min_lines}).")

    # Requirement 2: Minimum number of sections (e.g., from PRD M8.3)
    section_pattern = re.compile(r"^##\s+\d+\.\s+\w+") # Matches "## 1. Section Title"
    sections = [line for line in lines if section_pattern.match(line)]
    min_sections = 15 # Based on PRD M8.3, README >=15 sections
    
    if len(sections) < min_sections:
        print(f"❌ Section count check failed: {len(sections)} sections found, expected >= {min_sections}.")
        for section in sections:
            print(f"  - {section}")
        sys.exit(1)
    print(f"✅ Section count check passed: {len(sections)} sections found (expected >= {min_sections}).")
    
    # Optional: Check for specific links/keywords if needed, e.g., "ISO/IEC 25010" or "ADR register"
    if "ISO/IEC 25010" not in content:
        print(f"⚠️ Warning: 'ISO/IEC 25010' keyword not found in README. Ensure quality standards are referenced.")
    if "[docs/architecture/adr_register.md]" not in content:
        print(f"⚠️ Warning: Link to 'ADR register' not found in README. Ensure architecture docs are linked.")


    print(f"\n--- README.md check completed successfully ---")
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check README.md for structural and content requirements.")
    parser.add_argument("readme_file", type=str, nargs="?", default="README.md",
                        help="Path to the README.md file to check.")
    
    args = parser.parse_args()
    
    check_readme(Path(args.readme_file))
