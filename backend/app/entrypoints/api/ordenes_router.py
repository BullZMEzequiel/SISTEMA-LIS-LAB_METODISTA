from datetime import date

from fastapi import APIRouter, Depends, Response, status

from app.adapters.persistence.models import UsuarioModel
from app.adapters.security.dependencies import require_roles
from app.application.ports import Clock, PdfPort, UnitOfWork
from app.application.use_cases import (
    AceptarDelegacion,
    ActualizarOrdenBorrador,
    AgregarEstudio,
    CalcularEstudio,
    ConsultarAuditoria,
    ConsultarCambios,
    ConsultarDelegaciones,
    ConsultarEstudioOrden,
    ConsultarEstudiosOrden,
    ConsultarHistorial,
    ConsultarOrden,
    ConsultarOrdenes,
    ConsultarPapelera,
    ConsultarResultadoEstudio,
    ConsultarVersionesOrden,
    CrearCorreccion,
    CrearOrden,
    DelegarEstudio,
    DelegarOrden,
    FinalizarDelegacion,
    GenerarPDF,
    GuardarBorrador,
    MoverOrdenAPapelera,
    OficializarOrden,
    QuitarEstudio,
    RestaurarOrden,
)
from app.application.ports import CalculationPort
from app.domain.entities import (
    AuditEvent,
    Delegation,
    HistoryFilter,
    Order,
    OrderStudy,
    HistoryFilter,
    Patient,
    ResultChange,
    ResultVersion,
)
from app.domain.exceptions import DomainError
from app.entrypoints.api.contracts import (
    AuditEventResponse,
    AddStudyRequest,
    CalculateResponse,
    CorrectionRequest,
    DelegationRequest,
    DelegationResponse,
    OrderCreateRequest,
    OrderDraftUpdateRequest,
    OrderResponse,
    OrderStudyResponse,
    PatientResponse,
    ResultChangeResponse,
    ResultVersionResponse,
    SaveDraftRequest,
    TrashRequest,
    TrashRestoreResponse,
)
from app.entrypoints.api.dependencies import get_calculation_port, get_clock, get_pdf_port, get_unit_of_work
from app.entrypoints.api.http_errors import as_http_error

router = APIRouter(tags=["Órdenes", "Resultados", "Delegaciones", "Versiones", "Papelera", "PDF"])
authorized_roles = ["BIOQUIMICO"]


def _patient_response(patient: Patient | None) -> PatientResponse | None:
    if patient is None:
        return None
    return PatientResponse(
        id_paciente=patient.id_paciente,
        ci=patient.ci,
        nombres=patient.nombres,
        apellido_paterno=patient.apellido_paterno,
        apellido_materno=patient.apellido_materno,
        apellidos=" ".join(value for value in (patient.apellido_paterno, patient.apellido_materno) if value),
        fecha_nacimiento=patient.fecha_nacimiento,
        sexo=patient.sexo,
        telefono=patient.telefono,
        correo=patient.correo,
        creado_en=patient.creado_en,
    )


def _order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id_orden=order.id_orden,
        folio=order.folio,
        id_paciente=order.id_paciente,
        id_usuario_autor=order.id_usuario_autor,
        pieza=order.pieza,
        estado=order.estado.value,
        comentario_general=order.comentario_general,
        creado_en=order.creado_en,
        actualizado_en=None,
        oficializado_en=order.oficializado_en,
        estudios=[_order_study_response(study) for study in order.estudios],
        paciente=_patient_response(order.paciente),
    )


def _order_study_response(study: OrderStudy) -> OrderStudyResponse:
    return OrderStudyResponse(
        id_orden_estudio=study.id_orden_estudio,
        id_estudio=study.id_estudio,
        id_estudio_version=study.id_estudio_version,
        estado=study.estado.value,
        observaciones=study.observaciones,
    )


def _result_response(result: ResultVersion) -> ResultVersionResponse:
    return ResultVersionResponse(
        id_resultado_version=result.id_resultado_version,
        id_orden_estudio=result.id_orden_estudio,
        numero_version=result.numero_version,
        creado_por=result.creado_por,
        estado=result.estado.value,
        motivo_correccion=result.motivo_correccion,
        creado_en=result.creado_en,
        oficializado_en=result.oficializado_en,
        entradas=result.entradas,
        calculados=result.calculados,
        advertencias=result.advertencias,
        snapshot_completo=result.snapshot_completo,
    )


def _delegation_response(delegation: Delegation) -> DelegationResponse:
    return DelegationResponse(
        id_delegacion=delegation.id_delegacion,
        id_orden=delegation.id_orden,
        id_usuario_autor=delegation.id_usuario_autor,
        id_usuario_colaborador=delegation.id_usuario_colaborador,
        modalidad=delegation.modalidad.value,
        estudios=sorted(delegation.estudios),
        activa=delegation.activa,
        aceptada=delegation.aceptada,
        creada_en=delegation.creada_en,
        finalizada_en=delegation.finalizada_en,
    )


def _change_response(change: ResultChange) -> ResultChangeResponse:
    return ResultChangeResponse(
        id_parametro=change.id_parametro,
        codigo_parametro=change.codigo_parametro,
        id_orden_estudio=change.id_orden_estudio,
        numero_version=change.numero_version,
        valor_anterior=change.valor_anterior,
        valor_nuevo=change.valor_nuevo,
        comentario=change.comentario,
        id_usuario=change.id_usuario,
        creado_en=change.creado_en,
    )


def _audit_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id_usuario=event.id_usuario,
        id_orden=event.id_orden,
        id_orden_estudio=event.id_orden_estudio,
        id_resultado_version=event.id_resultado_version,
        accion=event.accion,
        entidad=event.entidad,
        descripcion=event.descripcion,
    )


def _execute(call):
    try:
        return call()
    except DomainError as exc:
        raise as_http_error(exc) from exc


@router.post("/ordenes", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> OrderResponse:
    order = _execute(lambda: CrearOrden(uow).execute(
        id_paciente=payload.id_paciente,
        id_usuario_autor=user.id_usuario,
        ids_estudio=payload.ids_estudio,
        pieza=payload.pieza,
    ))
    return _order_response(order)


@router.get("/ordenes", response_model=list[OrderResponse])
def list_orders(
    paciente_ci: str | None = None,
    nombre: str | None = None,
    folio: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    id_estudio: int | None = None,
    id_usuario_autor: int | None = None,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[OrderResponse]:
    filters = HistoryFilter(
        paciente_ci=paciente_ci,
        nombre=nombre,
        folio=folio,
        desde=desde,
        hasta=hasta,
        id_estudio=id_estudio,
        id_usuario_autor=id_usuario_autor,
    )
    orders = _execute(lambda: ConsultarOrdenes(uow).execute(user.id_usuario, filters))
    return [_order_response(order) for order in orders]


@router.get("/ordenes/{id_orden}", response_model=OrderResponse)
def get_order(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> OrderResponse:
    order = _execute(lambda: ConsultarOrden(uow).execute(id_orden, user.id_usuario))
    return _order_response(order)


@router.put("/ordenes/{id_orden}/borrador", response_model=OrderResponse)
def update_order_draft(
    id_orden: int,
    payload: OrderDraftUpdateRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> OrderResponse:
    order = _execute(lambda: ActualizarOrdenBorrador(uow).execute(
        id_orden,
        user.id_usuario,
        pieza=payload.pieza,
        comentario_general=payload.comentario_general,
    ))
    return _order_response(order)


@router.post("/ordenes/{id_orden}/oficializar", response_model=OrderResponse)
def officialize_order(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    calculation: CalculationPort = Depends(get_calculation_port),
    clock: Clock = Depends(get_clock),
) -> OrderResponse:
    order = _execute(lambda: OficializarOrden(uow, calculation, clock).execute(id_orden, user.id_usuario))
    return _order_response(order)


@router.post("/ordenes/{id_orden}/estudios", response_model=OrderStudyResponse, status_code=status.HTTP_201_CREATED)
def add_study(
    id_orden: int,
    payload: AddStudyRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> OrderStudyResponse:
    order = _execute(lambda: AgregarEstudio(uow).execute(id_orden, payload.id_estudio, user.id_usuario))
    study = order.estudios[-1]
    return _order_study_response(study)


@router.delete("/ordenes/{id_orden}/estudios/{id_estudio}", status_code=status.HTTP_204_NO_CONTENT)
def remove_study(
    id_orden: int,
    id_estudio: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> Response:
    _execute(lambda: QuitarEstudio(uow).execute(id_orden, id_estudio, user.id_usuario))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/ordenes/{id_orden}/estudios", response_model=list[OrderStudyResponse])
def list_order_studies(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[OrderStudyResponse]:
    studies = _execute(lambda: ConsultarEstudiosOrden(uow).execute(id_orden, user.id_usuario))
    return [_order_study_response(study) for study in studies]


@router.get("/ordenes/{id_orden}/estudios/{id_estudio}", response_model=ResultVersionResponse)
def get_study_result(
    id_orden: int,
    id_estudio: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ResultVersionResponse:
    result = _execute(lambda: ConsultarResultadoEstudio(uow).execute(id_orden, id_estudio, user.id_usuario))
    if result is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El estudio aún no tiene resultados.")
    return _result_response(result)


@router.post("/ordenes/{id_orden}/estudios/{id_estudio}/calcular", response_model=CalculateResponse)
def calculate_study(
    id_orden: int,
    id_estudio: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    calculation: CalculationPort = Depends(get_calculation_port),
) -> CalculateResponse:
    assigned = _execute(lambda: ConsultarEstudioOrden(uow).execute(id_orden, id_estudio, user.id_usuario))
    if assigned.id_orden_estudio is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El estudio no pertenece a la orden.")
    result = _execute(lambda: CalcularEstudio(uow, calculation).execute(assigned.id_orden_estudio, user.id_usuario))
    return CalculateResponse(
        id_resultado_version=result.id_resultado_version,
        id_orden_estudio=result.id_orden_estudio,
        numero_version=result.numero_version,
        estado=result.estado.value,
        entradas=result.entradas,
        calculados=result.calculados,
        advertencias=result.advertencias,
    )


@router.put("/ordenes/{id_orden}/estudios/{id_estudio}/resultado", response_model=ResultVersionResponse)
def save_study_result(
    id_orden: int,
    id_estudio: int,
    payload: SaveDraftRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ResultVersionResponse:
    assigned = _execute(lambda: ConsultarEstudioOrden(uow).execute(id_orden, id_estudio, user.id_usuario))
    if assigned.id_orden_estudio is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El estudio no pertenece a la orden.")
    result = _execute(lambda: GuardarBorrador(uow).execute(
        id_orden_estudio=assigned.id_orden_estudio,
        id_usuario=user.id_usuario,
        entradas=payload.entradas,
        comentario=payload.comentario,
    ))
    return _result_response(result)


@router.post("/ordenes/{id_orden}/delegaciones", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
def delegate_order(
    id_orden: int,
    payload: DelegationRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> DelegationResponse:
    if payload.modalidad.value == "TRABAJO_COMPLETO":
        delegation = _execute(lambda: DelegarOrden(uow).execute(
            id_orden=id_orden,
            id_usuario_autor=user.id_usuario,
            id_usuario_colaborador=payload.id_usuario_colaborador,
            comentario=payload.comentario,
        ))
    else:
        delegation = _execute(lambda: DelegarEstudio(uow).execute(
            id_orden=id_orden,
            id_usuario_autor=user.id_usuario,
            id_usuario_colaborador=payload.id_usuario_colaborador,
            ids_estudio=payload.ids_estudio,
            comentario=payload.comentario,
        ))
    return _delegation_response(delegation)


@router.post("/delegaciones/{id_delegacion}/aceptar", response_model=DelegationResponse)
def accept_delegation(
    id_delegacion: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> DelegationResponse:
    delegation = _execute(lambda: AceptarDelegacion(uow).execute(id_delegacion, user.id_usuario))
    return _delegation_response(delegation)


@router.post("/delegaciones/{id_delegacion}/finalizar", response_model=DelegationResponse)
def finish_delegation(
    id_delegacion: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
) -> DelegationResponse:
    delegation = _execute(lambda: FinalizarDelegacion(uow, clock).execute(id_delegacion, user.id_usuario))
    return _delegation_response(delegation)


@router.get("/ordenes/{id_orden}/delegaciones", response_model=list[DelegationResponse])
def list_delegations(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[DelegationResponse]:
    items = _execute(lambda: ConsultarDelegaciones(uow).execute(id_orden, user.id_usuario))
    return [_delegation_response(item) for item in items]


@router.get("/ordenes/{id_orden}/versiones", response_model=list[ResultVersionResponse])
def list_versions(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[ResultVersionResponse]:
    versions = _execute(lambda: ConsultarVersionesOrden(uow).execute(id_orden, user.id_usuario))
    return [_result_response(item) for item in versions]


@router.get("/ordenes/{id_orden}/cambios", response_model=list[ResultChangeResponse])
def list_changes(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[ResultChangeResponse]:
    return [_change_response(item) for item in _execute(lambda: ConsultarCambios(uow).execute(id_orden, user.id_usuario))]


@router.post("/ordenes/{id_orden}/correcciones", response_model=ResultVersionResponse, status_code=status.HTTP_201_CREATED)
def create_correction(
    id_orden: int,
    payload: CorrectionRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    calculation: CalculationPort = Depends(get_calculation_port),
) -> ResultVersionResponse:
    order = _execute(lambda: ConsultarOrden(uow).execute(id_orden, user.id_usuario))
    if not any(item.id_orden_estudio == payload.id_orden_estudio for item in order.estudios):
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El estudio no pertenece a la orden.")
    result = _execute(lambda: CrearCorreccion(uow, calculation).execute(
        id_orden_estudio=payload.id_orden_estudio,
        id_usuario=user.id_usuario,
        motivo=payload.motivo,
        nuevas_entradas=payload.nuevas_entradas,
    ))
    return _result_response(result)


@router.post("/ordenes/{id_orden}/papelera", response_model=TrashRestoreResponse)
def move_order_to_trash(
    id_orden: int,
    payload: TrashRequest,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
) -> TrashRestoreResponse:
    order = _execute(lambda: MoverOrdenAPapelera(uow, clock).execute(id_orden, user.id_usuario, payload.motivo))
    return TrashRestoreResponse(
        id_orden=order.id_orden,
        folio=order.folio,
        estado=order.estado.value,
        eliminado_por=order.eliminado_por,
        eliminado_en=order.eliminado_en,
        motivo=order.motivo_papelera,
    )


@router.get("/papelera", response_model=list[TrashRestoreResponse])
def list_trash(
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[TrashRestoreResponse]:
    orders = _execute(lambda: ConsultarPapelera(uow).execute(user.id_usuario))
    return [
        TrashRestoreResponse(
            id_orden=order.id_orden,
            folio=order.folio,
            estado=order.estado.value,
            eliminado_por=order.eliminado_por,
            eliminado_en=order.eliminado_en,
            motivo=order.motivo_papelera,
        )
        for order in orders
    ]


@router.post("/papelera/{id_orden}/restaurar", response_model=OrderResponse)
def restore_order(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
) -> OrderResponse:
    order = _execute(lambda: RestaurarOrden(uow, clock).execute(id_orden, user.id_usuario))
    return _order_response(order)


@router.get("/ordenes/{id_orden}/pdf")
def get_order_pdf(
    id_orden: int,
    user: UsuarioModel = Depends(require_roles(authorized_roles)),
    uow: UnitOfWork = Depends(get_unit_of_work),
    pdf: PdfPort = Depends(get_pdf_port),
) -> Response:
    _execute(lambda: ConsultarOrden(uow).execute(id_orden, user.id_usuario))
    content = _execute(lambda: GenerarPDF(uow, pdf).execute(id_orden))
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{id_orden}.pdf"'},
    )