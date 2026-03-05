import dagger
from dagger import dag, field, function, object_type
from urllib.parse import urlparse


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

        askpass_file = dag.current_module().source().file("assets/git-askpass.sh")
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

        repo_dir = (
            dag.container()
            .from_("alpine:3.23.3")
            .with_exec(["apk", "add", "--no-cache", "git"])
            .with_secret_variable("GIT_HTTP_PASSWORD", password)
            .with_env_variable("GIT_ASKPASS", "/tmp/git-askpass")
            .with_env_variable("GIT_TERMINAL_PROMPT", "0")
            .with_file("/tmp/git-askpass", askpass_file, permissions=0o700)
            .with_exec(clone_cmd)
            .directory("/repo")
        )
        return Repo(
            directory=repo_dir,
            repo=repo,
            username=username,
            password=password,
        )
