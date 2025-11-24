# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

The Hector team takes security seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

If you discover a security vulnerability, please report it by:

1. **Email**: Send details to the project maintainers (see AUTHORS or package metadata)
2. **Do NOT** open a public GitHub issue for security vulnerabilities
3. Include as much information as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### Response Timeline

- **Initial Response**: We aim to acknowledge receipt within 48 hours
- **Status Updates**: We will provide updates on the investigation within 7 days
- **Resolution**: We will work to address confirmed vulnerabilities as quickly as possible
  - Critical: within 7 days
  - High: within 30 days
  - Medium/Low: within 90 days

### What to Expect

- We will confirm receipt of your vulnerability report
- We will investigate and validate the issue
- We will develop and test a fix
- We will release a security patch and credit you (if desired)
- We will publish a security advisory

## Security Best Practices

When deploying Hector:

1. **Environment Variables**: Never commit `.env` files or secrets to version control
2. **Dependencies**: Regularly run `pip-audit` to check for vulnerable dependencies
3. **Updates**: Keep dependencies up to date
4. **Access Control**: Restrict access to production environments
5. **Monitoring**: Monitor logs for suspicious activity
6. **HTTPS**: Always use HTTPS in production
7. **Input Validation**: Validate and sanitize all user inputs

## Security Scanning

This project uses automated security scanning:

- **Dependency Auditing**: `pip-audit` runs in CI/CD pipeline
- **Code Quality**: Ruff linting and MyPy type checking
- **GitHub Security**: Dependabot alerts enabled

## Disclosure Policy

- We follow responsible disclosure practices
- Security advisories will be published after fixes are released
- We credit security researchers (unless they prefer to remain anonymous)

## Contact

For security concerns, contact the project maintainers listed in the repository.
