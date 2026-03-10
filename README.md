# Daggerverse

This repository contains public [Dagger](https://dagger.io/) modules.

## Modules

### `gitclient`

`gitclient` provides basic Git repository operations for Dagger workflows, including cloning with authentication,
editing files in the worktree, committing changes, and pushing back to a remote.

See [gitclient/README.md](gitclient/README.md) for usage details.

### `envupdate`

`envupdate` updates `KEY=VALUE` entries inside a managed block in an env file within a Dagger `Directory`. It is
intended for safe, validated env-file updates in automation workflows.

See [envupdate/README.md](envupdate/README.md) for usage details.
