import subprocess
import pytest

DOCKER_CMD = [
    "docker",
    "run",
    "--rm",
    "--network",
    "none",
    "--memory",
    "512m",
    "--read-only",
    "--tmpfs",
    "/tmp:size=64m",
    "--user",
    "1000",
    "stats-ai-r-sandbox",
    "Rscript",
    "-e",
]


def test_r_cat_output():
    """R sandbox can execute basic R and capture stdout."""
    result = subprocess.run(
        DOCKER_CMD + ["cat('hello from R')"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "hello from R" in result.stdout


def test_r_system_disabled():
    """system() is blocked by Rprofile.site."""
    result = subprocess.run(
        DOCKER_CMD + ["system('ls')"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "system() is disabled" in result.stderr


def test_r_download_file_disabled():
    """download.file() is blocked by Rprofile.site."""
    result = subprocess.run(
        DOCKER_CMD + ["download.file('http://example.com', '/tmp/x')"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "download.file() is disabled" in result.stderr
