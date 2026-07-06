# Changelog

All notable changes to hac-cli are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project skeleton and architecture (Phase 2)
- Domain models, ports, and exceptions
- TOML config store and OS keychain secret store
- Filesystem-backed Groovy script library with fuzzy search
- CLI commands: `hac env`, `hac groovy`, `hac scripts`
- Structured logging with secret redaction
- GitHub Actions CI/CD pipelines
- Pre-commit hooks with secret scanning

### Planned
- Phase 3: HAC HTTP client (auth + CSRF + execution)
- Phase 4: Textual TUI + NLP script selection
- Phase 5: CLAUDE.md, MCP servers, hooks
- Phase 6: Tests, docs, packaging
