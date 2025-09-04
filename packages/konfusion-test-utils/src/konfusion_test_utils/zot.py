from __future__ import annotations

import base64
import json
import logging
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

import bcrypt
from konfusion_test_utils.config import Config

if TYPE_CHECKING:
    import os

log = logging.getLogger(__name__)


class ZotError(Exception):
    pass


class ZotAlreadyRunningError(ZotError):
    pass


class ZotIsDownError(ZotError):
    pass


class ZotFailedToComeUpError(ZotError):
    pass


class Zot:
    def __init__(self, config: Config | None = None) -> None:
        if not config:
            config = Config.load_from_env()
        self._config = config

    @property
    def host(self) -> str:
        return f"localhost:{self._config.zot_port}"

    @property
    def url(self) -> str:
        return f"https://{self.host}"

    def check_status(self) -> None:
        req = urllib.request.Request(f"https://{self.host}/v2/")
        req.add_header("Authorization", f"Basic {self._basic_auth()}")
        try:
            with urllib.request.urlopen(  # noqa: S310 # scheme is always https
                req,
                context=self._ssl_context(),
                timeout=1.0,
            ):
                pass
        except urllib.error.URLError as e:
            raise ZotIsDownError(repr(e)) from e

    def wait_till_up(self, timeout_seconds: float = 60.0) -> None:
        start_time = time.time()

        while True:
            try:
                self.check_status()
                return None
            except ZotIsDownError as e:
                log.warning("Zot registry API not yet up: %s", e)

            remaining_time = timeout_seconds - (time.time() - start_time)
            if remaining_time < 1:
                raise ZotFailedToComeUpError(
                    f"Zot registry API failed to start in {timeout_seconds} seconds. "
                    f"Check the status of the {self._config.zot_container_name} container."
                )

            time.sleep(1)

    def run(self, *, restart: bool = False, clean: bool = False) -> None:
        """Run an instance of the Zot container registry in a podman container."""
        proc = subprocess.run(
            ["podman", "container", "exists", self._config.zot_container_name],
            check=False,
        )
        container_exists = proc.returncode == 0
        if container_exists and not restart:
            raise ZotAlreadyRunningError()

        self._config.zot_root_dir.mkdir(parents=True, exist_ok=True)

        # Clean storage directory unless explicitly configured to reuse
        storage_dir = self._config.zot_root_dir / "registry"
        if storage_dir.exists():
            if clean:
                log.info("Cleaning Zot storage directory: %s", storage_dir)
                shutil.rmtree(storage_dir)
            else:
                log.info("Reusing Zot storage directory: %s", storage_dir)

        zot_config = _ZotConfig(self._config)

        _generate_ca_cert(
            ca_key_path=self._config.ca_key_path, ca_cert_path=self._config.ca_cert_path
        )
        _generate_cert_signed_by_own_ca(
            ca_key_path=self._config.ca_key_path,
            ca_cert_path=self._config.ca_cert_path,
            cert_path=zot_config.zot_cert_path(),
            key_path=zot_config.zot_key_path(),
        )

        zot_config.zot_htpasswd_path().write_text(self._htpasswd_content())

        zot_config_json = json.dumps(zot_config.zot_config(), indent=2)
        zot_config.zot_config_path().write_text(zot_config_json + "\n")

        cmd = [
            "podman",
            "run",
            "--rm",
            "--detach",
            f"--volume={self._config.zot_root_dir.resolve()}:{zot_config.root_dir_in_container}",
            f"--publish={self._config.zot_port}:{self._config.zot_port}",
            f"--name={self._config.zot_container_name}",
            self._config.zot_container_image,
            "serve",
            zot_config.zot_config_path(in_container=True),
        ]
        if restart:
            cmd.insert(2, "--replace")

        log.info("Starting Zot container (name=%s)", self._config.zot_container_name)
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            text=True,
            check=True,
        )

    def kill(self) -> None:
        subprocess.run(
            ["podman", "kill", self._config.zot_container_name],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def write_containers_auth_json(self, path: Path) -> None:
        """Write a containers-auth.json file to the specified path."""
        auth_json = {
            "auths": {
                self.host: {
                    "auth": self._basic_auth(),
                },
            },
        }
        log.info("Writing Zot auth to %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump(auth_json, f)
            f.write("\n")

    def _basic_auth(self) -> str:
        return base64.b64encode(
            f"{self._config.zot_username}:{self._config.zot_password}".encode()
        ).decode()

    def _htpasswd_content(self) -> str:
        bcrypted_password = bcrypt.hashpw(
            self._config.zot_password.encode(), bcrypt.gensalt()
        ).decode()
        return f"{self._config.zot_username}:{bcrypted_password}"

    def _ssl_context(self) -> ssl.SSLContext:
        if self._config.ca_cert_path.exists():
            cafile = self._config.ca_cert_path
        else:
            cafile = None
        return ssl.create_default_context(cafile=cafile)


class _ZotConfig:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.root_dir_in_container = Path("/var/lib/zot")

    def zot_cert_path(self, *, in_container: bool = False) -> Path:
        return self._zot_path("zot.cert", in_container=in_container)

    def zot_key_path(self, *, in_container: bool = False) -> Path:
        return self._zot_path("zot.key", in_container=in_container)

    def zot_config_path(self, *, in_container: bool = False) -> Path:
        return self._zot_path("config.json", in_container=in_container)

    def zot_htpasswd_path(self, *, in_container: bool = False) -> Path:
        return self._zot_path("htpasswd", in_container=in_container)

    def _zot_path(self, filename: str, in_container: bool) -> Path:
        if in_container:
            return self.root_dir_in_container / filename
        else:
            return self.config.zot_root_dir / filename

    def zot_config(self) -> dict[str, Any]:
        # https://github.com/project-zot/zot/blob/432fde45affd66d2a42a0a578c822a23d828a8a9/build/stacker.yaml#L18-L44
        storage_root = self.root_dir_in_container / "registry"
        return {
            "storage": {
                # This is a path inside the zot container.
                # self.root_dir must get mounted in the container.
                "rootDirectory": storage_root.as_posix()
            },
            "http": {
                "address": "0.0.0.0",  # noqa: S104
                "port": self.config.zot_port,
                "compat": ["docker2s2"],
                # https://zotregistry.dev/v2.1.5/admin-guide/admin-configuration/#network-configuration
                "tls": {
                    "cert": self.zot_cert_path(in_container=True).as_posix(),
                    "key": self.zot_key_path(in_container=True).as_posix(),
                },
                # https://zotregistry.dev/v2.1.7/articles/authn-authz/#htpasswd
                "auth": {
                    "htpasswd": {
                        "path": self.zot_htpasswd_path(in_container=True).as_posix(),
                    }
                },
            },
            "log": {
                "level": "debug",
            },
            "extensions": {
                "search": {
                    "enable": True,
                    # "cve": {"updateInterval": "2h"},
                },
                "ui": {
                    "enable": True,
                },
                "mgmt": {
                    "enable": True,
                },
            },
        }


def _generate_ca_cert(ca_key_path: Path, ca_cert_path: Path) -> None:
    """Generate CA key+cert."""
    if ca_cert_path.exists():
        log.info("CA certificate already exists, re-using (%s)", ca_cert_path)
        return

    ca_key_path.parent.mkdir(parents=True, exist_ok=True)
    ca_cert_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Generating CA key and certificate (%s, %s)", ca_key_path, ca_cert_path)
    _run_openssl_cmd(["openssl", "genrsa", "-out", ca_key_path])
    _run_openssl_cmd(
        [
            "openssl",
            "req",
            "-x509",
            "-new",
            "-key",
            ca_key_path,
            "-out",
            ca_cert_path,
            "-days",
            "3650",
            "-subj",
            "/CN=localhost",
            "-addext",
            "basicConstraints=CA:TRUE",
        ]
    )


def _generate_cert_signed_by_own_ca(
    ca_key_path: Path,
    ca_cert_path: Path,
    cert_path: Path,
    key_path: Path,
) -> None:
    """Generate key+cert signed by our own CA."""
    if key_path.exists() and cert_path.exists():
        log.info(
            "Server key and certificate already exists, re-using (%s, %s)",
            key_path,
            cert_path,
        )
        return

    log.info(
        "Generating key and certificate signed by our CA (%s, %s)",
        key_path,
        cert_path,
    )
    _run_openssl_cmd(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            key_path,
            "-out",
            cert_path,
            "-CA",
            ca_cert_path,
            "-CAkey",
            ca_key_path,
            "-days",
            "3650",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ]
    )


def _run_openssl_cmd(cmd: list[str | os.PathLike[str]]) -> None:
    proc = subprocess.run(
        cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )
    if proc.returncode != 0:
        log.error(proc.stderr.rstrip())
    proc.check_returncode()
