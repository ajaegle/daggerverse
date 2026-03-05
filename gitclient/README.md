# Dagger Git Client module

This module allows working with git repositories. It supports cloning with PAT authentication and basic operations.

## Usage

```shell
dagger call clone --username ajaegle \
                  --password "op://Private/GitHub PAT dagger envupdate checkout push/token" \
                  --repo https://github.com/ajaegle/sample-manifests \
                  worktree entries
```
