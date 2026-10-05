from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.adapters.security.dependencies import require_roles
from app.entrypoints.api.schemas import DelegarOrdenRequest


def test_delegar_orden_acepta_destino() -> None:
    payload = DelegarOrdenRequest(
        id_orden=12,
        id_usuario_destino=4,
        observacion="Reasignar a bioquímica responsable.",
    )

    assert payload.id_orden == 12
    assert payload.id_usuario_destino == 4


def test_require_roles_permite_rol_autorizado() -> None:
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="ADMIN"))

    dependencia = require_roles(["ADMIN", "BIOQUIMICO"])

    assert dependencia(usuario) is usuario


def test_require_roles_rechaza_rol_no_autorizado() -> None:
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="ROL_NO_PERMITIDO"))
    dependencia = require_roles(["ADMIN", "BIOQUIMICO"])

    with pytest.raises(HTTPException) as exc_info:
        dependencia(usuario)
    assert exc_info.value.status_code == 403


def test_require_roles_nunca_autoriza_roles_heredados() -> None:
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="INTERNO"))

    with pytest.raises(HTTPException) as exc_info:
        require_roles(["INTERNO"])(usuario)
    assert exc_info.value.status_code == 403
