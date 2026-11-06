# Política de seguridad — DIABOLIC LATAM

## Versiones soportadas

| Versión | Soporte |
|---------|---------|
| 8.x     | ✅ Sí   |
| ≤ 7.x   | ❌ No   |

## Cómo reportar una vulnerabilidad

Abre un **issue privado** en el repositorio o contacta con el mantenedor (Condor2026) indicando:

- Versión afectada.
- Descripción del problema.
- Pasos para reproducirlo.
- Impacto potencial.

No publiques exploits antes de que se haya corregido.

## Superficie de ataque conocida

DIABOLIC LATAM es una herramienta local, pero expone un panel web Flask (por defecto en `127.0.0.1:5013`). Puntos a tener en cuenta:

### Autenticación
- **No hay autenticación.** Si se ejecuta con `--host 0.0.0.0`, cualquiera en la red local puede:
  - Lanzar scans (`/api/scan`, `/api/verify`).
  - Disparar la alarma (`/api/alarm/test`).
  - Añadir fuentes (`/api/sources/add`).
  - Modificar el umbral de alarma (`/api/alarm/config`).
  - Cambiar el nivel de alerta regional (`/api/vigipirate`).

**Recomendación**: mantener `127.0.0.1` salvo que se use un proxy autenticado por delante.

### CSRF
- Todos los POST exigen la cabecera `X-DF: 1`. Esto impide que una página de terceros abierta en el mismo navegador lance acciones sobre `localhost` sin permiso. **No es autenticación**: un `curl` directo sigue funcionando.

### XSS
- El frontend escapa todo con `esc()` y solo permite `http(s)://` en enlaces generados (`safeUrl()`). Los titulares provienen de fuentes externas, así que se tratan como no confiables.

### Dependencias externas (CDN)
- El panel carga Leaflet, Chart.js, vis-network y Google Fonts desde CDN. Si el usuario opera en red restringida o quiere evitar dependencias externas, debe alojarlos localmente y ajustar las URLs en `HTML_TEMPLATE`.

### Scraping
- El scraper realiza peticiones HTTP a sitios de terceros. Por defecto **no** respeta `robots.txt` (heredado de la v1); se puede activar con `--robots`.
- Las peticiones incluyen user-agents rotativos y delays aleatorios, pero no hay proxies.

### Almacenamiento
- Los datos se guardan en JSON local (`diabolic_narco.json`, `estado_fuentes_narco.json`, `url_cache_narco.json`, `diabolic_latam.log`). No se cifran. No contienen datos personales, solo titulares, fechas, ubicación aproximada y tipo de delito.

## Buenas prácticas

- No exponer el panel a Internet sin autenticación.
- Revisar `estado_fuentes_narco.json` si se añaden fuentes desde el panel: el campo `url` se adopta automáticamente.
- Mantener las dependencias actualizadas (`pip install -U flask requests beautifulsoup4`).
