# Security Policy

## Supported Versions

Only the **latest stable release** receives security updates. Older versions are
not actively maintained.

| Version        | Supported          |
| -------------- | ------------------ |
| latest (1.2.x) | :white_check_mark: |
| older          | :x:                |

See the [Releases page](https://github.com/phismith91/luxorliving/releases) for
the current version.

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues!**

### How to Report a Security Vulnerability?

1. **Email:** Send a detailed description to:
   [software@withphil.de](mailto:software@withphil.de)
2. **Subject:** Use "SECURITY: [Brief Description]" as subject
3. **Content:** Please include:
   - Detailed description of the security vulnerability
   - Steps to reproduce
   - Potential impact
   - Affected versions
   - Your contact information for follow-up questions

### What Happens After Reporting?

- **Response Time:** I will contact you within 48 hours
- **Investigation:** Security vulnerabilities are prioritized
- **Updates:** You will receive regular updates on progress
- **Publication:** For confirmed vulnerabilities, a fix will be developed and a
  security advisory created

### If the Vulnerability is Accepted:

- A security advisory will be published on GitHub
- A fix will be developed and tested
- A new version will be released
- You will receive credit in the release notes (if desired)

### If the Vulnerability is Declined:

- I will explain the decision to you
- If needed, the issue will be treated as a regular GitHub issue

## Automated Security Scanning

This project uses automated security scanning to detect vulnerabilities:

- **Python Code Security:** `bandit` runs on every pull request and push to main
- **Dependency Vulnerabilities:** `pip-audit` scans dependencies weekly
- **Dependency Updates:** Dependabot creates PRs for outdated dependencies
  weekly
- **Workflow:** Security scans run automatically via GitHub Actions (see
  `.github/workflows/security.yml`)

### Security Scan Reports

Security scan results are available as workflow artifacts:

1. Go to [Actions](../../actions/workflows/security.yml)
2. Select latest workflow run
3. Download `bandit-security-report` or `pip-audit-report` artifacts

### Security Best Practices

This integration follows security best practices:

1. **No Hardcoded Secrets:** All credentials stored in Home Assistant's secure
   storage
2. **HTTPS Only:** API communication uses HTTPS when available
3. **Input Validation:** User inputs are validated before processing
4. **Pinned Dependencies:** All dependencies pinned in `manifest.json`
5. **Repair Flows:** Automatic credential update flows for authentication issues

## Security Aspects of the LUXORliving Integration

Since LUXORliving is a Home Assistant integration, please note:

- **Network Communication:** Uses KNX/IP protocol for local network
  communication
- **Authentication:** REST API for tunneling authentication (local IPs only)
- **Data:** No personal data is stored or transmitted
- **Permissions:** Only access to local KNX devices and Home Assistant

## Responsible Disclosure

Please keep security vulnerabilities confidential until a fix is available.
Thank you for helping make the LUXORliving integration more secure! 🛡️
