from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_repository_governance_files_exist():
    assert (ROOT / ".github" / "CODEOWNERS").is_file()
    assert (ROOT / ".github" / "dependabot.yml").is_file()
    assert (ROOT / ".github" / "workflows" / "release.yml").is_file()
    assert (ROOT / ".github" / "workflows" / "mutation.yml").is_file()
    assert (ROOT / "docs" / "BRANCH_PROTECTION.md").is_file()


def test_pyproject_is_dependency_source_of_truth():
    with (ROOT / "pyproject.toml").open("rb") as file_obj:
        project = tomllib.load(file_obj)["project"]

    optional_dependencies = project["optional-dependencies"]
    assert "dev" in optional_dependencies
    assert "mutation" in optional_dependencies
    assert not (ROOT / "requirements_dev.txt").exists()
    assert not (ROOT / "requirements_style.txt").exists()


def test_branch_protection_doc_lists_enforced_reviews_and_checks():
    content = (ROOT / "docs" / "BRANCH_PROTECTION.md").read_text(encoding="utf-8")

    assert "required reviews" in content.lower()
    assert "required status checks" in content.lower()
    assert "Run Tests" in content
    assert "Pre-commit checks" in content
    assert "Release Checks" in content


def test_codeowners_covers_core_repository_paths():
    content = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")

    assert "* @phismith91" in content
    assert "/custom_components/luxor_living/ @phismith91" in content
    assert "/tests/ @phismith91" in content
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        pattern, *owners = stripped.split()
        assert pattern
        assert owners
        assert all(owner.startswith("@") for owner in owners)
