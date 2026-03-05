# Dagger Git Client module

This module allows working with git repositories. It supports cloning with PAT authentication and basic operations.

## Usage

Cloning a repository and accessing the worktree (as a directory)

```shell
dagger call clone --username ajaegle \
                  --password "op://Private/GitHub PAT dagger envupdate checkout push/token" \
                  --repo https://github.com/ajaegle/sample-manifests \
                  worktree entries
```

Cloning a repository, updating and commiting a file and pushing the changes back to the remote.

```shell
dagger call clone --username ajaegle \
                  --password "op://Private/GitHub PAT dagger envupdate checkout push/token" \
                  --repo https://github.com/ajaegle/sample-manifests \
                  write-file --path test.txt --content "hello from dagger at $(date)" \
                  add-all \
                  commit --message "test: update file via gitclient" --username "ajaegle" --email "mail@ajaegle.de" \
                  push --remote origin --branch main

```
