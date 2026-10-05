from __future__ import annotations

from ipaddress import ip_address
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, cast, func, or_, select, String, text
from sqlalchemy.orm import Session, selectinload

from app.application.ports import UnitOfWork
from app.domain.entities import (
    AuditEvent,
    Delegation,
    DelegationMode,
    HistoryFilter,
    Order,
    OrderStatus,
    OrderStudy,
    OrderStudyStatus,
    PanelDefinition,
    Patient,
    ResultChange,
    ResultStatus,
    ResultVersion,
    StudyDefinition,
    Value,
)
from app.adapters.persistence.models import (
    AuditoriaModel,
    AuditoriaSeguridadModel,
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
    folio_sequence,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return value


def _patient_domain(model: PacienteModel) -> Patient:
    return Patient(
        id_paciente=model.id_paciente,
        ci=model.ci,
        nombres=model.nombres,
        apellido_paterno=model.apellido_paterno,
        apellido_materno=model.apellido_materno,
        fecha_nacimiento=model.fecha_nacimiento,
        sexo=model.sexo,
        telefono=model.telefono,
        correo=model.correo,
        creado_por=model.creado_por,
        creado_en=model.creado_en,
        eliminado=model.eliminado_en is not None,
    )


def _reference_text(ranges: list[RangoReferenciaModel]) -> str:
    parts: list[str] = []
    for item in ranges:
        if item.referencia_texto:
            reference = item.referencia_texto
        else:
            lower = "" if item.limite_inferior is None else str(item.limite_inferior)
            upper = "" if item.limite_superior is None else str(item.limite_superior)
            reference = f"{lower}-{upper}"
        qualifiers = [f"sexo={item.sexo}"] if item.sexo else []
        if item.edad_minima is not None or item.edad_maxima is not None:
            qualifiers.append(f"edad={item.edad_minima or 0}-{item.edad_maxima or '∞'}")
        if item.unidad:
            reference = f"{reference} {item.unidad}"
        if qualifiers:
            reference = f"{' '.join(qualifiers)}: {reference}"
        parts.append(reference)
    return " | ".join(parts)


def _study_definition(version: EstudioVersionModel) -> StudyDefinition:
    study = version.estudio
    parameters = list(version.parametros)
    required = tuple(parameter.codigo for parameter in parameters if parameter.obligatorio and parameter.activo)
    parameter_ids = {parameter.codigo: parameter.id_parametro for parameter in parameters}
    units = {parameter.codigo: parameter.unidad_medida for parameter in parameters if parameter.unidad_medida}
    references = {
        parameter.codigo: _reference_text(list(parameter.rangos_referencia))
        for parameter in parameters
        if parameter.rangos_referencia
    }
    configuration = {
        "configuracion": version.configuracion or {},
        "parametros": [
            {
                "codigo": parameter.codigo,
                "nombre": parameter.nombre,
                "tipo_campo": parameter.tipo_campo,
                "tipo_dato": parameter.tipo_dato,
                "unidad_medida": parameter.unidad_medida,
                "formula_codigo": parameter.formula_codigo,
                "obligatorio": parameter.obligatorio,
                "orden_visualizacion": parameter.orden_visualizacion,
                "referencias": [
                    {
                        "sexo": reference.sexo,
                        "edad_minima": reference.edad_minima,
                        "edad_maxima": reference.edad_maxima,
                        "unidad": reference.unidad,
                        "limite_inferior": reference.limite_inferior,
                        "limite_superior": reference.limite_superior,
                        "referencia_texto": reference.referencia_texto,
                    }
                    for reference in parameter.rangos_referencia
                ],
            }
            for parameter in parameters
        ],
    }
    return StudyDefinition(
        id_estudio=study.id_estudio,
        codigo=study.codigo,
        nombre=study.nombre,
        id_estudio_version=version.id_estudio_version,
        numero_version=version.numero_version,
        estrategia_calculo=study.estrategia_calculo,
        parametros_obligatorios=required,
        parameter_ids=parameter_ids,
        unidades=units,
        referencias=references,
        configuracion=configuration,
    )


def _result_domain(model: ResultadoVersionModel) -> ResultVersion:
    inputs: dict[str, Value] = {}
    calculated: dict[str, Value] = {}
    for row in model.valores:
        code = row.parametro.codigo
        if row.valor_numerico is not None:
            value: Value = row.valor_numerico
        elif row.valor_booleano is not None:
            value = row.valor_booleano
        else:
            value = row.valor_texto
        if row.valor_calculado:
            calculated[code] = value
        else:
            inputs[code] = value
    snapshot = model.snapshot_completo or {}
    if not inputs and isinstance(snapshot.get("entradas"), dict):
        inputs = dict(snapshot["entradas"])
    if not calculated and isinstance(snapshot.get("calculados"), dict):
        calculated = dict(snapshot["calculados"])
    return ResultVersion(
        id_orden_estudio=model.id_orden_estudio,
        numero_version=model.numero_version,
        id_estudio_version=model.id_estudio_version,
        creado_por=model.creado_por,
        entradas=inputs,
        calculados=calculated,
        advertencias=list(snapshot.get("advertencias", [])),
        motivo_correccion=model.motivo_correccion,
        estado=ResultStatus(model.estado),
        id_resultado_version=model.id_resultado_version,
        creado_en=model.creado_en,
        oficializado_en=model.oficializado_en,
        comentario_estudio=model.comentario_estudio,
        snapshot_completo=snapshot,
    )


class _Patients:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, id_paciente: int) -> Patient | None:
        model = self.session.get(PacienteModel, id_paciente)
        return _patient_domain(model) if model else None

    def get_by_ci(self, ci: str) -> Patient | None:
        model = self.session.scalar(
            select(PacienteModel).where(PacienteModel.ci == ci, PacienteModel.eliminado_en.is_(None))
        )
        return _patient_domain(model) if model else None

    def search(self, query: str, limit: int = 50) -> list[Patient]:
        term = f"%{query.strip()}%"
        statement = (
            select(PacienteModel)
            .where(
                PacienteModel.eliminado_en.is_(None),
                or_(
                    PacienteModel.ci.ilike(term),
                    PacienteModel.nombres.ilike(term),
                    PacienteModel.apellido_paterno.ilike(term),
                    PacienteModel.apellido_materno.ilike(term),
                ),
            )
            .order_by(PacienteModel.apellido_paterno, PacienteModel.nombres)
            .limit(limit)
        )
        return [_patient_domain(item) for item in self.session.scalars(statement)]

    def add(self, patient: Patient) -> Patient:
        model = PacienteModel(
            ci=patient.ci,
            nombres=patient.nombres,
            apellido_paterno=patient.apellido_paterno,
            apellido_materno=patient.apellido_materno,
            fecha_nacimiento=patient.fecha_nacimiento,
            sexo=patient.sexo,
            telefono=patient.telefono,
            correo=patient.correo,
            creado_por=patient.creado_por,
        )
        self.session.add(model)
        self.session.flush()
        patient.id_paciente = model.id_paciente
        return patient

    def save(self, patient: Patient) -> Patient:
        model = self.session.get(PacienteModel, patient.id_paciente)
        if model is None:
            raise ValueError("El paciente ya no existe.")
        for field in (
            "ci", "nombres", "apellido_paterno", "apellido_materno", "fecha_nacimiento",
            "sexo", "telefono", "correo",
        ):
            setattr(model, field, getattr(patient, field))
        self.session.flush()
        return _patient_domain(model)


class _Users:
    def __init__(self, session: Session) -> None:
        self.session = session

    def exists_active_bioquimico(self, id_usuario: int) -> bool:
        return self._exists_active_role(id_usuario, "BIOQUIMICO")

    def exists_active_admin(self, id_usuario: int) -> bool:
        return self._exists_active_role(id_usuario, "ADMIN")

    def _exists_active_role(self, id_usuario: int, role_name: str) -> bool:
        statement = (
            select(func.count())
            .select_from(UsuarioModel)
            .join(RolModel, UsuarioModel.id_rol == RolModel.id_rol)
            .where(
                UsuarioModel.id_usuario == id_usuario,
                UsuarioModel.activo.is_(True),
                UsuarioModel.eliminado_en.is_(None),
                RolModel.nombre == role_name,
            )
        )
        return bool(self.session.scalar(statement))


class _Studies:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _versions_query(self):
        return select(EstudioVersionModel).options(
            selectinload(EstudioVersionModel.estudio),
            selectinload(EstudioVersionModel.parametros).selectinload(ParametroModel.rangos_referencia),
        )

    def get_active(self, id_estudio: int) -> StudyDefinition | None:
        statement = (
            self._versions_query()
            .join(EstudioModel, EstudioModel.id_estudio == EstudioVersionModel.id_estudio)
            .where(
                EstudioModel.id_estudio == id_estudio,
                EstudioModel.activo.is_(True),
                EstudioVersionModel.activa.is_(True),
            )
            .order_by(EstudioVersionModel.numero_version.desc())
            .limit(1)
        )
        version = self.session.scalar(statement)
        return _study_definition(version) if version else None

    def get_version(self, id_estudio_version: int) -> StudyDefinition | None:
        version = self.session.scalar(
            self._versions_query().where(EstudioVersionModel.id_estudio_version == id_estudio_version)
        )
        return _study_definition(version) if version else None

    def list_active(self) -> list[StudyDefinition]:
        statement = (
            self._versions_query()
            .join(EstudioModel, EstudioModel.id_estudio == EstudioVersionModel.id_estudio)
            .where(EstudioModel.activo.is_(True), EstudioVersionModel.activa.is_(True))
            .order_by(EstudioModel.nombre, EstudioVersionModel.numero_version.desc())
        )
        versions = list(self.session.scalars(statement))
        latest: dict[int, StudyDefinition] = {}
        for version in versions:
            latest.setdefault(version.id_estudio, _study_definition(version))
        return list(latest.values())

    def list_for_panel(self, id_panel: int) -> list[StudyDefinition]:
        statement = (
            select(PanelEstudioModel.orden_visualizacion, EstudioVersionModel)
            .join(EstudioModel, EstudioModel.id_estudio == PanelEstudioModel.id_estudio)
            .join(EstudioVersionModel, EstudioVersionModel.id_estudio == EstudioModel.id_estudio)
            .options(
                selectinload(EstudioVersionModel.estudio),
                selectinload(EstudioVersionModel.parametros).selectinload(ParametroModel.rangos_referencia),
            )
            .where(
                PanelEstudioModel.id_panel == id_panel,
                EstudioModel.activo.is_(True),
                EstudioVersionModel.activa.is_(True),
            )
            .order_by(PanelEstudioModel.orden_visualizacion, EstudioVersionModel.numero_version.desc())
        )
        seen: set[int] = set()
        results = []
        for _, version in self.session.execute(statement):
            if version.id_estudio not in seen:
                seen.add(version.id_estudio)
                results.append(_study_definition(version))
        return results


class _Panels:
    def __init__(self, session: Session, studies: _Studies) -> None:
        self.session = session
        self.studies = studies

    def list_active(self) -> list[PanelDefinition]:
        models = self.session.scalars(
            select(PanelModel).where(PanelModel.activo.is_(True)).order_by(PanelModel.nombre)
        ).all()
        return [PanelDefinition(item.id_panel, item.codigo, item.nombre, item.descripcion) for item in models]

    def get_active(self, id_panel: int) -> PanelDefinition | None:
        model = self.session.scalar(
            select(PanelModel).where(PanelModel.id_panel == id_panel, PanelModel.activo.is_(True))
        )
        return PanelDefinition(model.id_panel, model.codigo, model.nombre, model.descripcion) if model else None

    def list_studies(self, id_panel: int) -> list[StudyDefinition]:
        return self.studies.list_for_panel(id_panel)


class _Orders:
    def __init__(self, session: Session, results: _Results | None = None) -> None:
        self.session = session
        self.results = results

    def next_folio(self) -> str:
        return str(self.session.execute(text("SELECT laboratorio.generar_folio_lis()")).scalar_one())

    def _load(self, id_orden: int) -> OrdenModel | None:
        statement = (
            select(OrdenModel)
            .options(
                selectinload(OrdenModel.estudios)
                .selectinload(OrdenEstudioModel.versiones_resultado)
                .selectinload(ResultadoVersionModel.valores)
                .selectinload(ResultadoValorModel.parametro),
                selectinload(OrdenModel.estudios).selectinload(OrdenEstudioModel.estudio_version),
                selectinload(OrdenModel.papelera),
                selectinload(OrdenModel.paciente),
            )
            .where(OrdenModel.id_orden == id_orden)
        )
        return self.session.scalar(statement)

    def _to_domain(self, model: OrdenModel) -> Order:
        paper = model.papelera
        studies = [
            OrderStudy(
                id_estudio=assigned.id_estudio,
                id_estudio_version=assigned.id_estudio_version or 0,
                id_orden_estudio=assigned.id_orden_estudio,
                estado=OrderStudyStatus(assigned.estado),
                observaciones=assigned.observaciones,
            )
            for assigned in model.estudios
        ]
        return Order(
            id_paciente=model.id_paciente,
            id_usuario_autor=model.id_usuario_autor,
            folio=model.folio or "",
            estudios=studies,
            id_orden=model.id_orden,
            pieza=model.pieza,
            estado=OrderStatus(model.estado),
            comentario_general=model.comentario_general,
            creado_en=model.creado_en,
            oficializado_en=model.oficializado_en,
            eliminado_por=model.eliminado_por,
            eliminado_en=model.eliminado_en,
            motivo_papelera=model.motivo_papelera or (paper.motivo if paper else None),
            estado_anterior_papelera=OrderStatus(paper.estado_anterior) if paper else None,
            restaurado=paper.restaurado if paper else False,
            restaurado_por=paper.restaurado_por if paper else None,
            restaurado_en=paper.restaurado_en if paper else None,
            paciente=_patient_domain(model.paciente),
        )

    def get_by_id(self, id_orden: int) -> Order | None:
        model = self._load(id_orden)
        return self._to_domain(model) if model else None

    def get_order_for_study(self, id_orden_estudio: int) -> tuple[Order, OrderStudy] | None:
        assigned = self.session.get(OrdenEstudioModel, id_orden_estudio)
        if assigned is None:
            return None
        order = self.get_by_id(assigned.id_orden)
        if order is None:
            return None
        domain_assignment = next(
            (item for item in order.estudios if item.id_orden_estudio == id_orden_estudio),
            None,
        )
        return (order, domain_assignment) if domain_assignment else None

    def add(self, order: Order) -> Order:
        model = OrdenModel(
            folio=order.folio,
            id_paciente=order.id_paciente,
            id_usuario_autor=order.id_usuario_autor,
            pieza=order.pieza,
            estado=order.estado.value,
            comentario_general=order.comentario_general,
        )
        self.session.add(model)
        self.session.flush()
        order.id_orden = model.id_orden
        for study in order.estudios:
            assigned = OrdenEstudioModel(
                id_orden=model.id_orden,
                id_estudio=study.id_estudio,
                id_estudio_version=study.id_estudio_version,
                estado=study.estado.value,
                observaciones=study.observaciones,
            )
            self.session.add(assigned)
            self.session.flush()
            study.id_orden_estudio = assigned.id_orden_estudio
        self.session.flush()
        return order

    def save(self, order: Order) -> Order:
        model = self.session.get(OrdenModel, order.id_orden)
        if model is None:
            raise ValueError("La orden ya no existe.")
        model.pieza = order.pieza
        model.estado = order.estado.value
        model.comentario_general = order.comentario_general
        model.motivo_papelera = order.motivo_papelera
        model.eliminado_por = order.eliminado_por
        model.eliminado_en = order.eliminado_en
        model.oficializado_en = order.oficializado_en

        assigned_models = list(
            self.session.scalars(select(OrdenEstudioModel).where(OrdenEstudioModel.id_orden == order.id_orden))
        )
        by_id = {item.id_orden_estudio: item for item in assigned_models}
        retained_ids: set[int] = set()
        for domain_study in order.estudios:
            if domain_study.id_orden_estudio is None:
                orm_study = OrdenEstudioModel(
                    id_orden=order.id_orden,
                    id_estudio=domain_study.id_estudio,
                    id_estudio_version=domain_study.id_estudio_version,
                    estado=domain_study.estado.value,
                    observaciones=domain_study.observaciones,
                )
                self.session.add(orm_study)
                self.session.flush()
                domain_study.id_orden_estudio = orm_study.id_orden_estudio
                retained_ids.add(orm_study.id_orden_estudio)
            else:
                orm_study = by_id.get(domain_study.id_orden_estudio)
                if orm_study is None:
                    raise ValueError("Un estudio de la orden desapareció de la persistencia.")
                orm_study.estado = domain_study.estado.value
                orm_study.observaciones = domain_study.observaciones
                retained_ids.add(orm_study.id_orden_estudio)
        for id_assigned, orm_study in by_id.items():
            if id_assigned not in retained_ids:
                self.session.delete(orm_study)

        paper = self.session.scalar(
            select(PapeleraOrdenModel).where(PapeleraOrdenModel.id_orden == order.id_orden)
        )
        if order.estado is OrderStatus.TRASH:
            if paper is None:
                paper = PapeleraOrdenModel(
                    id_orden=order.id_orden,
                    eliminado_por=order.eliminado_por,
                    estado_anterior=(order.estado_anterior_papelera or OrderStatus.OFFICIAL).value,
                    motivo=order.motivo_papelera or "Retirada de la papelera.",
                )
                self.session.add(paper)
            else:
                paper.eliminado_por = order.eliminado_por
                paper.estado_anterior = (order.estado_anterior_papelera or OrderStatus.OFFICIAL).value
                paper.motivo = order.motivo_papelera or paper.motivo
                paper.restaurado = False
                paper.restaurado_por = None
                paper.restaurado_en = None
        elif paper is not None and order.restaurado:
            paper.restaurado = True
            paper.restaurado_por = order.restaurado_por
            paper.restaurado_en = order.restaurado_en
        self.session.flush()
        return order

    def list_official(self, filters: HistoryFilter) -> list[Order]:
        statement = select(OrdenModel).where(OrdenModel.estado == OrderStatus.OFFICIAL.value)
        if filters.paciente_ci:
            statement = statement.join(PacienteModel).where(PacienteModel.ci == filters.paciente_ci)
        if filters.nombre:
            if not filters.paciente_ci:
                statement = statement.join(PacienteModel)
            term = f"%{filters.nombre.strip()}%"
            statement = statement.where(
                or_(PacienteModel.nombres.ilike(term), PacienteModel.apellido_paterno.ilike(term), PacienteModel.apellido_materno.ilike(term))
            )
        if filters.folio:
            statement = statement.where(OrdenModel.folio.ilike(f"%{filters.folio.strip()}%"))
        if filters.desde:
            statement = statement.where(OrdenModel.creado_en >= datetime.combine(filters.desde, datetime.min.time(), tzinfo=timezone.utc))
        if filters.hasta:
            statement = statement.where(OrdenModel.creado_en < datetime.combine(filters.hasta.fromordinal(filters.hasta.toordinal() + 1), datetime.min.time(), tzinfo=timezone.utc))
        if filters.id_usuario_autor:
            statement = statement.where(OrdenModel.id_usuario_autor == filters.id_usuario_autor)
        if filters.id_estudio:
            statement = statement.where(
                select(OrdenEstudioModel.id_orden_estudio)
                .where(
                    OrdenEstudioModel.id_orden == OrdenModel.id_orden,
                    OrdenEstudioModel.id_estudio == filters.id_estudio,
                )
                .exists()
            )
        models = self.session.scalars(statement.order_by(OrdenModel.creado_en.desc())).all()
        return [self.get_by_id(model.id_orden) for model in models]

    def list_trash(self, id_usuario: int) -> list[Order]:
        models = self.session.scalars(
            select(OrdenModel)
            .where(OrdenModel.estado == OrderStatus.TRASH.value, OrdenModel.id_usuario_autor == id_usuario)
            .order_by(OrdenModel.eliminado_en.desc())
        ).all()
        return [self.get_by_id(model.id_orden) for model in models]

    def list_by_author(self, id_usuario: int) -> list[Order]:
        models = self.session.scalars(
            select(OrdenModel)
            .where(OrdenModel.id_usuario_autor == id_usuario)
            .order_by(OrdenModel.creado_en.desc())
        ).all()
        return [self.get_by_id(model.id_orden) for model in models]


class _Results:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _query(self):
        return select(ResultadoVersionModel).options(
            selectinload(ResultadoVersionModel.valores).selectinload(ResultadoValorModel.parametro)
        )

    def _persist_values(self, result_model: ResultadoVersionModel, result: ResultVersion) -> None:
        current_rows = list(
            self.session.scalars(
                select(ResultadoValorModel)
                .options(selectinload(ResultadoValorModel.parametro))
                .where(
                    ResultadoValorModel.id_resultado_version == result_model.id_resultado_version
                )
            )
        )
        version = self.session.get(EstudioVersionModel, result.id_estudio_version)
        if version is None:
            raise ValueError("La versión de configuración del resultado no existe.")
        parameters = {parameter.codigo: parameter for parameter in version.parametros}
        current_by_code = {row.parametro.codigo: row for row in current_rows}
        units = result.snapshot_completo.get("unidades", {})
        references = result.snapshot_completo.get("referencias", {})
        desired_codes: set[str] = set()
        for values, calculated in ((result.entradas, False), (result.calculados, True)):
            for code, value in values.items():
                parameter = parameters.get(code)
                if parameter is None:
                    raise ValueError(f"El parámetro '{code}' no existe en la versión de estudio.")
                desired_codes.add(code)
                row = current_by_code.get(code)
                kwargs: dict[str, Any] = {
                    "valor_numerico": None,
                    "valor_texto": None,
                    "valor_booleano": None,
                }
                if value is not None:
                    if parameter.tipo_dato in {"DECIMAL", "ENTERO"}:
                        kwargs["valor_numerico"] = Decimal(str(value))
                    elif parameter.tipo_dato == "BOOLEANO":
                        kwargs["valor_booleano"] = bool(value)
                    else:
                        kwargs["valor_texto"] = str(value)
                if row is None:
                    row = ResultadoValorModel(
                        id_resultado_version=result_model.id_resultado_version,
                        id_parametro=parameter.id_parametro,
                        **kwargs,
                    )
                    self.session.add(row)
                else:
                    row.id_parametro = parameter.id_parametro
                    for name, value_to_store in kwargs.items():
                        setattr(row, name, value_to_store)
                row.unidad_utilizada = units.get(code) or parameter.unidad_medida
                row.referencia_utilizada = references.get(code)
                row.fuera_de_rango = None
                row.valor_calculado = calculated
                row.orden_visualizacion = parameter.orden_visualizacion
        for code, row in current_by_code.items():
            if code not in desired_codes:
                self.session.delete(row)

    def _save(self, result: ResultVersion) -> ResultVersion:
        model = self.session.get(ResultadoVersionModel, result.id_resultado_version) if result.id_resultado_version else None
        if model is None:
            model = ResultadoVersionModel(
                id_orden_estudio=result.id_orden_estudio,
                numero_version=result.numero_version,
                id_estudio_version=result.id_estudio_version,
                creado_por=result.creado_por,
                estado=result.estado.value,
                motivo_correccion=result.motivo_correccion,
                comentario_estudio=result.comentario_estudio,
                snapshot_completo=_json_value(result.snapshot_completo),
                oficializado_en=result.oficializado_en,
            )
            self.session.add(model)
            self.session.flush()
            result.id_resultado_version = model.id_resultado_version
        else:
            if model.estado != ResultStatus.DRAFT.value:
                if not (
                    model.estado == ResultStatus.OFFICIAL.value
                    and result.estado is ResultStatus.SUPERSEDED
                ):
                    raise ValueError("Una versión de resultado oficial o cerrada es inmutable.")
                persisted = self.session.scalar(
                    self._query().where(
                        ResultadoVersionModel.id_resultado_version == model.id_resultado_version
                    )
                )
                if persisted is None:
                    raise ValueError("No se pudo recargar la versión de resultado.")
                original = _result_domain(persisted)
                if (
                    result.id_orden_estudio != original.id_orden_estudio
                    or result.numero_version != original.numero_version
                    or result.id_estudio_version != original.id_estudio_version
                    or result.creado_por != original.creado_por
                    or result.motivo_correccion != original.motivo_correccion
                    or result.comentario_estudio != original.comentario_estudio
                    or result.entradas != original.entradas
                    or result.calculados != original.calculados
                    or result.advertencias != original.advertencias
                    or result.snapshot_completo != original.snapshot_completo
                    or result.creado_en != original.creado_en
                    or result.oficializado_en != original.oficializado_en
                ):
                    raise ValueError("No se pueden alterar los datos de una versión oficial.")
                model.estado = result.estado.value
                self.session.flush()
                return result
            model.estado = result.estado.value
            model.motivo_correccion = result.motivo_correccion
            model.comentario_estudio = result.comentario_estudio
            model.snapshot_completo = _json_value(result.snapshot_completo)
            model.oficializado_en = result.oficializado_en
        self._persist_values(model, result)
        self.session.flush()
        return result

    def get_draft(self, id_orden_estudio: int) -> ResultVersion | None:
        model = self.session.scalar(
            self._query()
            .where(
                ResultadoVersionModel.id_orden_estudio == id_orden_estudio,
                ResultadoVersionModel.estado == ResultStatus.DRAFT.value,
            )
            .order_by(ResultadoVersionModel.numero_version.desc())
            .limit(1)
        )
        return _result_domain(model) if model else None

    def get_latest(self, id_orden_estudio: int) -> ResultVersion | None:
        model = self.session.scalar(
            self._query()
            .where(ResultadoVersionModel.id_orden_estudio == id_orden_estudio)
            .order_by(ResultadoVersionModel.numero_version.desc())
            .limit(1)
        )
        return _result_domain(model) if model else None

    def list_versions(self, id_orden_estudio: int) -> list[ResultVersion]:
        models = self.session.scalars(
            self._query()
            .where(ResultadoVersionModel.id_orden_estudio == id_orden_estudio)
            .order_by(ResultadoVersionModel.numero_version)
        ).all()
        return [_result_domain(model) for model in models]

    def list_for_order_study(self, id_orden_estudio: int) -> list[ResultVersion]:
        return self.list_versions(id_orden_estudio)

    def save_draft(self, result: ResultVersion) -> ResultVersion:
        if result.estado is not ResultStatus.DRAFT:
            raise ValueError("Solo se puede guardar un borrador como mutable.")
        return self._save(result)

    def add_correction(self, result: ResultVersion, changes: list[ResultChange]) -> ResultVersion:
        saved = self._save(result)
        self.save_changes(changes, saved.id_resultado_version)
        return saved

    def save(self, result: ResultVersion) -> ResultVersion:
        return self._save(result)

    def save_changes(self, changes: list[ResultChange], id_resultado_version: int) -> None:
        for change in changes:
            id_parametro = change.id_parametro
            if id_parametro is None:
                result = self.session.get(ResultadoVersionModel, id_resultado_version)
                parameter = self.session.scalar(
                    select(ParametroModel).where(
                        ParametroModel.id_estudio_version == result.id_estudio_version,
                        ParametroModel.codigo == change.codigo_parametro,
                    )
                )
                id_parametro = parameter.id_parametro if parameter else None
            self.session.add(
                CambioResultadoModel(
                    id_resultado_version=id_resultado_version,
                    id_parametro=id_parametro,
                    id_usuario=change.id_usuario,
                    valor_anterior=change.valor_anterior,
                    valor_nuevo=change.valor_nuevo,
                    comentario=change.comentario,
                )
            )
        self.session.flush()

    def latest_official_order_results(self, id_orden: int) -> list[ResultVersion]:
        ids = self.session.scalars(
            select(OrdenEstudioModel.id_orden_estudio).where(OrdenEstudioModel.id_orden == id_orden)
        ).all()
        results = []
        for id_assigned in ids:
            result = self.get_latest(id_assigned)
            if result and result.estado is ResultStatus.OFFICIAL:
                results.append(result)
        return results


class _Delegations:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _accepted_ids(self, id_orden: int) -> set[int]:
        statement = select(AuditoriaModel.datos_nuevos).where(
            AuditoriaModel.id_orden == id_orden,
            AuditoriaModel.accion == "DELEGACION_ACEPTADA",
        )
        accepted = set()
        for payload in self.session.scalars(statement):
            if payload and payload.get("id_delegacion") is not None:
                accepted.add(int(payload["id_delegacion"]))
        return accepted

    def _map(self, model: DelegacionModel) -> Delegation:
        studies = list(
            self.session.scalars(
                select(OrdenEstudioModel.id_estudio)
                .join(
                    DelegacionEstudioModel,
                    DelegacionEstudioModel.id_orden_estudio == OrdenEstudioModel.id_orden_estudio,
                )
                .where(DelegacionEstudioModel.id_delegacion == model.id_delegacion)
            )
        )
        accepted = model.id_delegacion in self._accepted_ids(model.id_orden)
        return Delegation(
            id_orden=model.id_orden,
            id_usuario_autor=model.id_usuario_autor,
            id_usuario_colaborador=model.id_usuario_colaborador,
            modalidad=DelegationMode(model.modalidad),
            id_delegacion=model.id_delegacion,
            estudios=set(studies),
            activa=model.activa,
            aceptada=accepted,
            comentario=model.comentario,
            creada_en=model.creada_en,
            finalizada_en=model.finalizada_en,
        )

    def get_by_id(self, id_delegacion: int) -> Delegation | None:
        model = self.session.get(DelegacionModel, id_delegacion)
        return self._map(model) if model else None

    def get_active_for_order(self, id_orden: int) -> Delegation | None:
        model = self.session.scalar(
            select(DelegacionModel).where(
                DelegacionModel.id_orden == id_orden,
                DelegacionModel.activa.is_(True),
            )
        )
        return self._map(model) if model else None

    def list_for_collaborator(self, id_usuario: int) -> list[Delegation]:
        models = self.session.scalars(
            select(DelegacionModel)
            .where(DelegacionModel.id_usuario_colaborador == id_usuario, DelegacionModel.activa.is_(True))
            .order_by(DelegacionModel.creada_en.desc())
        ).all()
        return [self._map(model) for model in models]

    def list_for_order(self, id_orden: int) -> list[Delegation]:
        models = self.session.scalars(
            select(DelegacionModel)
            .where(DelegacionModel.id_orden == id_orden)
            .order_by(DelegacionModel.creada_en.desc())
        ).all()
        return [self._map(model) for model in models]

    def add(self, delegation: Delegation) -> Delegation:
        model = DelegacionModel(
            id_orden=delegation.id_orden,
            id_usuario_autor=delegation.id_usuario_autor,
            id_usuario_colaborador=delegation.id_usuario_colaborador,
            modalidad=delegation.modalidad.value,
            comentario=delegation.comentario,
            activa=delegation.activa,
        )
        self.session.add(model)
        self.session.flush()
        delegation.id_delegacion = model.id_delegacion
        order_study_ids = self.session.scalars(
            select(OrdenEstudioModel.id_orden_estudio).where(
                OrdenEstudioModel.id_orden == delegation.id_orden,
                OrdenEstudioModel.id_estudio.in_(delegation.estudios),
            )
        ).all()
        if len(order_study_ids) != len(delegation.estudios):
            raise ValueError("La delegación contiene estudios que no pertenecen a la orden.")
        for id_orden_estudio in order_study_ids:
            self.session.add(
                DelegacionEstudioModel(
                    id_delegacion=model.id_delegacion,
                    id_orden_estudio=id_orden_estudio,
                )
            )
        self.session.flush()
        return delegation

    def save(self, delegation: Delegation) -> Delegation:
        model = self.session.get(DelegacionModel, delegation.id_delegacion)
        if model is None:
            raise ValueError("La delegación ya no existe.")
        model.activa = delegation.activa
        model.finalizada_en = delegation.finalizada_en
        model.comentario = delegation.comentario
        self.session.flush()
        return delegation


class _Audits:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: AuditEvent) -> None:
        self.session.add(
            AuditoriaModel(
                id_usuario=event.id_usuario,
                id_orden=event.id_orden,
                id_orden_estudio=event.id_orden_estudio,
                id_resultado_version=event.id_resultado_version,
                accion=event.accion,
                entidad=event.entidad,
                descripcion=event.descripcion,
                datos_anteriores=_json_value(event.datos_anteriores),
                datos_nuevos=_json_value(event.datos_nuevos),
            )
        )

    @staticmethod
    def _event(model: AuditoriaModel) -> AuditEvent:
        data = model.datos_nuevos or model.datos_anteriores or {}
        if model.entidad == "paciente":
            entidad_id = data.get("id_paciente")
        elif model.entidad == "orden":
            entidad_id = model.id_orden
        elif model.id_orden_estudio is not None:
            entidad_id = model.id_orden_estudio
        else:
            entidad_id = model.id_resultado_version or model.id_orden
        return AuditEvent(
            accion=model.accion,
            id_usuario=model.id_usuario or 0,
            id_orden=model.id_orden,
            id_orden_estudio=model.id_orden_estudio,
            id_resultado_version=model.id_resultado_version,
            entidad=model.entidad,
            entidad_id=int(entidad_id) if entidad_id is not None else None,
            descripcion=model.descripcion,
            datos_anteriores=model.datos_anteriores,
            datos_nuevos=model.datos_nuevos,
            id_auditoria=model.id_auditoria,
            creado_en=model.creado_en,
        )

    def list_recent(self, limit: int = 200) -> list[AuditEvent]:
        models = self.session.scalars(
            select(AuditoriaModel).order_by(AuditoriaModel.creado_en.desc()).limit(limit)
        ).all()
        return [self._event(model) for model in models]

    def list_for_order(self, id_orden: int, limit: int = 200) -> list[AuditEvent]:
        models = self.session.scalars(
            select(AuditoriaModel)
            .where(AuditoriaModel.id_orden == id_orden)
            .order_by(AuditoriaModel.creado_en.desc())
            .limit(limit)
        ).all()
        return [self._event(model) for model in models]

    def add_security_event(
        self,
        id_usuario: int | None,
        evento: str,
        ip_origen: str | None = None,
        user_agent: str | None = None,
        detalles: dict[str, object] | None = None,
    ) -> None:
        try:
            normalized_ip = str(ip_address(ip_origen)) if ip_origen else None
        except ValueError:
            normalized_ip = None
        self.session.add(
            AuditoriaSeguridadModel(
                id_usuario=id_usuario,
                evento=evento,
                ip_origen=normalized_ip,
                user_agent=user_agent,
                detalles=_json_value(detalles),
            )
        )

    def list_changes(self, id_orden: int) -> list[ResultChange]:
        statement = (
            select(
                CambioResultadoModel,
                ParametroModel.codigo,
                ResultadoVersionModel.id_orden_estudio,
                ResultadoVersionModel.numero_version,
            )
            .join(ResultadoVersionModel, ResultadoVersionModel.id_resultado_version == CambioResultadoModel.id_resultado_version)
            .join(OrdenEstudioModel, OrdenEstudioModel.id_orden_estudio == ResultadoVersionModel.id_orden_estudio)
            .outerjoin(ParametroModel, ParametroModel.id_parametro == CambioResultadoModel.id_parametro)
            .where(OrdenEstudioModel.id_orden == id_orden)
            .order_by(CambioResultadoModel.creado_en)
        )
        return [
            ResultChange(
                id_parametro=model.id_parametro,
                codigo_parametro=code or "",
                valor_anterior=model.valor_anterior,
                valor_nuevo=model.valor_nuevo,
                comentario=model.comentario,
                id_usuario=model.id_usuario,
                id_orden_estudio=id_orden_estudio,
                numero_version=numero_version,
                creado_en=model.creado_en,
            )
            for model, code, id_orden_estudio, numero_version in self.session.execute(statement)
        ]


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.patients = _Patients(session)
        self.users = _Users(session)
        self.studies = _Studies(session)
        self.panels = _Panels(session, self.studies)
        self.results = _Results(session)
        self.orders = _Orders(session, self.results)
        self.delegations = _Delegations(session)
        self.audits = _Audits(session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
