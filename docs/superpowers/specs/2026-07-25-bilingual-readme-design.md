# Bilingual README Design

## Goal

Publish a complete Korean project guide in `README.md` and an equivalent
English guide in `README.en.md`. Both documents must let a new reader
understand the pilot, run fixture mode, configure live mode, exercise the API,
and understand the project's limits without reading source code first.

## File and language policy

- `README.md` is the default Korean document for the target portfolio audience.
- `README.en.md` is the complete English counterpart.
- Both documents start with `한국어 | English` links.
- The two versions use the same section order, commands, variable names, API
  contracts, cautions, and claims. Translation may be natural rather than
  sentence-for-sentence.

## Required sections

1. Title, language switch, and one-sentence value proposition.
2. Problem and service overview.
3. Core capabilities and the
   `sync → analyze → review → audit → evaluation` demo flow.
4. Architecture and the roles of FastAPI, Neo4j Aura, Gemini, and Cohere.
5. Prerequisites.
6. Fixture quick start with virtual environment, dependency installation,
   server startup, browser URL, and health check.
7. Live-mode credential setup:
   - Gemini API key from the official Google AI Studio key page;
   - Cohere evaluation or production key from the official API Keys dashboard;
   - Neo4j Aura connection URI, username, and password from instance creation
     or its downloaded credentials file.
8. `.env.example` copy and `.env` registration example with blank placeholders
   only.
9. Fixture, live, and misconfigured mode rules.
10. Browser workflow and complete REST API examples.
11. Endpoint and error-status reference.
12. Tests, Docker execution, and optional Cloud Run command.
13. Current modular backend directory structure.
14. Data source, security and cost cautions, and honest pilot limitations.

## Accuracy and security rules

- Derive commands, paths, defaults, environment variables, and API contracts
  from the current repository.
- Use only official Google, Cohere, Neo4j, Google Cloud, and EUR-Lex links.
- Never include real secrets, credential-shaped examples, measured results
  that were not run, or claims of successful live credentials or public
  deployment.
- State that all five required live values must be set; zero selects fixture
  mode and a partial set selects misconfigured mode.
- Explain that `.env` must not be committed and keys must remain server-side.
- Distinguish deterministic fixture evaluation from live model performance.
- State that this is a portfolio pilot, not legal advice or a production
  compliance system.

## Verification

- Check every command and environment variable against the repository.
- Confirm both README files contain the same required headings and links.
- Confirm `.env` remains ignored.
- Run `PYTHONPATH=. python -m pytest -q`.
- Scan both files for accidental secret values and unsupported performance,
  production, or deployment claims.
