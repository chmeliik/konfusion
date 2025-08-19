from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Self


@dataclasses.dataclass(frozen=True, kw_only=True)
class Config:
    ca_key_path: Path
    ca_cert_path: Path
    zot_root_dir: Path
    zot_container_image: str
    zot_container_name: str
    zot_port: str
    zot_username: str
    zot_password: str
    konfusion_container_image: str | None
    clean_registry_storage: bool
    containers_auth_json_path: Path

    @classmethod
    def load_from_env(cls) -> Self:
        # Different directories for CA cert and CA key to make working with skopeo easier
        # (skopeo's --(src|dest)-cert-dir option expects a directory with only the CA cert)
        ca_cert_path = os.getenv("TEST_CA_CERT_PATH") or ".testdata/ca_cert/ca.crt"
        ca_key_path = os.getenv("TEST_CA_CERT_DIR") or ".testdata/ca_key/ca.key"

        zot_root_dir = os.getenv("TEST_ZOT_ROOT_DIR") or ".testdata/zot"
        zot_container_image = (
            os.getenv("TEST_ZOT_CONTAINER_IMAGE") or "ghcr.io/project-zot/zot:v2.1.5"
        )
        zot_container_name = (
            os.getenv("TEST_ZOT_CONTAINER_NAME") or "konfusion-zot-registry"
        )
        zot_port = os.getenv("TEST_ZOT_PORT") or "5000"
        zot_username = os.getenv("TEST_ZOT_USERNAME") or "konfusion"
        zot_password = os.getenv("TEST_ZOT_PASSWORD") or "confusion"

        konfusion_container_image = os.getenv("TEST_KONFUSION_CONTAINER_IMAGE")

        clean_registry_storage = (
            os.getenv("TEST_CLEAN_REGISTRY_STORAGE", "true").lower() != "false"
        )

        containers_auth_json_path = (
            os.getenv("TEST_CONTAINERS_AUTH_JSON_PATH")
            or ".testdata/containers-auth.json"
        )

        return cls(
            ca_key_path=Path(ca_key_path),
            ca_cert_path=Path(ca_cert_path),
            zot_root_dir=Path(zot_root_dir),
            zot_container_image=zot_container_image,
            zot_container_name=zot_container_name,
            zot_port=zot_port,
            zot_username=zot_username,
            zot_password=zot_password,
            konfusion_container_image=konfusion_container_image,
            clean_registry_storage=clean_registry_storage,
            containers_auth_json_path=Path(containers_auth_json_path),
        )
