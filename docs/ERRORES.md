# Bloqueos y decisiones de avance

Este archivo registra bloqueos que impiden validar un criterio de fase, qué observación los detectó, su impacto, la decisión tomada y el punto futuro en que deben resolverse. Se conserva el historial aunque el trabajo continúe en fases independientes.

## B-001 — Fase 7: relaciones clínicas de paneles ausentes

- **Detectado:** 2026-10-04, durante la Fase 7 — Órdenes, paneles y estudios.
- **Evidencia:** `paneles` contiene los dos paneles requeridos, pero `panel_estudios` está vacío; el catálogo tiene cuatro estudios semilla frente a catorce hojas clínicas en el Excel.
- **Impacto:** En la base actual, elegir `HC-QMC-SEROL-EGO` o `HC-QMC-SERO-PROT` no agrega estudios. No se puede validar con el catálogo real la selección automática ni confirmar la definición de los catorce estudios.
- **Causa:** No hay una relación hoja → estudio → panel aprobada; las fases 0–4 prohíben inferir composición, parámetros o relaciones clínicas.
- **Acción intentada:** Implementar la selección de panel mediante la relación `panel_estudios`, exponer la consulta de panel y añadir prueba de integración con una fila temporal revertida al terminar la prueba.
- **Resultado:** El mecanismo funciona con una relación válida y la prueba pasa; el estado de producción sigue sin composición clínica.
- **Decisión:** No insertar asociaciones supuestas ni alterar fórmulas. Diferir el mapeo al trabajo de catálogo clínico con validación del laboratorio. Avanzar a Fase 8, que opera sobre estudios explícitos de una orden y no requiere decidir la composición de paneles.
- **Resolver cuando:** Se apruebe el inventario clínico de las catorce hojas, su identidad como estudios, su pertenencia a los paneles y sus parámetros/rangos; cargar la configuración validada y probar los paneles reales.
- **Estado:** abierto / diferido.
