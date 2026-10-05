# Fase 4: Migración y validación de cálculos clínicos

**Fecha:** 2026-10-01

**Fuentes comparadas:** `1. FORMATO CENTRAL 2026.xlsx`, estrategias `backend/app/domain/calculations/` y tests unitarios existentes.

## Resultado

Se conservaron las cuatro estrategias ya implementadas y sus fórmulas. No se modificó ninguna fórmula clínica. `CalculationEngine` las integra por identificador de estrategia, convierte entradas a `Decimal`, propaga advertencias y expresa parámetros faltantes/valores no numéricos como errores de dominio.

La inspección del libro confirmó 19 pestañas: 14 clínicas con contenido, cuatro vacías y `VN`. Hay 42 fórmulas en total; varias son `NOW()`/`TODAY()` para fecha, no cálculos clínicos. Las estrategias clínicas actuales cubren Hemograma, Hepatograma, Perfil lipídico y Proteinograma. No se inventaron estrategias ni parámetros para las pestañas restantes.

## Comparación de estrategias existentes

| Estudio | Excel | Código y tests | Resultado |
| --- | --- | --- | --- |
| Hemograma | En `HC-QMC` y `HC-QMC-SEROL-EGO. `: `C10=107000*C12`, `C13=0.32*C12`, `D17:D21=C17:C21*C11`. En `HC-QMC-SERO-PROT` las celdas cambian, pero se conserva el patrón. `C17:C21` usa formato porcentual; `0.62` representa 62%. | `HemogramaStrategy`: factores `107000` y `0.32`, diferencial por glóbulos blancos y salida absoluta redondeada a entero. Tests verifican factores, valores absolutos, tolerancia y advertencia. | Las fórmulas/escala de entrada coinciden. La tolerancia 0.999–1.001 es validación del código, no una regla encontrada como fórmula en Excel; se conserva como comportamiento previo probado. |
| Hepatograma | `HC-QMC` y `HC-QMC-SEROL-EGO. `: `C41=C39-C40`; la celda usa formato numérico `0.0`. | `HepatogramaStrategy` resta bilirrubina directa de total y cuantiza a dos decimales. Test actual: 1.00−0.25 = 0.75. | La operación matemática coincide. Hay discrepancia de precisión/presentación: el Excel muestra un decimal, el código devuelve dos. Se documenta; no se cambió redondeo. |
| Perfil lipídico | `HC-QMC` y `HC-QMC-SEROL-EGO. `: `K43=K40/5`; `K42=K39-K41-K43`. Las celdas usan formato General. | `PerfilLipidicoStrategy` cuantiza VLDL a dos decimales y usa ese valor cuantizado al calcular LDL; luego redondea LDL a dos. Los tests actuales pasan, incluido el vector de regresión 164.5/102.4/0. | Discrepancia de precisión intermedia: Excel referencia el valor interno de K43 sin `ROUND`; el código redondea antes de restarlo. El vector existente no distingue ambas rutas. Pendiente de decisión clínica sobre la precisión oficial; fórmula intacta. |
| Proteinograma | `HC-QMC-SERO-PROT`: `G46=G42-G44`; `G48=G44/G46`. Las celdas son General, sin redondeo explícito. | `ProteinogramaStrategy` redondea globulina a dos decimales antes de calcular A/G y redondea A/G a dos. Test actual: 7.2−4.5 = 2.70 y 4.5/2.70 = 1.67. | Discrepancia de precisión intermedia y de salida: Excel divide el valor interno de G46 y no indica redondeo de G46/G48; el código cuantiza ambos. Pendiente de validación del laboratorio; no se ajustó. |

Los casos numéricos anteriores describen el contrato actual de tests/código. No reemplazan una validación de precisión clínica ni justifican cambiar el redondeo.

## Fórmulas adicionales del Excel

### QMC-ELEC

- `C25=C21-C23` es otra resta de bilirrubina indirecta.
- `H49=B47-G47-G51` tiene referencias a `B47` (“Colesterol”), `G47` (“HDL-COL:”) y `G51` (“VLDL-COL:”); el valor calculado almacenado en el XLSX es `#VALUE!`.
- `H51=B49/5` usa `B49`, que contiene la etiqueta “Trigliceridos”; el valor calculado almacenado es `#VALUE!`.

### ELECTROLITOS

- `C24=C20-C22` es otra resta de bilirrubina indirecta.
- `H48=B46-G46-G50` usa `B46` (“Colesterol”), `G46` (“HDL-COL:”) y `G50` (“VLDL-COL:”); el valor calculado almacenado es `#VALUE!`.
- `H50=B48/5` usa `B48`, la etiqueta “Trigliceridos”; el valor calculado almacenado es `#VALUE!`.

Estas fórmulas parecen referencias de columna/celda incorrectas, pero no se corrigieron ni se trasladaron a nuevas estrategias: la regla de esta fase exige documentar discrepancias y no inferir qué celdas numéricas quiso usar la bioquímica.

## Otras pestañas y configuración

Las hojas `ORINA`, `COPROLOGICO ` y `P.R. Ag NASAL` tienen fórmulas de fecha (`NOW()`/`TODAY()`), no fórmulas clínicas. `COAGULACION`, `TEST EMBARAZO`, `PANEL TOXICLOGICO`, `P.R HEPATITIS`, `SEROLOGIA` y `CURV TOLERANCIA` no contienen fórmulas. Las hojas/paneles restantes requieren modelar campos manuales, orden y referencias antes de crear estrategias.

La hoja `VN` tiene referencias y unidades, pero ninguna fórmula. No se cargaron todavía rangos ni parámetros. La base actual cuenta con cuatro estudios semilla y cero filas de parámetros/rangos; la configuración clínica completa pertenece a la fase de catálogo y requiere validar el mapeo de cada celda con el laboratorio.

## Pruebas

- `test_hemograma.py`, `test_hepatograma.py`, `test_perfil_lipidico.py`, `test_proteinograma.py`: conservados y ejecutados.
- Suite clínica enfocada más tests del `CalculationEngine`: **16 passed**.
- Suite completa del backend al cierre: **23 passed**, dos advertencias deprecadas de Passlib/Argon2.

## Discrepancias pendientes

1. Confirmar con el laboratorio la precisión/redondeo esperado de bilirrubina indirecta frente al formato de una cifra decimal en Excel.
2. Confirmar si VLDL debe conservar precisión completa al calcular LDL, o si el LIS debe redondearlo primero como hace la estrategia actual.
3. Confirmar si globulina y relación A/G deben conservar precisión completa o redondearse a dos decimales como hace el código actual/tests.
4. Corregir con la bioquímica las referencias inválidas de QMC-ELEC/ELECTROLITOS antes de añadir estrategias para esos paneles.
5. Mapear campos, unidades, orden y rangos `VN` de las otras hojas clínicas antes de completar el catálogo.

## Cambios de esta fase

- **Modificado:** contrato de `CalculationStrategy` para tipar resultados clínicos y advertencias.
- **Fórmulas clínicas modificadas:** ninguna.
- **Tests clínicos eliminados o cambiados:** ninguno.
- **Documento creado:** `docs/FASE_4_CALCULOS.md`.