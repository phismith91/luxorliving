#!/usr/bin/env python3
"""
Upload Issues to GitHub from Markdown Files

This script reads markdown files from the review_issues directory and creates
GitHub issues using the GitHub REST API.

Usage:
    # With environment variable
    export GITHUB_TOKEN=your_token_here
    python3 upload_issues_to_github.py

    # With command line argument
    python3 upload_issues_to_github.py --token YOUR_TOKEN

    # For a specific repository
    python3 upload_issues_to_github.py --repo owner/repo

Requirements:
    - GitHub Personal Access Token with 'repo' scope
    - Create token at: https://github.com/settings/tokens
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Tuple


class GitHubIssueUploader:
    """Uploads issues to GitHub from markdown files."""

    def __init__(self, repo_owner: str, repo_name: str, token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.api_base = "https://api.github.com"

    def parse_markdown_file(self, file_path: Path) -> Tuple[str, str, List[str]]:
        """Parse a markdown file and extract title, body, and labels."""
        content = file_path.read_text()
        lines = content.split('\n')

        # Extract title (first line without #)
        title = lines[0].replace('# ', '').strip()

        # Extract labels
        labels = []
        for line in lines:
            if line.startswith('**Labels:**'):
                labels_str = line.replace('**Labels:**', '').strip()
                labels = [label.strip() for label in labels_str.split(',')]
                break

        # Extract body (everything after the --- separator)
        body_start = False
        body_lines = []
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 2:
                body_start = True
                continue
            if body_start:
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        return title, body, labels

    def create_issue(self, title: str, body: str, labels: List[str]) -> Dict:
        """Create a GitHub issue using the REST API."""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"

        data = {
            "title": title,
            "body": body,
            "labels": labels
        }

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {
                    "success": True,
                    "issue_url": result.get('html_url', 'Unknown'),
                    "issue_number": result.get('number', 'Unknown')
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {
                "success": False,
                "error": f"HTTP {e.code}: {error_body}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def upload_all_issues(self, issues_dir: Path) -> Dict[str, int]:
        """Upload all issues from the markdown files."""
        stats = {
            "total": 0,
            "created": 0,
            "failed": 0
        }

        # Get all markdown files
        md_files = sorted(issues_dir.glob("*.md"))

        if not md_files:
            print(f"❌ No markdown files found in {issues_dir}")
            return stats

        print(f"\n🚀 Uploading {len(md_files)} issues to GitHub")
        print(f"📦 Repository: {self.repo_owner}/{self.repo_name}\n")

        for i, file_path in enumerate(md_files, 1):
            stats["total"] += 1

            print(f"{i}/{len(md_files)} Processing: {file_path.name}")

            try:
                # Parse the markdown file
                title, body, labels = self.parse_markdown_file(file_path)

                print(f"   Title: {title}")
                print(f"   Labels: {', '.join(labels)}")

                # Create the issue
                result = self.create_issue(title, body, labels)

                if result["success"]:
                    stats["created"] += 1
                    print(f"   ✅ Created: {result['issue_url']}")
                else:
                    stats["failed"] += 1
                    print(f"   ❌ Failed: {result['error']}")

            except Exception as e:
                stats["failed"] += 1
                print(f"   ❌ Error parsing file: {e}")

            print()

        return stats


def get_repo_from_git() -> Tuple[str, str]:
    """Try to extract repository owner and name from git remote."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()

        # Parse various GitHub URL formats
        # SSH: git@github.com:owner/repo.git
        # HTTPS: https://github.com/owner/repo.git
        # Proxy: http://...@.../git/owner/repo

        patterns = [
            r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$',  # Standard GitHub
            r'/git/([^/]+)/([^/]+?)(?:\.git)?$'  # Proxy format
        ]

        for pattern in patterns:
            match = re.search(pattern, remote_url)
            if match:
                return match.group(1), match.group(2)

        return None, None

    except Exception:
        return None, None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upload review issues to GitHub from markdown files"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--repo",
        help="Repository in format owner/name (auto-detected from git if not provided)"
    )
    parser.add_argument(
        "--issues-dir",
        default="review_issues",
        help="Directory containing markdown issue files (default: review_issues)"
    )

    args = parser.parse_args()

    # Get token
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GitHub token required")
        print("")
        print("Provide token via:")
        print("  1. Command line: --token YOUR_TOKEN")
        print("  2. Environment: export GITHUB_TOKEN=YOUR_TOKEN")
        print("")
        print("Create a token at: https://github.com/settings/tokens")
        print("Required scope: 'repo'")
        sys.exit(1)

    # Get repository
    if args.repo:
        parts = args.repo.split('/')
        if len(parts) != 2:
            print("❌ Error: Repository must be in format owner/name")
            sys.exit(1)
        repo_owner, repo_name = parts
    else:
        repo_owner, repo_name = get_repo_from_git()
        if not repo_owner or not repo_name:
            print("❌ Error: Could not detect repository from git")
            print("   Please specify with --repo owner/name")
            sys.exit(1)

    # Get issues directory
    issues_dir = Path(args.issues_dir)
    if not issues_dir.exists():
        print(f"❌ Error: Issues directory not found: {issues_dir}")
        print("")
        print("Please run create_issues_from_review.py first to generate issue files.")
        sys.exit(1)

    print("\n" + "="*80)
    print("⚙️  CONFIGURATION")
    print("="*80)
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"Issues directory: {issues_dir}")
    print(f"Token: {'*' * 20}{token[-4:] if len(token) > 4 else '****'}")

    # Create uploader
    uploader = GitHubIssueUploader(repo_owner, repo_name, token)

    # Upload all issues
    stats = uploader.upload_all_issues(issues_dir)

    # Print summary
    print("="*80)
    print("📊 UPLOAD SUMMARY")
    print("="*80)
    print(f"✅ Successfully created: {stats['created']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📈 Total processed: {stats['total']}\n")

    if stats["failed"] > 0:
        print("⚠️  Some issues failed to upload. Please check the errors above.")
        return 1
    elif stats["created"] > 0:
        print(f"🎉 All {stats['created']} issues created successfully!")
        return 0
    else:
        print("ℹ️  No issues were processed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
