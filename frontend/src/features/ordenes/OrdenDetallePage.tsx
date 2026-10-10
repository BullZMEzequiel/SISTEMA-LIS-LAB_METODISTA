import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ordenesService } from "../../services/ordenesService";
import type { OrdenDetalle, OrdenEstudio, ResultadoVersion } from "../../services/ordenesService";
import { catalogoService } from "../../services/catalogoService";
import type { EstudioConParametros, Parametro } from "../../services/catalogoService";

type EntradaValor = string;

export function OrdenDetallePage() {
  const { id } = useParams<{ id: string }>();
  const idOrden = Number(id);

  const [orden, setOrden] = useState<OrdenDetalle | null>(null);
  const [indice, setIndice] = useState(0);
  const [definicion, setDefinicion] = useState<EstudioConParametros | null>(null);
  const [entradas, setEntradas] = useState<Record<string, EntradaValor>>({});
  const [resultado, setResultado] = useState<ResultadoVersion | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finalizando, setFinalizando] = useState(false);

  // Carga inicial de la orden
  useEffect(() => {
    ordenesService.obtenerOrden(idOrden).then(setOrden).catch(() => setError("No se pudo cargar la orden."));
  }, [idOrden]);

  const estudioActual: OrdenEstudio | undefined = orden?.estudios[indice];

  // Al cambiar de estudio, carga su definición de parámetros y limpia el formulario
  useEffect(() => {
    if (!estudioActual) return;
    setDefinicion(null);
    setResultado(null);
    setEntradas({});
    setError(null);
    catalogoService
      .parametrosDeEstudio(estudioActual.id_estudio)
      .then((def) => {
        setDefinicion(def);
        const iniciales: Record<string, EntradaValor> = {};
        def.parametros
          .filter((p) => p.tipo_campo !== "CALCULADO_AUTOMATICO")
          .forEach((p) => { iniciales[p.codigo.toLowerCase()] = ""; });
        setEntradas(iniciales);
      })
      .catch(() => setError("No se pudo cargar la definición del estudio."));
  }, [estudioActual?.id_estudio]);

  function actualizarEntrada(codigo: string, valor: string) {
    setEntradas((prev) => ({ ...prev, [codigo]: valor }));
  }

  async function guardarYCalcular() {
    if (!estudioActual) return;
    setCargando(true);
    setError(null);
    try {
      // 1. Convierte strings a número donde aplica, guarda borrador
      const entradasNumericas: Record<string, string | number | boolean | null> = {};
      Object.entries(entradas).forEach(([codigo, valor]) => {
        entradasNumericas[codigo] = valor === "" ? null : (isNaN(Number(valor)) ? valor : Number(valor));
      });
      await ordenesService.guardarBorrador(idOrden, estudioActual.id_estudio, entradasNumericas);

      // 2. Si el estudio tiene estrategia de cálculo, calcula. Si no (Química,
      //    Electrolitos, EGO), el guardado del borrador ya es el resultado final.
      if (definicion?.estrategia_calculo) {
        const calculado = await ordenesService.calcularEstudio(idOrden, estudioActual.id_estudio);
        setResultado(calculado);
      } else {
        setResultado({
          id_resultado_version: null,
          id_orden_estudio: estudioActual.id_orden_estudio ?? 0,
          numero_version: 1,
          estado: "BORRADOR",
          entradas: entradasNumericas,
          calculados: {},
          advertencias: [],
        });
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "No se pudo calcular. Revise los valores ingresados.");
    } finally {
      setCargando(false);
    }
  }

  function siguiente() {
    if (orden && indice < orden.estudios.length - 1) setIndice(indice + 1);
  }
  function anterior() {
    if (indice > 0) setIndice(indice - 1);
  }

  async function finalizarOrden() {
    setFinalizando(true);
    setError(null);
    try {
      const actualizada = await ordenesService.oficializarOrden(idOrden);
      setOrden(actualizada);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "No se pudo oficializar la orden. Verifique que todos los estudios tengan resultado.");
    } finally {
      setFinalizando(false);
    }
  }

  if (!orden) return <div className="p-6">Cargando orden...</div>;

  const esUltimo = indice === orden.estudios.length - 1;
  const camposEntrada = (definicion?.parametros ?? []).filter((p: Parametro) => p.tipo_campo !== "CALCULADO_AUTOMATICO");
  const camposCalculados = (definicion?.parametros ?? []).filter((p: Parametro) => p.tipo_campo === "CALCULADO_AUTOMATICO");

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Orden {orden.folio}</h1>
      <p className="text-gray-500 mb-4">Estado: {orden.estado} · Estudio {indice + 1} de {orden.estudios.length}</p>

      {error && <p className="text-red-600 mb-3">{error}</p>}

      {orden.estado === "OFICIAL" ? (
        <p className="text-green-700 font-medium">Esta orden ya fue oficializada y quedó visible en el historial.</p>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {/* Panel izquierdo: formulario */}
          <div className="border rounded p-4">
            <h2 className="font-semibold mb-3">{definicion?.nombre ?? "Cargando..."}</h2>
            {camposEntrada.map((p) => (
              <div key={p.codigo} className="mb-3">
                <label className="block text-sm text-gray-600 mb-1">
                  {p.nombre} {p.unidad_medida ? `(${p.unidad_medida})` : ""} {p.obligatorio && "*"}
                </label>
                <input
                  type="text"
                  value={entradas[p.codigo.toLowerCase()] ?? ""}
                  onChange={(e) => actualizarEntrada(p.codigo.toLowerCase(), e.target.value)}
                  className="border rounded px-3 py-2 w-full"
                />
              </div>
            ))}
            <button
              type="button"
              onClick={guardarYCalcular}
              disabled={cargando}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 mt-2"
            >
              {cargando ? "Calculando..." : "Guardar y calcular"}
            </button>
          </div>

          {/* Panel derecho: informe preliminar */}
          <div className="border rounded p-4 bg-gray-50">
            <h2 className="font-semibold mb-3">Informe preliminar</h2>
            {!resultado && <p className="text-gray-400">Aún sin resultados para este estudio.</p>}
            {resultado && (
              <>
                {camposCalculados.map((p) => (
                  <div key={p.codigo} className="flex justify-between border-b py-1 text-sm">
                    <span>{p.nombre}</span>
                    <strong>{String(resultado.calculados[p.codigo.toLowerCase()] ?? "—")} {p.unidad_medida}</strong>
                  </div>
                ))}
                {resultado.advertencias.length > 0 && (
                  <div className="mt-3 text-amber-700 text-sm">
                    {resultado.advertencias.map((a, i) => <p key={i}>⚠ {a}</p>)}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {orden.estado !== "OFICIAL" && (
        <div className="flex justify-between mt-6">
          <button type="button" onClick={anterior} disabled={indice === 0}
            className="bg-gray-200 px-4 py-2 rounded disabled:opacity-50">
            ← Atrás
          </button>
          {esUltimo ? (
            <button type="button" onClick={finalizarOrden} disabled={finalizando}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50">
              {finalizando ? "Subiendo..." : "Finalizar y subir al historial"}
            </button>
          ) : (
            <button type="button" onClick={siguiente}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Siguiente →
            </button>
          )}
        </div>
      )}
    </div>
  );
}