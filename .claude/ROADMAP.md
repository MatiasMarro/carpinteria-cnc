# ROADMAP.md - PRÓXIMOS PASOS PRIORIZADOS

## FASE 1 - VALIDACIÓN EN PRODUCCIÓN (ESTA SEMANA)

**Objetivo**: Cortar 3-5 muebles reales con el sistema, registrar tiempos.

### ✅ v1.0 - YA HECHO
- Sistema funcional con nesting integrado
- DXF R2000 compatible Aspire V8.502
- CLI: escritorio, estantería, preconfigurados

### 🔄 INMEDIATO (Esta semana)
- [ ] Cortar 3 muebles con DXFs generados
- [ ] Registrar tiempo real vs estimado
- [ ] Registrar errores/gaps en Aspire
- [ ] Feedback a Claude si algo no funciona
- [ ] Comprobar accesorios (minifix, tornillos, correderas)

**Success**: Sistema funciona en producción real, tiempos calibrados

---

## FASE 2 - OPTIMIZACIÓN (1-2 semanas después)

Prioridad: Máximo impacto / mínimo esfuerzo

### Tier 1 - CRÍTICO (3-5 días)
```
[ ] Calibrador de tiempos
    - Input: CSV con tiempos reales (5-10 muebles)
    - Output: Factores ajuste (1.2x, 0.85x, etc)
    - Impacto: Estimador 95%+ preciso
    
[ ] DB sobrantes
    - SQLite: tabla sobrantes (placa_id, ancho, alto, estado)
    - Integración nesting: consultar antes de usar placa nueva
    - Impacto: -5% material = $1,200/mes en 12 muebles/mes
    
[ ] Validador Aspire
    - Script: check si DXF se abre correctamente
    - Impacto: catch problemas antes de producción
```

### Tier 2 - IMPORTANTE (1 semana)
```
[ ] Dashboard Streamlit
    - Input: sliders (ancho, profundidad, altura, mecha)
    - Output: preview nesting + costo + tiempo + accesorios
    - Impacto: UX mejor que CLI, menos errores input
    
[ ] Más muebles
    - Mesita noche (40x40x50cm, 1 cajón)
    - Cajonera (50x50x100cm, 3 cajones)
    - Placard pequeño (80x200x30cm, 4 estantes)
    - Impacto: Expandir ofertas, +2-3 muebles/mes potencial
```

### Tier 3 - NICE TO HAVE (2 semanas)
```
[ ] Reportes PDF
    - Jinja2 templates: cotización + lista accesorios
    - Impacto: Presentación profesional, menos emails

[ ] Nesting v2 (opcional)
    - Simulated Annealing para exploración global
    - Impacto: 86% → 92%+ eficiencia (marginal)
```

---

## FASE 3 - ESCALADO (1-2 meses después)

```
[ ] Integración Fusion 360
    - Add-in Python: leer parámetros de modelo 3D
    - Impacto: Saltarse CLI, flujo Fusion→DXF automático

[ ] Histórico datos
    - Todas las órdenes en CSV: cliente, mueble, tiempo, costo real
    - Analytics: qué mueble es más rentable, tendencias

[ ] Sistema órdenes
    - Form simple: cliente, mueble, parámetros
    - Output: cotización + proyecto reservado
    - Impacto: Más profesional, tracking de órdenes
```

---

## FASE 4 - AUTOMATIZACIÓN AVANZADA (3-6 meses)

```
[ ] IoT en CNC
    - Raspberry Pi + Mach3 API
    - Tracking tiempos reales, alertas de error
    - Impacto: Histórico preciso, feedback automático

[ ] ML predicción
    - Entrenar con histórico (cliente, mueble, params → tiempo real)
    - Impacto: Estimador preciso sin mantenimiento

[ ] Dashboard producción
    - Kanban digital: órdenes → en progreso → listo
    - Impacto: Gestión de equipo (para cuando crezcan)
```

---

## DECISIÓN INMEDIATA

**¿Por dónde empezar?**

**Opción A: Rápido** (RECOMENDADO para ahora)
1. Cortar 5 muebles → registrar tiempos
2. Calibrador de tiempos (1 día)
3. DB sobrantes (2 días)
4. Listo para escalar → 8-12 muebles/mes

**Opción B: Fancy**
1. Dashboard Streamlit primero
2. Después el resto

**Mi recomendación**: **Opción A**
- Validación real > bonita UI
- Sobrantes ya ahorran $1,200/mes
- 4-5 días = ROI instantáneo

---

## TRACKING DE PROGRESO

```
v1.0 ✅ DONE
├─ Core system
├─ DXF R2000 compatible
├─ CLI funcional
└─ 2 tipos muebles

v1.1 (NEXT 1-2 semanas)
├─ Calibrador tiempos
├─ DB sobrantes
└─ Dashboard Streamlit

v1.2 (Próximas 2-4 semanas)
├─ +3 muebles
├─ Reportes PDF
└─ Nesting v2 (opcional)

v2.0 (Mes 2-3)
├─ Integración Fusion
├─ Histórico analytics
└─ Sistema órdenes

v3.0 (Mes 3-6)
├─ IoT + RPi
├─ ML predicción
└─ Dashboard kanban
```

---

## CÓMO PEDIR FEATURES

Cuando necesites algo nuevo en Claude Code, sé específico:

```
"Necesito agregar Mesita noche (40x40x50cm, 1 cajón).
Mismos materiales y union que escritorio."

vs.

"Agrega más muebles"
```

**Mejor aún**:
```
"Agrega Mesita noche: 40x40x50cm, 1 cajón (estándar), materiales = escritorio.
Preconfigurados: _standard (default), _roble (futuro).
Test: python cli.py usar mesita_standard --exportar"
```

---

## Métricas de éxito

| Métrica | Actual | Target | Timeline |
|---------|--------|--------|----------|
| Muebles/mes | 3 | 12 | 2 meses |
| Tiempo diseño | 45min | 5min | YA |
| Nesting manual | 30-40min | 0min | YA |
| Eficiencia material | 75% | 90% | Fase 2 |
| Estimador error | ±20% | ±5% | Fase 2 |

---

**Siguiente paso**: Abre Claude Code, carga el proyecto, y escribe en chat:

```
He descargado el proyecto. Quiero empezar con Phase 2:
1. Calibrador de tiempos
2. DB sobrantes

¿Por cuál empiezo?
```

Claude tendrá el contexto de `.claude/` y sabrá exactamente qué hacer.
