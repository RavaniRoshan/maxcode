# Security policy

## Reporting a vulnerability

Report security issues through GitHub's private vulnerability reporting on this
repository, or by email to the maintainers listed in `pyproject.toml`. Do not
open a public issue for a vulnerability.

Include the affected version, a reproduction, and the impact. We aim to reply
within 72 hours.

## Secrets

maxcode never stores API keys. Keys are read from environment variables named
in `maxcode.toml`. If you find a key in a log, a config file, or a committed
file, treat it as compromised and rotate it immediately.

## Scope

The engine runs with the permissions of the user who starts maxcode. Review a
plan before approving it. `cmd:` checks run shell commands and are shown in the
plan; approve them only when you understand them.
