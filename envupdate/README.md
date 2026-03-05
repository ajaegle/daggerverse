# Dagger Envupdate module

This module updates `KEY=VALUE` lines inside a managed block of one env file in a `Directory`.

Scope:
- one file per call
- git-agnostic
- all requested updates succeed or fail together

Managed block markers (exact, case-sensitive):
- `# managed by image automation start`
- `# managed by image automation end`

## CLI examples

Update one key in a local checkout and print the updated file:

```bash
dagger call \
  update-file \
  --directory /path/to/sample-manifests \
  --env-file-path stacks/dev/infra/.env \
  --update SECOND_APP_VERSION=0.2.0 \
  file --path stacks/dev/infra/.env contents
```

Update multiple keys in the same managed block:

```bash
dagger call \
  update-file \
  --directory /path/to/sample-manifests \
  --env-file-path stacks/dev/infra/.env \
  --update FIRST_APP_VERSION=0.1.1 \
  --update SECOND_APP_VERSION=0.2.0
```

## Validation

- `update` must be non-empty
- each update must be exactly one `KEY=VALUE`
- duplicate keys in input updates are rejected
- key format: `^[A-Z0-9_]+$`
- value format: `^[A-Za-z0-9._:@-]+$`
- `@` is allowed at most once and not at the start or end
- target file must be readable UTF-8 text
- managed markers must each exist exactly once, in correct order (start before end)
- each requested key must exist exactly once between markers

If validation fails, the function raises one aggregated error and does not rewrite the file.
