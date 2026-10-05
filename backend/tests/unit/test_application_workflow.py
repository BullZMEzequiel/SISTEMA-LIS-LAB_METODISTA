from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from app.application.use_cases.colaboracion import (
    AceptarDelegacion,
    DelegarEstudio,
    FinalizarDelegacion,
)
from app.application.use_cases.ciclo_vida import GenerarPDF, MoverOrdenAPapelera, RestaurarOrden
from app.application.use_cases.consultas import ConsultarCambios, ConsultarHistorial, ConsultarVersiones
from app.application.use_cases.ordenes import AgregarEstudio, CrearOrden, QuitarEstudio
from app.application.use_cases.pacientes import BuscarPaciente, CrearPaciente, ActualizarPaciente
from app.application.use_cases.resultados import (
    CalcularEstudio,
    CrearCorreccion,
    GuardarBorrador,
    OficializarOrden,
)
from app.domain.entities import (
    AuditEvent,
    CalculationOutcome,
    Delegation,
    HistoryFilter,
    Order,
    OrderStatus,
    OrderStudy,
    Patient,
    ResultChange,
    ResultStatus,
    ResultVersion,
    StudyDefinition,
)
from app.domain.exceptions import InvalidState, PermissionDenied, ValidationError
from app.domain.services.calculation_engine import CalculationEngine


class MemoryUnitOfWork:
    def __init__(self) -> None:
        self.patients = MemoryPatients()
        self.users = MemoryUsers()
        self.studies = MemoryStudies()
        self.orders = MemoryOrders()
        self.results = MemoryResults()
        self.delegations = MemoryDelegations()
        self.audits = MemoryAudits()
        self.audits.changes = self.results.changes
        self.commit_count = 0
        self.rollback_count = 0

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


class MemoryPatients:
    def __init__(self) -> None:
        self.items: dict[int, Patient] = {}
        self.next_id = 1

    def get_by_id(self, id_paciente: int) -> Patient | None:
        return self.items.get(id_paciente)

    def get_by_ci(self, ci: str) -> Patient | None:
        return next((patient for patient in self.items.values() if patient.ci == ci), None)

    def search(self, query: str, limit: int = 50) -> list[Patient]:
        term = query.casefold()
        return [patient for patient in self.items.values() if term in patient.ci.casefold()][:limit]

    def add(self, patient: Patient) -> Patient:
        patient.id_paciente = self.next_id
        self.next_id += 1
        self.items[patient.id_paciente] = patient
        return patient

    def save(self, patient: Patient) -> Patient:
        self.items[patient.id_paciente] = patient
        return patient


class MemoryUsers:
    def exists_active_bioquimico(self, id_usuario: int) -> bool:
        return id_usuario in {7, 8}

    def exists_active_admin(self, id_usuario: int) -> bool:
        return False


class MemoryStudies:
    def __init__(self) -> None:
        self.items = {
            id_estudio: StudyDefinition(
                id_estudio=id_estudio,
                codigo=f"STUDIO_{id_estudio}",
                nombre=f"Estudio {id_estudio}",
                id_estudio_version=100 + id_estudio,
                numero_version=1,
                estrategia_calculo="FAKE",
                parametros_obligatorios=("manual", "calculado"),
                parameter_ids={"manual": 130, "calculado": 131},
                unidades={"manual": "mg/dL", "calculado": "mg/dL"},
                referencias={"manual": "1-10 mg/dL", "calculado": "2-20 mg/dL"},
                configuracion={"captura": "entrada manual"},
            )
            for id_estudio in (13, 14)
        }

    def get_active(self, id_estudio: int) -> StudyDefinition | None:
        return self.items.get(id_estudio)

    def get_version(self, id_estudio_version: int) -> StudyDefinition | None:
        return next(
            (study for study in self.items.values() if study.id_estudio_version == id_estudio_version),
            None,
        )


class MemoryOrders:
    def __init__(self) -> None:
        self.items: dict[int, Order] = {}
        self.next_id = 1
        self.next_study_id = 1
        self.folio_count = 0

    def next_folio(self) -> str:
        self.folio_count += 1
        return f"LIS-{self.folio_count:08d}"

    def get_by_id(self, id_orden: int) -> Order | None:
        return self.items.get(id_orden)

    def get_order_for_study(self, id_orden_estudio: int) -> tuple[Order, OrderStudy] | None:
        for order in self.items.values():
            for study in order.estudios:
                if study.id_orden_estudio == id_orden_estudio:
                    return order, study
        return None

    def add(self, order: Order) -> Order:
        order.id_orden = self.next_id
        self.next_id += 1
        for study in order.estudios:
            study.id_orden_estudio = self.next_study_id
            self.next_study_id += 1
        self.items[order.id_orden] = order
        return order

    def save(self, order: Order) -> Order:
        self.items[order.id_orden] = order
        return order

    def list_official(self, filters: HistoryFilter) -> list[Order]:
        return [order for order in self.items.values() if order.estado is OrderStatus.OFFICIAL]

    def list_trash(self, id_usuario: int) -> list[Order]:
        return [
            order
            for order in self.items.values()
            if order.estado is OrderStatus.TRASH and order.id_usuario_autor == id_usuario
        ]


class MemoryResults:
    def __init__(self) -> None:
        self.items: dict[int, list[ResultVersion]] = {}
        self.next_id = 1
        self.changes: list[ResultChange] = []

    def get_draft(self, id_orden_estudio: int) -> ResultVersion | None:
        return next(
            (item for item in reversed(self.items.get(id_orden_estudio, [])) if item.estado is ResultStatus.DRAFT),
            None,
        )

    def get_latest(self, id_orden_estudio: int) -> ResultVersion | None:
        versions = self.items.get(id_orden_estudio, [])
        return versions[-1] if versions else None

    def list_versions(self, id_orden_estudio: int) -> list[ResultVersion]:
        return list(self.items.get(id_orden_estudio, []))

    def save_draft(self, result: ResultVersion) -> ResultVersion:
        if result.id_resultado_version is None:
            result.id_resultado_version = self.next_id
            self.next_id += 1
            self.items.setdefault(result.id_orden_estudio, []).append(result)
        return result

    def add_correction(self, result: ResultVersion, changes: list[ResultChange]) -> ResultVersion:
        self.save_draft(result)
        self.save_changes(changes, result.id_resultado_version)
        return result

    def save(self, result: ResultVersion) -> ResultVersion:
        return result

    def save_changes(self, changes: list[ResultChange], id_resultado_version: int) -> None:
        self.changes.extend(changes)

    def latest_official_order_results(self, id_orden: int) -> list[ResultVersion]:
        return [
            versions[-1]
            for versions in self.items.values()
            if versions and versions[-1].estado is ResultStatus.OFFICIAL
        ]


class MemoryDelegations:
    def __init__(self) -> None:
        self.items: dict[int, Delegation] = {}
        self.next_id = 1

    def get_by_id(self, id_delegacion: int) -> Delegation | None:
        return self.items.get(id_delegacion)

    def get_active_for_order(self, id_orden: int) -> Delegation | None:
        return next(
            (item for item in self.items.values() if item.id_orden == id_orden and item.activa),
            None,
        )

    def list_for_collaborator(self, id_usuario: int) -> list[Delegation]:
        return [item for item in self.items.values() if item.id_usuario_colaborador == id_usuario]

    def add(self, delegation: Delegation) -> Delegation:
        delegation.id_delegacion = self.next_id
        self.next_id += 1
        self.items[delegation.id_delegacion] = delegation
        return delegation

    def save(self, delegation: Delegation) -> Delegation:
        self.items[delegation.id_delegacion] = delegation
        return delegation


class MemoryAudits:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []
        self.changes: list[ResultChange] = []

    def add(self, event: AuditEvent) -> None:
        self.events.append(event)

    def list_changes(self, id_orden: int) -> list[ResultChange]:
        return list(self.changes)


class FakeCalculation:
    def calculate(self, strategy: str, inputs: dict[str, object]) -> CalculationOutcome:
        assert strategy == "FAKE"
        return CalculationOutcome(calculados={"calculado": inputs["manual"] * 2})


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 1, tzinfo=timezone.utc)


class FakePdf:
    def render_official(self, order: Order, results: list[ResultVersion]) -> bytes:
        return f"{order.folio}:{len(results)}".encode()


def test_main_patient_order_draft_calculation_officialization_and_correction_flow() -> None:
    uow = MemoryUnitOfWork()
    patient = CrearPaciente(uow).execute(
        ci="CI-1",
        nombres="Ana",
        apellido_paterno="Pérez",
        fecha_nacimiento=date(1990, 1, 1),
        sexo="F",
        creado_por=7,
    )
    assert BuscarPaciente(uow).por_ci("CI-1", id_usuario=7) is patient
    patient = ActualizarPaciente(uow).execute(patient.id_paciente, 7, {"telefono": "555-0101"})
    assert patient.telefono == "555-0101"

    with pytest.raises(ValidationError, match="al menos un estudio"):
        CrearOrden(uow).execute(id_paciente=patient.id_paciente, id_usuario_autor=7, ids_estudio=[])
    assert uow.orders.folio_count == 0

    order = CrearOrden(uow).execute(
        id_paciente=patient.id_paciente,
        id_usuario_autor=7,
        ids_estudio=[13, 13],
        pieza="Sala 1",
    )
    assert order.folio == "LIS-00000001"
    assert len(order.estudios) == 1
    assigned_id = order.estudios[0].id_orden_estudio

    GuardarBorrador(uow).execute(
        id_orden_estudio=assigned_id,
        id_usuario=7,
        entradas={"manual": Decimal("4")},
    )
    calculated = CalcularEstudio(uow, FakeCalculation()).execute(assigned_id, 7)
    assert calculated.calculados["calculado"] == Decimal("8")
    OficializarOrden(uow, FakeCalculation(), FixedClock()).execute(order.id_orden, 7)

    version_one = uow.results.get_latest(assigned_id)
    assert order.estado is OrderStatus.OFFICIAL
    assert version_one.numero_version == 1
    assert version_one.estado is ResultStatus.OFFICIAL
    assert version_one.snapshot_completo["referencias"]["manual"] == "1-10 mg/dL"
    assert version_one.snapshot_completo["configuracion"]["captura"] == "entrada manual"
    original_inputs = dict(version_one.entradas)
    with pytest.raises(InvalidState, match="ya no está pendiente de edición"):
        GuardarBorrador(uow).execute(
            id_orden_estudio=assigned_id,
            id_usuario=7,
            entradas={"manual": Decimal("9")},
        )
    assert version_one.entradas == original_inputs

    version_two = CrearCorreccion(uow, FakeCalculation()).execute(
        id_orden_estudio=assigned_id,
        id_usuario=7,
        motivo="Corrección por error de transcripción.",
        nuevas_entradas={"manual": Decimal("5")},
    )
    assert version_two.numero_version == 2
    assert version_two.estado is ResultStatus.DRAFT
    assert version_one.entradas == original_inputs

    OficializarOrden(uow, FakeCalculation(), FixedClock()).execute(order.id_orden, 7)
    assert version_one.estado is ResultStatus.SUPERSEDED
    assert version_two.estado is ResultStatus.OFFICIAL
    assert version_two.snapshot_completo["entradas"]["manual"] == Decimal("5")
    assert len(ConsultarVersiones(uow).execute(assigned_id, 7)) == 2
    assert ConsultarCambios(uow).execute(order.id_orden, 7)
    assert any(change.id_parametro == 130 for change in uow.results.changes)
    assert len(ConsultarHistorial(uow).execute(7, HistoryFilter())) == 1
    assert GenerarPDF(uow, FakePdf()).execute(order.id_orden) == b"LIS-00000001:1"

    MoverOrdenAPapelera(uow, FixedClock()).execute(order.id_orden, 7, "Orden duplicada.")
    with pytest.raises(InvalidState, match="orden oficial"):
        GenerarPDF(uow, FakePdf()).execute(order.id_orden)
    RestaurarOrden(uow, FixedClock()).execute(order.id_orden, 7)
    assert order.estado is OrderStatus.OFFICIAL


def test_study_delegation_requires_acceptance_and_restricts_other_studies() -> None:
    uow = MemoryUnitOfWork()
    patient = CrearPaciente(uow).execute(
        ci="CI-2",
        nombres="Luis",
        apellido_paterno="López",
        fecha_nacimiento=date(1985, 4, 3),
        sexo="M",
        creado_por=7,
    )
    order = CrearOrden(uow).execute(
        id_paciente=patient.id_paciente,
        id_usuario_autor=7,
        ids_estudio=[13, 14],
    )
    delegated = DelegarEstudio(uow).execute(
        id_orden=order.id_orden,
        id_usuario_autor=7,
        id_usuario_colaborador=8,
        ids_estudio=[13],
    )
    assigned = {study.id_estudio: study for study in order.estudios}

    with pytest.raises(PermissionDenied):
        GuardarBorrador(uow).execute(
            id_orden_estudio=assigned[13].id_orden_estudio,
            id_usuario=8,
            entradas={"manual": Decimal("1")},
        )

    AceptarDelegacion(uow).execute(delegated.id_delegacion, 8)
    GuardarBorrador(uow).execute(
        id_orden_estudio=assigned[13].id_orden_estudio,
        id_usuario=8,
        entradas={"manual": Decimal("1")},
    )
    with pytest.raises(PermissionDenied, match="este estudio"):
        GuardarBorrador(uow).execute(
            id_orden_estudio=assigned[14].id_orden_estudio,
            id_usuario=8,
            entradas={"manual": Decimal("2")},
        )
    finalized = FinalizarDelegacion(uow).execute(delegated.id_delegacion, 8)
    assert not finalized.activa


def test_calculation_engine_routes_to_existing_clinical_strategy() -> None:
    outcome = CalculationEngine().calculate(
        "HEPATOGRAMA",
        {"bilirrubina_total": Decimal("1.80"), "bilirrubina_directa": Decimal("0.40")},
    )

    assert outcome.calculados == {"bilirrubina_indirecta": Decimal("1.40")}
    assert outcome.advertencias == ()

    with pytest.raises(ValidationError, match="parámetro requerido"):
        CalculationEngine().calculate("HEPATOGRAMA", {"bilirrubina_total": Decimal("1")})
    with pytest.raises(ValidationError, match="números finitos"):
        CalculationEngine().calculate("HEPATOGRAMA", {
            "bilirrubina_total": Decimal("Infinity"),
            "bilirrubina_directa": Decimal("0"),
        })


def test_pending_orders_cannot_generate_official_pdf_and_correction_requires_reason() -> None:
    uow = MemoryUnitOfWork()
    patient = CrearPaciente(uow).execute(
        ci="CI-4",
        nombres="Eva",
        apellido_paterno="Ríos",
        fecha_nacimiento=date(1992, 5, 6),
        sexo="F",
        creado_por=7,
    )
    order = CrearOrden(uow).execute(
        id_paciente=patient.id_paciente,
        id_usuario_autor=7,
        ids_estudio=[13],
    )

    with pytest.raises(InvalidState, match="orden oficial"):
        GenerarPDF(uow, FakePdf()).execute(order.id_orden)
    with pytest.raises(ValidationError, match="10 caracteres"):
        CrearCorreccion(uow, FakeCalculation()).execute(
            id_orden_estudio=order.estudios[0].id_orden_estudio,
            id_usuario=7,
            motivo="mal",
            nuevas_entradas={"manual": Decimal("2")},
        )


def test_only_original_author_can_officialize_and_domain_has_no_framework_imports() -> None:
    uow = MemoryUnitOfWork()
    patient = CrearPaciente(uow).execute(
        ci="CI-5",
        nombres="Noé",
        apellido_paterno="Díaz",
        fecha_nacimiento=date(1991, 3, 2),
        sexo="M",
        creado_por=7,
    )
    order = CrearOrden(uow).execute(
        id_paciente=patient.id_paciente,
        id_usuario_autor=7,
        ids_estudio=[13],
    )
    order_study_id = order.estudios[0].id_orden_estudio
    GuardarBorrador(uow).execute(
        id_orden_estudio=order_study_id,
        id_usuario=7,
        entradas={"manual": Decimal("2")},
    )
    CalcularEstudio(uow, FakeCalculation()).execute(order_study_id, 7)

    with pytest.raises(PermissionDenied, match="autor original"):
        OficializarOrden(uow, FakeCalculation(), FixedClock()).execute(order.id_orden, 8)
    assert order.estado is OrderStatus.DRAFT

    roots = [Path(__file__).parents[2] / "app" / "domain", Path(__file__).parents[2] / "app" / "application"]
    forbidden = ("fastapi", "sqlalchemy", "postgres", "react")
    for root in roots:
        for source in root.rglob("*.py"):
            content = source.read_text(encoding="utf-8").lower()
            assert not any(name in content for name in forbidden), source


def test_studies_can_be_added_and_removed_but_order_cannot_become_empty() -> None:
    uow = MemoryUnitOfWork()
    patient = CrearPaciente(uow).execute(
        ci="CI-3",
        nombres="Sara",
        apellido_paterno="Vega",
        fecha_nacimiento=date(1994, 7, 8),
        sexo="F",
        creado_por=7,
    )
    order = CrearOrden(uow).execute(
        id_paciente=patient.id_paciente,
        id_usuario_autor=7,
        ids_estudio=[13, 14],
    )

    QuitarEstudio(uow).execute(order.id_orden, 14, 7)
    assert [study.id_estudio for study in order.estudios] == [13]
    with pytest.raises(InvalidState, match="al menos un estudio"):
        QuitarEstudio(uow).execute(order.id_orden, 13, 7)

    AgregarEstudio(uow).execute(order.id_orden, 14, 7)
    assert {study.id_estudio for study in order.estudios} == {13, 14}