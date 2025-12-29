# Security Policy

## Supported Versions

The following versions of the LUXORliving integration are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues!**

### How to Report a Security Vulnerability?

1. **Email:** Send a detailed description to: [philismith91@gmail.com](mailto:philismith91@gmail.com)
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
- **Publication:** For confirmed vulnerabilities, a fix will be developed and a security advisory created

### If the Vulnerability is Accepted:

- A security advisory will be published on GitHub
- A fix will be developed and tested
- A new version will be released
- You will receive credit in the release notes (if desired)

### If the Vulnerability is Declined:

- I will explain the decision to you
- If needed, the issue will be treated as a regular GitHub issue

## Security Aspects of the LUXORliving Integration

Since LUXORliving is a Home Assistant integration, please note:

- **Network Communication:** Uses KNX/IP protocol for local network communication
- **Authentication:** REST API for tunneling authentication (local IPs only)
- **Data:** No personal data is stored or transmitted
- **Permissions:** Only access to local KNX devices and Home Assistant

## Responsible Disclosure

Please keep security vulnerabilities confidential until a fix is available. Thank you for helping make the LUXORliving integration more secure! 🛡️
