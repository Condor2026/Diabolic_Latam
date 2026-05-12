# Diabolical Latam V6.0

**Version 6.0 | License: MIT | Python 3.11 | OSINT: Pasivo | ASIN: Terranio | Compliance: ISO**

---

## Diabolical Latam es una herramienta OSINT pasiva y analítica que monitoriza 42 periódicos digitales de 18 países latinoamericanos (desde Argentina hasta México, pasando por Colombia, Chile, Perú, Brasil, etc.) para detectar, clasificar y visualizar patrones delictivos.

No guarda datos personales, solo titulares, fechas y ubicaciones por país. Filosofía: *"Un gran poder conlleva una gran responsabilidad"*.

---

### Índice
- ¿Qué hace DIABOLIC?
- Características clave
- Tecnología y arquitectura
- Instalación y uso
- Modo terminal (10 comandos)
- Modo web interactivo
- Fuentes monitorizadas
- Países cubiertos
- Léxico criminal latinoamericano
- Tipo de OSINT y metodología
- Ética, legalidad y protección de datos
- Contribuciones y futuro
- Licencia

---

### ¿Qué hace DIABOLIC?

DIABOLIC automatiza el proceso de scraping de noticias de sucesos de medios locales y nacionales de Latinoamérica. En lugar de leer docenas de periódicos cada día, la herramienta:

- Extrae automáticamente titulares, fechas, fuentes y ubicación geográfica (país) de noticias relacionadas con delitos.
- Clasifica los incidentes en categorías (robo, estafa, narcotráfico, violencia, asesinato, violación, extorsión, mafia, corrupción, desaparición, ciberdelito…).
- Almacena los datos localmente en formato JSON, sin guardar ningún dato personal.
- Analiza tendencias temporales (7, 30, 90 días) y distribuciones por país y tipo de delito.
- Detecta conexiones entre incidentes: misma zona, fechas cercanas, mismo modus operandi (lanzazo, motochorro, alunicero, vacuna, gota a gota, sicariato…) que pueden indicar una misma banda u organización criminal.
- Visualiza los resultados mediante una interfaz web interactiva con gráficos de barras y filtros dinámicos.
- Exporta los datos a CSV o JSON para análisis externos.

---

### Características clave

🔁 **Rotación de User‑Agent** – Evita bloqueos de los periódicos simulando diferentes navegadores y versiones en cada petición.

🧠 **Paginación inteligente** – Prueba automáticamente hasta 12 formatos diferentes de paginación y recuerda el que funciona para cada dominio.

🔎 **Detector automático de URLs** – Si una URL de un periódico deja de funcionar, el sistema busca rutas alternativas (policiales, sucesos, seguridad, judicial, etc.) y actualiza la configuración.

📊 **Clasificación avanzada de delitos** – Utiliza una lista amplia de palabras clave, incluyendo jerga local latinoamericana (lanzazo, motochorro, vacuna, gota a gota, sicariato, feminicidio, fosa clandestina, coima, testaferro…). Se puede extender fácilmente.

🔗 **Conexiones entre incidentes** – Por tipo y país (ej. 5 robos en México en 7 días). Por modus operandi (detecta repetición de términos como “lanzazo” o “vacuna”). Frecuencia temporal (incidentes/día).

🌐 **Interfaz web interactiva** – Gráficos de barras por país y tipo de delito. Filtros por período (últimos 7, 30, 90 días). Lista de los últimos 20 incidentes. Botones para actualizar datos y exportar JSON/CSV.

🖥️ **Menú terminal completo** – 10 comandos que permiten ejecutar todas las funciones sin necesidad de abrir el navegador.

🌍 **Multilingüe** – Soporte español y portugués (selector al inicio).

---

### Tecnología y arquitectura

- **Lenguaje:** Python 3.8+
- **Framework web:** Flask (servidor ligero)
- **Scraping:** Requests + BeautifulSoup4
- **Almacenamiento:** JSON local (sin bases de datos externas)
- **Estructura modular:**
  - `DetectorURLs`: encargado de verificar y corregir URLs de periódicos.
  - `GestorDatos`: carga, guarda y procesa los incidentes.
  - `ExtractorNoticias`: realiza el scraping con rotación de User‑Agent y paginación inteligente.
- **Colores en terminal:** Códigos ANSI para una experiencia visual atractiva.

---

### Instalación y uso

**Requisitos previos:** Python 3.8 o superior, git, conexión a Internet.

#### Opción 1: En Termux (Android)

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install requests beautifulsoup4 flask
git clone https://github.com/Condor2026/Diabolic_Latam
cd Diabolic_Latam
python Diabolic_Latam.py
