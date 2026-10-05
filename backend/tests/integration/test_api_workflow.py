from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.adapters.persistence.models import (
    AuditoriaModel,
    EstudioModel,
    EstudioVersionModel,
    OrdenModel,
    PanelEstudioModel,
    PanelModel,
    ParametroModel,
    PapeleraOrdenModel,
    ResultadoValorModel,
    ResultadoVersionModel,
    RolModel,
    UsuarioModel,
)
from app.adapters.persistence.uow import SqlAlchemyUnitOfWork
from app.adapters.persistence.session import DATABASE_URL, get_db
from app.adapters.security.auth import pwd_context
from main import app


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, str, str, int, str, Session], None, None]:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    token_part = uuid4().hex
    role = session.scalar(select(RolModel).where(RolModel.nombre == "BIOQUIMICO"))
    admin_role = session.scalar(select(RolModel).where(RolModel.nombre == "ADMIN"))
    assert role is not None
    assert admin_role is not None
    author = UsuarioModel(
        id_rol=role.id_rol,
        ci=f"API-{token_part[:16]}",
        nombres="API",
        apellido_paterno="Autor",
        correo=f"author-{token_part}@example.test",
        hash_password=pwd_context.hash("password-api"),
        activo=True,
    )
    collaborator = UsuarioModel(
        id_rol=role.id_rol,
        ci=f"API-C-{token_part[:13]}",
        nombres="API",
        apellido_paterno="Colaborador",
        correo=f"collaborator-{token_part}@example.test",
        hash_password=pwd_context.hash("password-api"),
        activo=True,
    )
    admin = UsuarioModel(
        id_rol=admin_role.id_rol,
        ci=f"API-A-{token_part[:13]}",
        nombres="API",
        apellido_paterno="Administrador",
        correo=f"admin-{token_part}@example.test",
        hash_password=pwd_context.hash("password-api"),
        activo=True,
    )
    session.add_all([author, collaborator, admin])
    session.flush()
    collaborator_id = collaborator.id_usuario

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            author_login = client.post(
                "/auth/login",
                json={"usuario": author.ci, "password": "password-api"},
            )
            collaborator_login = client.post(
                "/auth/login",
                json={"usuario": collaborator.ci, "password": "password-api"},
            )
            admin_login = client.post(
                "/auth/login",
                json={"usuario": admin.ci, "password": "password-api"},
            )
            assert author_login.status_code == 200, author_login.text
            assert collaborator_login.status_code == 200, collaborator_login.text
            assert admin_login.status_code == 200, admin_login.text
            yield (
                client,
                author_login.json()["access_token"],
                collaborator_login.json()["access_token"],
                collaborator_id,
                admin_login.json()["access_token"],
                session,
            )
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_api_auth_patient_catalog_order_draft_delegation_audit_and_guards(api_client) -> None:
    client, author_token, collaborator_token, collaborator_id, _, _ = api_client
    author_headers = {"Authorization": f"Bearer {author_token}"}
    collaborator_headers = {"Authorization": f"Bearer {collaborator_token}"}

    me = client.get("/auth/me", headers=author_headers)
    assert me.status_code == 200
    assert me.json()["rol"] == "BIOQUIMICO"

    studies = client.get("/estudios", headers=author_headers)
    panels = client.get("/paneles", headers=author_headers)
    assert studies.status_code == 200 and len(studies.json()) == 4
    assert panels.status_code == 200 and len(panels.json()) == 2
    study = studies.json()[0]
    assert client.get(f"/paneles/{panels.json()[0]['id_panel']}/estudios", headers=author_headers).json() == []
    assert client.get(f"/paneles/{panels.json()[0]['id_panel']}", headers=author_headers).json()["id_panel"] == panels.json()[0]["id_panel"]

    patient_create = client.post(
        "/pacientes",
        headers=author_headers,
        json={
            "ci": f"PAT-{uuid4().hex[:12]}",
            "nombres": "Paciente API",
            "apellido_paterno": "Prueba",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "F",
        },
    )
    assert patient_create.status_code == 201, patient_create.text
    patient = patient_create.json()
    assert client.get(f"/pacientes/{patient['id_paciente']}", headers=author_headers).status_code == 200
    assert client.get("/pacientes", params={"q": patient["ci"]}, headers=author_headers).json()[0]["ci"] == patient["ci"]
    assert client.put(
        f"/pacientes/{patient['id_paciente']}",
        headers=author_headers,
        json={"telefono": "555-0101"},
    ).json()["telefono"] == "555-0101"

    empty_order = client.post(
        "/ordenes",
        headers=author_headers,
        json={"id_paciente": patient["id_paciente"], "ids_estudio": []},
    )
    assert empty_order.status_code == 422

    created_order = client.post(
        "/ordenes",
        headers=author_headers,
        json={"id_paciente": patient["id_paciente"], "ids_estudio": [study["id_estudio"]], "pieza": "Sala API"},
    )
    assert created_order.status_code == 201, created_order.text
    order = created_order.json()
    order_id = order["id_orden"]
    order_study_id = order["estudios"][0]["id_orden_estudio"]
    assert client.get("/ordenes", headers=author_headers).json()[0]["id_orden"] == order_id
    assert client.get(f"/ordenes/{order_id}", headers=author_headers).status_code == 200
    assert client.put(
        f"/ordenes/{order_id}/borrador",
        headers=author_headers,
        json={"comentario_general": "captura API"},
    ).json()["comentario_general"] == "captura API"
    assert len(client.get(f"/ordenes/{order_id}/estudios", headers=author_headers).json()) == 1

    saved = client.put(
        f"/ordenes/{order_id}/estudios/{study['id_estudio']}/resultado",
        headers=author_headers,
        json={"entradas": {}},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["id_resultado_version"] is not None
    assert client.get(
        f"/ordenes/{order_id}/estudios/{study['id_estudio']}", headers=author_headers
    ).status_code == 200
    assert client.get(f"/ordenes/{order_id}/versiones", headers=author_headers).status_code == 200

    # The seed has study shells but no parameter catalogue; calculations/publication must fail safely.
    assert client.post(
        f"/ordenes/{order_id}/estudios/{study['id_estudio']}/calcular",
        headers=author_headers,
    ).status_code == 422
    officialization = client.post(f"/ordenes/{order_id}/oficializar", headers=author_headers)
    assert officialization.status_code == 422, officialization.text
    assert client.get(f"/ordenes/{order_id}/pdf", headers=author_headers).status_code == 409

    delegated = client.post(
        f"/ordenes/{order_id}/delegaciones",
        headers=author_headers,
        json={"id_usuario_colaborador": collaborator_id, "modalidad": "TRABAJO_COMPLETO"},
    )
    assert delegated.status_code == 201, delegated.text
    delegation_id = delegated.json()["id_delegacion"]
    duplicate_delegation = client.post(
        f"/ordenes/{order_id}/delegaciones",
        headers=author_headers,
        json={"id_usuario_colaborador": collaborator_id, "modalidad": "TRABAJO_COMPLETO"},
    )
    assert duplicate_delegation.status_code == 409
    assert client.get("/ordenes", headers=collaborator_headers).json() == []
    assert client.post(f"/delegaciones/{delegation_id}/aceptar", headers=collaborator_headers).status_code == 200
    assert client.get("/ordenes", headers=collaborator_headers).json()[0]["id_orden"] == order_id
    assert client.post(f"/delegaciones/{delegation_id}/finalizar", headers=collaborator_headers).status_code == 200
    assert client.get(f"/ordenes/{order_id}", headers=collaborator_headers).status_code == 403

    assert client.get("/auditoria", headers=author_headers).status_code == 200
    order_audit = client.get(f"/auditoria/ordenes/{order_id}", headers=author_headers)
    assert order_audit.status_code == 200
    assert all(event["id_auditoria"] and event["creado_en"] for event in order_audit.json())
    assert all(
        event["entidad"] == "orden" and event["entidad_id"] == order_id
        for event in order_audit.json()
    )
    assert {
        event["accion"] for event in order_audit.json()
    } >= {"ORDEN_DELEGADA", "DELEGACION_ACEPTADA", "DELEGACION_FINALIZADA"}
    assert client.get("/papelera", headers=author_headers).json() == []
    assert client.post(
        f"/ordenes/{order_id}/papelera",
        headers=author_headers,
        json={"motivo": "Orden pendiente"},
    ).status_code == 409
    assert client.post(f"/papelera/{order_id}/restaurar", headers=author_headers).status_code == 409
    assert client.post("/auth/logout", headers=author_headers).status_code == 204


def test_api_role_authorization_and_delegated_study_access(api_client) -> None:
    client, author_token, collaborator_token, collaborator_id, admin_token, _ = api_client
    author_headers = {"Authorization": f"Bearer {author_token}"}
    collaborator_headers = {"Authorization": f"Bearer {collaborator_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    assert client.get("/pacientes", params={"q": "no-existe"}).status_code == 401
    assert client.post(
        "/api/analisis/calcular",
        json={"codigo_modulo": "HEPATOGRAMA", "entradas": {}},
    ).status_code == 401
    assert client.get("/ordenes").status_code == 401

    assert client.get("/admin/usuarios", headers=author_headers).status_code == 403
    assert client.get("/pacientes", params={"q": "no-existe"}, headers=admin_headers).status_code == 403
    assert client.get("/estudios", headers=admin_headers).status_code == 403
    assert client.get("/ordenes", headers=admin_headers).status_code == 403
    assert client.post(
        "/api/analisis/calcular",
        headers=admin_headers,
        json={"codigo_modulo": "HEPATOGRAMA", "entradas": {}},
    ).status_code == 403
    assert client.get("/auditoria", headers=admin_headers).status_code == 200

    studies = client.get("/estudios", headers=author_headers).json()
    patient_response = client.post(
        "/pacientes",
        headers=author_headers,
        json={
            "ci": f"AUTH-{uuid4().hex[:12]}",
            "nombres": "Prueba",
            "apellido_paterno": "Autorización",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "F",
        },
    )
    assert patient_response.status_code == 201, patient_response.text
    order_response = client.post(
        "/ordenes",
        headers=author_headers,
        json={
            "id_paciente": patient_response.json()["id_paciente"],
            "ids_estudio": [studies[0]["id_estudio"], studies[1]["id_estudio"]],
        },
    )
    assert order_response.status_code == 201, order_response.text
    order_id = order_response.json()["id_orden"]
    assigned_study_id = studies[0]["id_estudio"]
    unassigned_to_collaborator_id = studies[1]["id_estudio"]

    assert client.get(f"/ordenes/{order_id}", headers=admin_headers).status_code == 403
    assert client.post(f"/ordenes/{order_id}/oficializar", headers=admin_headers).status_code == 403
    assert client.get(f"/auditoria/ordenes/{order_id}", headers=admin_headers).status_code == 200

    delegation_response = client.post(
        f"/ordenes/{order_id}/delegaciones",
        headers=author_headers,
        json={
            "id_usuario_colaborador": collaborator_id,
            "modalidad": "POR_ESTUDIO",
            "ids_estudio": [assigned_study_id],
        },
    )
    assert delegation_response.status_code == 201, delegation_response.text
    assert delegation_response.json()["estudios"] == [assigned_study_id]
    delegation_id = delegation_response.json()["id_delegacion"]
    assert client.post(f"/delegaciones/{delegation_id}/aceptar", headers=author_headers).status_code == 403
    accepted = client.post(f"/delegaciones/{delegation_id}/aceptar", headers=collaborator_headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["estudios"] == [assigned_study_id]
    collaborator_orders = client.get("/ordenes", headers=collaborator_headers)
    assert collaborator_orders.status_code == 200, collaborator_orders.text
    assert [study["id_estudio"] for study in collaborator_orders.json()[0]["estudios"]] == [assigned_study_id]
    collaborator_order = client.get(f"/ordenes/{order_id}", headers=collaborator_headers)
    assert collaborator_order.status_code == 200, collaborator_order.text
    assert [study["id_estudio"] for study in collaborator_order.json()["estudios"]] == [assigned_study_id]
    collaborator_studies = client.get(f"/ordenes/{order_id}/estudios", headers=collaborator_headers)
    assert collaborator_studies.status_code == 200, collaborator_studies.text
    assert [study["id_estudio"] for study in collaborator_studies.json()] == [assigned_study_id]

    allowed_result = client.put(
        f"/ordenes/{order_id}/estudios/{assigned_study_id}/resultado",
        headers=collaborator_headers,
        json={"entradas": {}},
    )
    assert allowed_result.status_code == 200, allowed_result.text
    denied_result = client.put(
        f"/ordenes/{order_id}/estudios/{unassigned_to_collaborator_id}/resultado",
        headers=collaborator_headers,
        json={"entradas": {}},
    )
    assert denied_result.status_code == 403, denied_result.text
    assert client.post(f"/ordenes/{order_id}/oficializar", headers=collaborator_headers).status_code == 403
    assert client.post(f"/delegaciones/{delegation_id}/finalizar", headers=collaborator_headers).status_code == 200
    assert client.put(
        f"/ordenes/{order_id}/estudios/{assigned_study_id}/resultado",
        headers=collaborator_headers,
        json={"entradas": {}},
    ).status_code == 403
    order_audit = client.get(f"/auditoria/ordenes/{order_id}", headers=author_headers)
    assert order_audit.status_code == 200
    assert {
        event["accion"] for event in order_audit.json()
    } >= {"ESTUDIOS_DELEGADOS", "DELEGACION_ACEPTADA", "DELEGACION_FINALIZADA"}


def test_panel_and_manual_study_selection_create_deduplicated_order(api_client) -> None:
    client, author_token, _, _, _, session = api_client
    headers = {"Authorization": f"Bearer {author_token}"}
    panel = session.scalar(select(PanelModel).where(PanelModel.activo.is_(True)).order_by(PanelModel.id_panel))
    studies = session.scalars(
        select(EstudioModel).where(EstudioModel.activo.is_(True)).order_by(EstudioModel.id_estudio)
    ).all()
    assert panel is not None and len(studies) >= 2

    association = session.get(PanelEstudioModel, (panel.id_panel, studies[0].id_estudio))
    if association is None:
        association = PanelEstudioModel(
            id_panel=panel.id_panel,
            id_estudio=studies[0].id_estudio,
            orden_visualizacion=1,
        )
        session.add(association)
        session.flush()

    panel_response = client.get(f"/paneles/{panel.id_panel}", headers=headers)
    assert panel_response.status_code == 200, panel_response.text
    panel_studies = client.get(f"/paneles/{panel.id_panel}/estudios", headers=headers)
    assert panel_studies.status_code == 200, panel_studies.text
    auto_selected = [study["id_estudio"] for study in panel_studies.json()]
    assert auto_selected == [studies[0].id_estudio]
    selected_ids = auto_selected + [studies[1].id_estudio, auto_selected[0]]

    patient_response = client.post(
        "/pacientes",
        headers=headers,
        json={
            "ci": f"PANEL-{uuid4().hex[:12]}",
            "nombres": "Paciente",
            "apellido_paterno": "Panel",
            "fecha_nacimiento": "1988-06-15",
            "sexo": "F",
        },
    )
    assert patient_response.status_code == 201, patient_response.text
    order_response = client.post(
        "/ordenes",
        headers=headers,
        json={
            "id_paciente": patient_response.json()["id_paciente"],
            "ids_estudio": selected_ids,
        },
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    assert order["folio"].startswith("LIS-")
    assert {study["id_estudio"] for study in order["estudios"]} == {
        studies[0].id_estudio,
        studies[1].id_estudio,
    }
    assert len(order["estudios"]) == 2

    empty_order = client.post(
        "/ordenes",
        headers=headers,
        json={"id_paciente": patient_response.json()["id_paciente"], "ids_estudio": []},
    )
    assert empty_order.status_code == 422


def test_api_official_result_correction_preserves_v1_and_records_comparison(api_client) -> None:
    client, author_token, collaborator_token, _, _, session = api_client
    headers = {"Authorization": f"Bearer {author_token}"}
    collaborator_headers = {"Authorization": f"Bearer {collaborator_token}"}
    token_part = uuid4().hex
    study = EstudioModel(codigo=f"TEST-{token_part[:12]}", nombre="Estudio de prueba de versionado")
    session.add(study)
    session.flush()
    configuration = EstudioVersionModel(
        id_estudio=study.id_estudio,
        numero_version=1,
        configuracion={},
        activa=True,
    )
    session.add(configuration)
    session.flush()
    parameter = ParametroModel(
        id_estudio_version=configuration.id_estudio_version,
        codigo="valor",
        nombre="Valor de prueba",
        tipo_campo="ENTRADA_MANUAL",
        tipo_dato="DECIMAL",
        obligatorio=True,
    )
    session.add(parameter)
    session.flush()

    patient_response = client.post(
        "/pacientes",
        headers=headers,
        json={
            "ci": f"VERSION-{token_part[:12]}",
            "nombres": "Paciente",
            "apellido_paterno": "Versionado",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "F",
        },
    )
    assert patient_response.status_code == 201, patient_response.text
    order_response = client.post(
        "/ordenes",
        headers=headers,
        json={
            "id_paciente": patient_response.json()["id_paciente"],
            "ids_estudio": [study.id_estudio],
        },
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    order_id = order["id_orden"]
    assigned_study_id = order["estudios"][0]["id_orden_estudio"]
    study_id = study.id_estudio

    first_draft = client.put(
        f"/ordenes/{order_id}/estudios/{study_id}/resultado",
        headers=headers,
        json={"entradas": {"valor": 1.25}},
    )
    assert first_draft.status_code == 200, first_draft.text
    first_official = client.post(f"/ordenes/{order_id}/oficializar", headers=headers)
    assert first_official.status_code == 200, first_official.text
    versions_before = client.get(f"/ordenes/{order_id}/versiones", headers=headers)
    assert versions_before.status_code == 200, versions_before.text
    version_one = next(
        item for item in versions_before.json()
        if item["id_orden_estudio"] == assigned_study_id and item["numero_version"] == 1
    )
    assert version_one["estado"] == "OFICIAL"
    assert version_one["entradas"] == {"valor": "1.250000"}

    persisted_v1 = session.scalar(
        select(ResultadoVersionModel).where(
            ResultadoVersionModel.id_resultado_version == version_one["id_resultado_version"]
        )
    )
    assert persisted_v1 is not None
    persisted_value_v1 = session.scalar(
        select(ResultadoValorModel).where(
            ResultadoValorModel.id_resultado_version == version_one["id_resultado_version"],
            ResultadoValorModel.id_parametro == parameter.id_parametro,
        )
    )
    assert persisted_value_v1 is not None
    original_snapshot = dict(persisted_v1.snapshot_completo)
    original_value = persisted_value_v1.valor_numerico

    immutable_copy = SqlAlchemyUnitOfWork(session).results.get_latest(assigned_study_id)
    assert immutable_copy is not None
    immutable_copy.entradas["valor"] = 99
    with pytest.raises(ValueError, match="inmutable|alterar"):
        SqlAlchemyUnitOfWork(session).results.save(immutable_copy)

    correction = client.post(
        f"/ordenes/{order_id}/correcciones",
        headers=headers,
        json={
            "id_orden_estudio": assigned_study_id,
            "motivo": "Corrección de transcripción de prueba.",
            "nuevas_entradas": {"valor": 2.5},
        },
    )
    assert correction.status_code == 201, correction.text
    assert correction.json()["numero_version"] == 2
    assert correction.json()["creado_por"] is not None
    assert correction.json()["motivo_correccion"] == "Corrección de transcripción de prueba."
    assert client.post(f"/ordenes/{order_id}/oficializar", headers=headers).status_code == 200

    versions_after = client.get(f"/ordenes/{order_id}/versiones", headers=headers)
    assert versions_after.status_code == 200, versions_after.text
    order_versions = [
        item for item in versions_after.json()
        if item["id_orden_estudio"] == assigned_study_id
    ]
    version_one_after = next(item for item in order_versions if item["numero_version"] == 1)
    version_two = next(item for item in order_versions if item["numero_version"] == 2)
    assert version_one_after["estado"] == "SUPERADA"
    assert version_one_after["entradas"] == {"valor": "1.250000"}
    assert version_two["estado"] == "OFICIAL"
    assert version_two["entradas"] == {"valor": "2.500000"}

    changes = client.get(f"/ordenes/{order_id}/cambios", headers=headers)
    assert changes.status_code == 200, changes.text
    comparison = next(change for change in changes.json() if change["codigo_parametro"] == "valor")
    assert comparison["id_orden_estudio"] == assigned_study_id
    assert comparison["numero_version"] == 2
    assert comparison["valor_anterior"] == "1.250000"
    assert comparison["valor_nuevo"] == "2.5"
    assert comparison["id_usuario"] == order["id_usuario_autor"]
    assert comparison["creado_en"] is not None
    assert comparison["comentario"] == "Corrección de transcripción de prueba."

    session.expire_all()
    persisted_v1_after = session.get(ResultadoVersionModel, version_one["id_resultado_version"])
    persisted_value_v1_after = session.scalar(
        select(ResultadoValorModel).where(
            ResultadoValorModel.id_resultado_version == version_one["id_resultado_version"],
            ResultadoValorModel.id_parametro == parameter.id_parametro,
        )
    )
    assert persisted_v1_after is not None
    assert persisted_value_v1_after is not None
    assert persisted_v1_after.snapshot_completo == original_snapshot
    assert persisted_value_v1_after.valor_numerico == original_value

    # La papelera es un cambio de estado reversible, no un DELETE de la orden oficial.
    assert client.post(
        f"/ordenes/{order_id}/papelera",
        headers=collaborator_headers,
        json={"motivo": "Retiro no autorizado."},
    ).status_code == 403
    trashed = client.post(
        f"/ordenes/{order_id}/papelera",
        headers=headers,
        json={"motivo": "Corrección administrativa documentada."},
    )
    assert trashed.status_code == 200, trashed.text
    assert trashed.json()["estado"] == "PAPELERA"
    assert trashed.json()["eliminado_por"] == order["id_usuario_autor"]
    assert trashed.json()["eliminado_en"] is not None

    session.expire_all()
    persisted_order = session.get(OrdenModel, order_id)
    paper = session.scalar(select(PapeleraOrdenModel).where(PapeleraOrdenModel.id_orden == order_id))
    assert persisted_order is not None and persisted_order.estado == "PAPELERA"
    assert paper is not None
    assert paper.eliminado_por == order["id_usuario_autor"]
    assert paper.estado_anterior == "OFICIAL"
    assert paper.motivo == "Corrección administrativa documentada."
    assert paper.restaurado is False
    assert [item["id_orden"] for item in client.get("/papelera", headers=headers).json()] == [order_id]

    restored = client.post(f"/papelera/{order_id}/restaurar", headers=headers)
    assert restored.status_code == 200, restored.text
    assert restored.json()["estado"] == "OFICIAL"
    assert client.get("/papelera", headers=headers).json() == []

    session.expire_all()
    persisted_order = session.get(OrdenModel, order_id)
    paper = session.scalar(select(PapeleraOrdenModel).where(PapeleraOrdenModel.id_orden == order_id))
    assert persisted_order is not None and persisted_order.estado == "OFICIAL"
    assert paper is not None and paper.restaurado is True
    assert paper.restaurado_por == order["id_usuario_autor"]
    assert paper.restaurado_en is not None
    assert {
        event.accion
        for event in session.scalars(
            select(AuditoriaModel).where(AuditoriaModel.id_orden == order_id)
        )
    } >= {"ORDEN_A_PAPELERA", "ORDEN_RESTAURADA"}


def test_security_audit_is_separate_and_tracks_authentication_and_admin_changes(api_client) -> None:
    client, author_token, collaborator_token, _, admin_token, _ = api_client
    author_headers = {"Authorization": f"Bearer {author_token}"}
    collaborator_headers = {"Authorization": f"Bearer {collaborator_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    author = client.get("/auth/me", headers=author_headers)
    admin = client.get("/auth/me", headers=admin_headers)
    assert author.status_code == 200 and admin.status_code == 200
    author_id = author.json()["id_usuario"]
    assert client.post(
        "/auth/login",
        json={"usuario": f"NO-USER-{uuid4().hex[:8]}", "password": "wrong-password"},
    ).status_code == 401
    assert client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    ).status_code == 401
    assert client.post("/auth/logout", headers=author_headers).status_code == 204

    password_change = client.put(
        f"/admin/usuarios/{author_id}/reset-password",
        headers=admin_headers,
        json={"nueva_password": "new-password"},
    )
    assert password_change.status_code == 200, password_change.text
    deactivation = client.put(
        f"/admin/usuarios/{author_id}",
        headers=admin_headers,
        json={"activo": False},
    )
    assert deactivation.status_code == 200, deactivation.text
    assert client.post(
        "/auth/login",
        json={"usuario": author.json()["ci"], "password": "new-password"},
    ).status_code == 403

    security_audit = client.get("/admin/auditoria/seguridad", headers=admin_headers)
    assert security_audit.status_code == 200, security_audit.text
    events = security_audit.json()
    event_names = {event["evento"] for event in events}
    assert {
        "LOGIN_EXITOSO",
        "LOGIN_FALLIDO",
        "TOKEN_INVALIDO",
        "LOGOUT",
        "CAMBIO_CREDENCIALES",
        "USUARIO_DESACTIVADO",
    } <= event_names
    assert all(event["id_evento"] and event["creado_en"] for event in events)
    assert client.get(
        "/admin/auditoria/seguridad",
        headers=collaborator_headers,
    ).status_code == 403

    clinical_audit = client.get("/auditoria", headers=admin_headers)
    assert clinical_audit.status_code == 200, clinical_audit.text
    assert all("evento" not in event for event in clinical_audit.json())
