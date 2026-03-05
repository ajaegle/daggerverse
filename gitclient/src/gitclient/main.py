import dagger
from dagger import dag, field, function, object_type
from urllib.parse import urlparse


def _git_base_container(password: dagger.Secret) -> dagger.Container:
    askpass_file = dag.current_module().source().file("assets/git-askpass.sh")
    return (
        dag.container()
        .from_("alpine:3.23.3")
        .with_exec(["apk", "add", "--no-cache", "git"])
        .with_secret_variable("GIT_HTTP_PASSWORD", password)
        .with_env_variable("GIT_ASKPASS", "/tmp/git-askpass")
        .with_env_variable("GIT_TERMINAL_PROMPT", "0")
        .with_file("/tmp/git-askpass", askpass_file, permissions=0o700)
    )


@object_type
class Repo:
    directory: dagger.Directory = field()
    repo: str = field()
    username: str = field()
    password: dagger.Secret = field()

    @function
    def worktree(self) -> dagger.Directory:
        """Return the repository contents without the .git directory."""
        return self.directory.without_directory(".git")

    @function
    def update_worktree(self, worktree: dagger.Directory) -> "Repo":
        """Replace non-.git content while preserving existing .git metadata."""
        updated_directory = (
            dag.directory()
            .with_directory(".", worktree.without_directory(".git"))
            .with_directory(".git", self.directory.directory(".git"))
        )
        return Repo(
            directory=updated_directory,
            repo=self.repo,
            username=self.username,
            password=self.password,
        )

    @function
    async def push(self, remote: str = "origin", branch: str = "") -> str:
        """Push the current repository state from a fresh Git container."""
        if not remote:
            raise ValueError("remote must not be empty")

        push_cmd = ["git", "-c", f"credential.username={self.username}", "push", remote]
        if branch:
            push_cmd.append(branch)

        return await (
            _git_base_container(self.password)
            .with_directory("/repo", self.directory)
            .with_workdir("/repo")
            .with_exec(push_cmd)
            .stderr()
        )


@object_type
class Gitclient:
    @function
    def clone(
        self,
        repo: str,
        username: str,
        password: dagger.Secret,
        ref: str = "main",
    ) -> Repo:
        """Clone an HTTPS repository using username + PAT/password auth."""
        parsed = urlparse(repo)
        if parsed.scheme != "https":
            raise ValueError("repo must use https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("repo must not contain embedded credentials")
        if not parsed.netloc:
            raise ValueError("repo must be a valid https URL")

        clone_cmd = [
            "git",
            "-c",
            f"credential.username={username}",
            "clone",
            "--branch",
            ref,
            "--single-branch",
            repo,
            "/repo",
        ]

        repo_dir = _git_base_container(password).with_exec(clone_cmd).directory("/repo")
        return Repo(
            directory=repo_dir,
            repo=repo,
            username=username,
            password=password,
        )
