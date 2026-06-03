# 📍 Hoja de ruta de DIABOLIC (LATAM)

Este documento describe las direcciones de desarrollo, mejoras planificadas y funcionalidades futuras para **DIABOLIC LATAM**.  
La hoja de ruta es orientativa y puede cambiar según las necesidades de la comunidad y los principios éticos del proyecto.

---

## 🟢 Versión actual (7.0)

- ✅ Scraping de **más de 70 periódicos de 18 países latinoamericanos**.
- ✅ Enfoque especial en **narcotráfico, crimen organizado, violencia y corrupción**.
- ✅ Rotación de User‑Agent y paginación inteligente.
- ✅ Detector automático de URLs rotas.
- ✅ Clasificación de delitos con **léxico criminal latinoamericano** (español y portugués).
- ✅ Conexiones entre incidentes (opción 3 del menú).
- ✅ Interfaz web con gráficos y filtros (7/30/90 días).
- ✅ Exportación a JSON y CSV.
- ✅ Menú terminal completo (10 comandos).
- ✅ Código ético, sin almacenamiento de datos personales.
- ✅ Cumplimiento con **LGPD** (Brasil) y principios **GDPR**.
- ✅ Soporte multiplataforma: Termux, Linux, Windows.
- ✅ Banner con filosofía Spiderman.

---

## 🟡 Próximas mejoras (corto plazo – 3 meses)

### 1. Mapas de calor regionales
- Visualización geográfica de incidentes sobre mapas de Latinoamérica (Leaflet / OpenStreetMap).
- Geolocalización por país, estado/provincia y municipio.

### 2. Alertas personalizables
- Sistema de alertas por Telegram, Discord o correo electrónico para patrones relevantes (ej. aumento de violencia en una región específica).
- Configuración de umbrales por el usuario.

### 3. Nuevas fuentes de datos
- Ampliar base de periódicos a **más de 100 fuentes**.
- Incorporar boletines oficiales de gobiernos latinoamericanos.
- Agregar canales de Twitter/X de fiscalías, policías y ministerios públicos de la región.

### 4. Léxico criminal enriquecido
- Expansión continua del diccionario de jerga criminal latinoamericana.
- Soporte para términos de **narcotráfico y crimen organizado** específicos de cada país (narcocorredores, "halcones", "sicariato", etc.).

### 5. Mejora en la detección de conexiones
- Expandir la opción 3 con gráficos de red que visualicen relaciones entre incidentes.
- Añadir nivel de confianza (bajo/medio/alto) en los patrones detectados.

---

## 🟠 Funcionalidades en estudio (medio plazo – 6 meses)

### 6. API pública
- Endpoint REST para consultar incidentes, estadísticas y patrones.
- Documentación Swagger/OpenAPI.

### 7. Instalación mediante Docker
- Contenedor Docker para facilitar el despliegue en servidores.
- Orquestación con docker-compose.

### 8. Análisis predictivo básico
- Modelos de machine learning ligeros para estimar tendencias futuras.
- Siempre con datos agregados y sin predecir individuos.

### 9. Integración con herramientas de inteligencia de código abierto
- Exportación directa a Maltego, OpenCTI o MISP.

### 10. Verificación de fuentes
- Mecanismo automático que compruebe la fiabilidad de los periódicos y detecte posibles fake news.

---

## 🔴 Ideas a largo plazo (1 año o más)

### 11. Colaboración con universidades latinoamericanas
- Programas de investigación criminológica usando datos anonimizados de DIABOLIC LATAM.

### 12. Móvil nativo
- Aplicación Android/iOS que consuma la API pública.

### 13. Comunidad de contribuidores en español/portugués
- Creación de una guía de contribución detallada y un canal de comunicación (Discord/Matrix) para desarrolladores hispanohablantes y lusófonos.

### 14. Ampliación a Centroamérica y Caribe
- Inclusión de fuentes de prensa de países centroamericanos y del Caribe aún no cubiertos.

---

## 📌 Cómo proponer nuevas ideas

Si quieres sugerir una funcionalidad, reportar un error o participar en el desarrollo, abre un *issue* en el repositorio de GitHub con la etiqueta `enhancement` o `roadmap`.  
Toda contribución debe respetar el [Código de Conducta](CODE_OF_CONDUCT.md) y los principios éticos del proyecto.

---

*Última actualización: marzo 2026*  
**SpectrumSecurity** – *OSINT ético al servicio de la ciudadanía* 🔥
