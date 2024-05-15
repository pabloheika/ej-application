from functools import reduce
from invoke import task

from .base import runner

__all__ = [
    "docker_up",
    "docker_build",
    "docker_exec",
    "docker_attach",
    "docker_test",
    "docker_stop",
    "docker_rm",
    "docker_logs",
    "docker_push",
]

COMPOSE_BINARY = "docker compose"


@task
def docker_up(ctx, dry_run=False, d=False):
    """
    Executes EJ on url http://localhost:8000
    """
    do = runner(ctx, dry_run, pty=True)
    file = "docker/docker-compose.yml"
    compose = (
        f"{COMPOSE_BINARY} -f {file} up -d" if d else f"{COMPOSE_BINARY} -f {file} up"
    )
    do(compose)


@task
def docker_build(ctx, dry_run=False, no_cache=False, prod=False, registry="", tag=""):
    """
    Build EJ web server image.
    By default, this command will install all EJ dependencies.
    """
    do = runner(ctx, dry_run, pty=True)
    image = f"{registry}/ej-server" if registry else "docker-server"
    tagged_image = f"{image}:{tag}" if tag else image
    argsList = ["-f docker/Dockerfile", f"-t {tagged_image}"]
    argsList.append("--no-cache") if no_cache else False
    args: str = reduce(lambda x, y: x + " " + y, argsList)
    do(f"docker build {args} .")


@task
def docker_push(ctx, dry_run=False, registry="", tag=""):
    """
    Push EJ server Docker image to a public registry.
    """
    do = runner(ctx, dry_run, pty=True)
    image = f"{registry}/ej-server" if registry else "docker-server"
    tagged_image = f"{image}:{tag}" if tag else image
    do(f"docker push {tagged_image}")


@task
def docker_exec(ctx, command, dry_run=False, build=False):
    """
    Executes a command inside EJ web server container;
    """
    do = runner(ctx, dry_run, pty=True)
    do(
        f"docker exec --user=root -it  server /bin/bash -c 'source /root/.bashrc && {command}'"
    )


@task
def docker_test(ctx, dry_run=False, build=False):
    """
    Runs EJ tests;
    """
    do = runner(ctx, dry_run, pty=True)
    do("docker exec --user=root -it  server /bin/bash -c 'inv test'")


@task
def docker_attach(ctx):
    """
    Connect to EJ web server container;
    """
    do = runner(ctx, dry_run=False, pty=True)
    do("docker exec -it server bash")


@task
def docker_stop(ctx):
    """
    Stop EJ containers;
    """
    do = runner(ctx, dry_run=False, pty=True)
    do(f"{COMPOSE_BINARY} -f docker/docker-compose.yml stop")


@task
def docker_rm(ctx):
    """
    Remove EJ containers;
    """
    do = runner(ctx, dry_run=False, pty=True)
    do(f"{COMPOSE_BINARY} -f docker/docker-compose.yml rm")


@task
def docker_logs(ctx):
    """
    Follows EJ web server log;
    """
    do = runner(ctx, dry_run=False, pty=True)
    do("docker logs -f server")
