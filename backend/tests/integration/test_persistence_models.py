import os
from datetime import date
from uuid import uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, inspect, select
from sqlalchemy.orm import Session, configure_mappers

from app.adapters.persistence.models import (
    AuditoriaModel,
    AuditoriaSeguridadModel,
    Base,
    CambioResultadoModel,
    DelegacionEstudioModel,
    DelegacionModel,
    EstudioModel,
    EstudioVersionModel,
    OrdenEstudioModel,
    OrdenModel,
    PacienteModel,
    PanelEstudioModel,
    PanelModel,
    ParametroModel,
    PapeleraOrdenModel,
    RangoReferenciaModel,
    ResultadoValorModel,
    ResultadoVersionModel,
    RolModel,
    UsuarioModel,
)
from app.adapters.persistence.repositories import (
    AuditoriaRepository,
    DelegacionRepository,
    EstudioRepository,
    OrdenRepository,
    PacienteRepository,
    ResultadoRepository,
    UsuarioRepository,
)


def test_all_relational_models_match_database_columns_and_foreign_keys() -> None:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgrespassword@localhost:5432/lis_hospital",
    )
    engine = create_engine(database_url)
    inspector = inspect(engine)
    configure_mappers()

    assert len(Base.metadata.tables) == 19
    for key, model_table in Base.metadata.tables.items():
        schema, table_name = key.split(".", maxsplit=1)
        reflected_columns = inspector.get_columns(table_name, schema=schema)
        database_columns = {column["name"] for column in reflected_columns}
        assert set(model_table.columns.keys()) == database_columns, table_name
        for column in reflected_columns:
            mapped_column = model_table.columns[column["name"]]
            assert mapped_column.nullable == column["nullable"], (
                table_name,
                column["name"],
            )
            assert mapped_column.type.compile(dialect=engine.dialect) == column["type"].compile(
                dialect=engine.dialect
            ), (table_name, column["name"])
        assert inspector.get_pk_constraint(table_name, schema=schema)["constrained_columns"] == [
            column.name for column in model_table.primary_key.columns
        ], table_name
        mapped_foreign_keys = {
            (
                tuple(element.parent.name for element in constraint.elements),
                tuple(element.column.name for element in constraint.elements),
                constraint.elements[0].column.table.schema,
                constraint.elements[0].column.table.name,
                (constraint.elements[0].ondelete or "").upper(),
            )
            for constraint in model_table.foreign_key_constraints
        }
        database_foreign_keys = {
            (
                tuple(foreign_key["constrained_columns"]),
                tuple(foreign_key["referred_columns"]),
                foreign_key["referred_schema"],
                foreign_key["referred_table"],
                (foreign_key.get("options", {}).get("ondelete") or "").upper(),
            )
            for foreign_key in inspector.get_foreign_keys(table_name, schema=schema)
        }
        assert mapped_foreign_keys == database_foreign_keys, table_name
        assert len(inspector.get_unique_constraints(table_name, schema=schema)) == sum(
            isinstance(item, UniqueConstraint) for item in model_table.constraints
        ), table_name
        assert len(inspector.get_check_constraints(table_name, schema=schema)) == sum(
            isinstance(item, CheckConstraint) for item in model_table.constraints
        ), table_name
        actual_index_names = {
            item["name"] for item in inspector.get_indexes(table_name, schema=schema)
        }
        assert {index.name for index in model_table.indexes} <= actual_index_names, table_name

    orders = Base.metadata.tables["laboratorio.ordenes"]
    assert "pieza" in orders.columns
    assert "pieza_cama" not in orders.columns


def test_models_persist_relationships_and_repositories_query_them() -> None:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgrespassword@localhost:5432/lis_hospital",
    )
    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    token = uuid4().hex

    try:
        role = session.scalar(select(RolModel).where(RolModel.nombre == "BIOQUIMICO"))
        assert role is not None
        author = UsuarioModel(
            id_rol=role.id_rol,
            ci=f"PERSIST-{token[:12]}",
            nombres="Persistencia",
            apellido_paterno="Autor",
            correo=f"author-{token}@example.test",
            hash_password="test-hash",
        )
        collaborator = UsuarioModel(
            id_rol=role.id_rol,
            ci=f"PERSIST-C-{token[:10]}",
            nombres="Persistencia",
            apellido_paterno="Colaborador",
            correo=f"collaborator-{token}@example.test",
            hash_password="test-hash",
        )
        patient = PacienteModel(
            ci=f"PAT-{token[:12]}",
            nombres="Paciente",
            apellido_paterno="Prueba",
            fecha_nacimiento=date(2000, 1, 1),
            sexo="F",
        )
        panel = PanelModel(codigo=f"PANEL-{token[:12]}", nombre="Panel integración")
        study = EstudioModel(codigo=f"STUDY-{token[:12]}", nombre="Estudio integración")
        session.add_all([author, collaborator, patient, panel, study])
        session.flush()

        patient.creado_por = author.id_usuario
        study_version = EstudioVersionModel(
            id_estudio=study.id_estudio,
            numero_version=1,
            creado_por=author.id_usuario,
        )
        panel_study = PanelEstudioModel(
            id_panel=panel.id_panel,
            id_estudio=study.id_estudio,
            orden_visualizacion=1,
        )
        parameter = ParametroModel(
            id_estudio_version=study_version.id_estudio_version,
            codigo="valor_prueba",
            nombre="Valor de prueba",
            tipo_campo="ENTRADA_MANUAL",
        )
        session.add_all([study_version, panel_study])
        session.flush()
        parameter.id_estudio_version = study_version.id_estudio_version
        order = OrdenModel(
            folio=f"T-{token[:28]}",
            paciente=patient,
            autor=author,
            pieza="Sala 1",
            estado="BORRADOR",
        )
        session.add_all([parameter, order])
        session.flush()
        reference = RangoReferenciaModel(
            id_parametro=parameter.id_parametro,
            sexo="F",
            limite_inferior=1,
            limite_superior=10,
        )
        session.add(reference)

        order_study = OrdenEstudioModel(
            id_orden=order.id_orden,
            id_estudio=study.id_estudio,
            id_estudio_version=study_version.id_estudio_version,
            estado="BORRADOR",
        )
        session.add(order_study)
        session.flush()

        result_version = ResultadoVersionModel(
            id_orden_estudio=order_study.id_orden_estudio,
            numero_version=1,
            id_estudio_version=study_version.id_estudio_version,
            creado_por=author.id_usuario,
            snapshot_completo={"version_config": 1},
        )
        session.add(result_version)
        session.flush()

        result_value = ResultadoValorModel(
            id_resultado_version=result_version.id_resultado_version,
            id_parametro=parameter.id_parametro,
            valor_numerico=5,
            unidad_utilizada="mg/dL",
            referencia_utilizada="1-10 mg/dL",
        )
        delegation = DelegacionModel(
            id_orden=order.id_orden,
            id_usuario_autor=author.id_usuario,
            id_usuario_colaborador=collaborator.id_usuario,
            modalidad="POR_ESTUDIO",
        )
        session.add_all([result_value, delegation])
        session.flush()
        session.add(DelegacionEstudioModel(
            id_delegacion=delegation.id_delegacion,
            id_orden_estudio=order_study.id_orden_estudio,
        ))

        session.add_all([
            AuditoriaModel(
                id_usuario=author.id_usuario,
                id_orden=order.id_orden,
                accion="TEST_PERSISTENCIA",
                entidad="orden",
            ),
            CambioResultadoModel(
                id_resultado_version=result_version.id_resultado_version,
                id_parametro=parameter.id_parametro,
                id_usuario=author.id_usuario,
                valor_anterior="4",
                valor_nuevo="5",
                comentario="Prueba de persistencia",
            ),
            PapeleraOrdenModel(
                id_orden=order.id_orden,
                eliminado_por=author.id_usuario,
                estado_anterior="OFICIAL",
                motivo="Prueba reversible",
            ),
            AuditoriaSeguridadModel(
                id_usuario=author.id_usuario,
                evento="TEST_PERSISTENCIA",
            ),
        ])
        session.flush()

        assert PacienteRepository(session).get_by_ci(patient.ci).creador.id_usuario == author.id_usuario
        assert UsuarioRepository(session).get_by_identifier(author.ci).rol.nombre == "BIOQUIMICO"
        assert EstudioRepository(session).list_for_panel(panel.id_panel)[0].codigo == study.codigo
        assert OrdenRepository(session).get_by_id(order.id_orden).estudios[0].estudio.nombre == study.nombre
        assert ResultadoRepository(session).list_versions(order_study.id_orden_estudio)[0].valores[0].valor_numerico == 5
        assert DelegacionRepository(session).get_active_for_order(order.id_orden).estudios[0].id_orden_estudio == order_study.id_orden_estudio
        assert AuditoriaRepository(session).list_for_order(order.id_orden)[0].accion == "TEST_PERSISTENCIA"
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()