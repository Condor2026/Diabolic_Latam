# ROADMAP — DIABOLIC LATAM

## ✅ Completado (v8.0)

- Clasificador v3 con scrub, términos fuertes/débiles, contexto policial y confianza por evento.
- Categorías internas: `fisico`, `rue`, `cyber`.
- Geolocalización LatAm (país → estado/departamento → ciudad) con desambiguación por fuente.
- Fusión multi-fuente (un duplicado suma fuentes y confianza).
- Alarma de violencia armada con panel dedicado y clusters de 24 h.
- Alertas oficiales en canal separado (DEA, OFAC, UNODC, UIF, GAFILAT…).
- Indicadores tipo crypto: RSI, SMA7/30, Bollinger, volatilidad, índice de amenaza.
- Pronóstico semanal (Holt), tendencias, hotspots, red y Sankey.
- Mapa enriquecido (Carto/OSM/HOT/Voyager/Light/satélite + calor/clusters/pulsos/hotspots/timelapse).
- Panel web con SSE, 7 pestañas, filtros, paginación y ampliación de gráficos.
- Centro de scan con consola en vivo y estado por fuente.
- Auto-descubrimiento de URLs y RSS de respaldo.
- Exportaciones JSON/CSV/HTML/GeoJSON.
- Migración automática del JSON de la v7.

## 🚧 En curso / próximo (v8.x)

- Caché de indicadores (`/api/indicators`) para no recalcular en cada ticker.
- Diagnóstico de fuentes con motivo de rechazo por candidato en el panel.
- Mejora del léxico regional (Brasil, Cono Sur).
- Documentación de la fórmula del índice de amenaza.

## 🔮 Futuro (v9+)

- Embeddings semánticos para fusión de duplicados (sustituir Jaccard por similitud coseno).
- Tests unitarios del clasificador y de `geolocalizar()`.
- Fallback local de CDNs (Leaflet, Chart.js, vis-network).
- Webhook / Telegram para la alarma (además de SSE).
- Más fuentes oficiales de la región.
- Traducción de la documentación a portugués e inglés.

## ❌ Descartado

- Bases de datos externas (se mantiene JSON local por simplicidad y portabilidad).
- Almacenamiento de datos personales.
