# CLAUDE CODE - INSTRUCCIONES PARA ESTE PROYECTO

## Lee esto primero

Eres copiloto de desarrollo para Carpintería 2.0, un sistema paramétrico CNC.

**Reglas**:
1. Siempre ejecuta código después de escribir (verifica que funciona)
2. Si cambias algo, haz commit automático con mensaje claro
3. Mantén la estructura modular: cambios en `src/` no afecten `cli.py`
4. Tests: siempre prueba nuevas features con `python cli.py`
5. DXF: valida que genere R2000 (no R2018) compatible Aspire V8.502

**Antes de empezar**:
- Lee `.claude/PROJECT.md` (contexto)
- Lee `.claude/ROADMAP.md` (qué hacer next)
- Lee `.claude/ARCHITECTURE.md` (estructura técnica)

**Workflow típico**:
```
Tú: "Necesito X feature"
↓
Yo: Leo PROJECT.md + ROADMAP.md
↓
Yo: Propongo solución (rápida)
↓
Tú: Aprobás o pedís cambios
↓
Yo: Implemento + ejecuto + commit
↓
Resultado: Feature lista + testeada
```

**Dónde buscar si necesito contexto**:
- Problema original: `PROJECT.md`
- Arquitectura: `ARCHITECTURE.md` 
- Próximos pasos: `ROADMAP.md`
- Decision log: `PROJECT.md` sección "Decisiones"
- Código modular: revisar `src/` correspondiente

**Si hay que hacer breaking change**:
- Avisá primero
- Referenciá decisión arquitectónica original
- Propone alternativa si es posible
- Justificá por qué el cambio vale la pena

**Commits** (siempre con mensaje claro):
```
git add -A
git commit -m "Feature: nesting v2 con Simulated Annealing"
git push origin main
```

**Errores comunes que evitar**:
- ❌ Cambiar formato DXF sin testear en Aspire
- ❌ Agregar dependencias sin revisar requirements.txt
- ❌ Modificar classes de furniture_core sin actualizar todas las subclases
- ❌ Asumir dimensiones de placa sin verificar

**Éxito = Feature implementada + testeada + commiteada**
