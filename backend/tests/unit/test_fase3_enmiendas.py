from types import SimpleNamespace

import pytest

from app.adapters.security.dependencies import require_roles
from app.entrypoints.api.schemas import DelegarOrdenRequest, SolicitudEnmiendaRequest


def test_solicitud_enmienda_requiere_motivo_clinico() -> None:
    payload = SolicitudEnmiendaRequest(
        id_resultado=10,
        motivo_justificativo="Se corrigió el valor por ajuste clínico de la muestra.",
        nuevos_valores_entrada={"hematocrito": 45, "globulos_blancos": 7600},
    )

    assert payload.id_resultado == 10
    assert "ajuste clínico" in payload.motivo_justificativo.lower()


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
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="INTERNO"))
    dependencia = require_roles(["ADMIN", "BIOQUIMICO"])

    with pytest.raises(Exception):
        dependencia(usuario)
