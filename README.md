# DIABOLIC_LATAM v6.0

**Version 6.0 | License: MIT | Python 3.11 | OSINT: Pasivo | Scraping | Termux | Linux** | Android**

---

## DIABOLIC_LATAM es una herramienta OSINT pasiva y analítica diseñada para monitorizar automáticamente 42 periódicos digitales de 18 países latinoamericanos, extrayendo y procesando noticias de sucesos para detectar patrones delictivos, tendencias geográficas y conexiones entre incidentes.

Nace con una filosofía clara: *“Un gran poder conlleva una gran responsabilidad”*. Por eso su diseño prioriza la transparencia, la ética y el respeto a la privacidad. Soporta español y portugués.

---

### 📌 Índice
- [¿Qué hace DIABOLIC?](#-qué-hace-diabolic)
- [Características clave](#-características-clave)
- [Tecnología y arquitectura](#-tecnología-y-arquitectura)
- [Instalación y uso](#-instalación-y-uso)
- [Modo terminal (10 comandos)](#-modo-terminal-10-comandos)
- [Modo web interactivo](#-modo-web-interactivo)
- [Fuentes monitorizadas](#-fuentes-monitorizadas)
- [Países cubiertos](#-países-cubiertos)
- [Léxico criminal latinoamericano](#-léxico-criminal-latinoamericano)
- [Tipo de OSINT y metodología](#-tipo-de-osint-y-metodología)
- [Ética, legalidad y protección de datos](#-ética-legalidad-y-protección-de-datos)
- [Contribuciones y futuro](#-contribuciones-y-futuro)
- [Licencia](#-licencia)

---

### 🔍 ¿Qué hace DIABOLIC_LATAM?

DIABOLIC_LATAM automatiza el proceso de scraping de noticias de sucesos de medios locales y nacionales de Latinoamérica. En lugar de leer decenas de periódicos cada día, la herramienta:

- Extrae automáticamente titulares, fechas, fuentes y ubicación geográfica (país) de noticias relacionadas con delitos.
- Clasifica los incidentes en categorías (robo, estafa, narcotráfico, violencia, asesinato, violación, extorsión, mafia, corrupción, desaparición, ciberdelito…).
- Almacena los datos localmente en formato JSON, sin guardar ningún dato personal.
- Analiza tendencias temporales (7, 30, 90 días) y distribuciones por país y tipo de delito.
- Detecta conexiones entre incidentes: misma zona, fechas cercanas, mismo modus operandi (lanzazo, motochorro, vacuna, gota a gota, sicariato…) que pueden indicar una misma banda u organización criminal.
- Visualiza los resultados mediante una interfaz web interactiva con gráficos de barras y filtros dinámicos.
- Exporta los datos a CSV o JSON para análisis externos.

---

### ⚙️ Características clave

🔁 **Rotación de User‑Agent**  
Evita bloqueos de los periódicos simulando diferentes navegadores y versiones en cada petición.

🧠 **Paginación inteligente**  
Prueba automáticamente hasta 12 formatos diferentes de paginación (/pagina/2, ?page=2, ?offset=2, etc.) y recuerda el que funciona para cada dominio.

🔎 **Detector automático de URLs**  
Si una URL de un periódico deja de funcionar, el sistema busca rutas alternativas (/policiales, /sucesos, /seguridad, /judicial, etc.) y actualiza la configuración.

📊 **Clasificación avanzada de delitos**  
Utiliza una lista amplia de palabras clave, incluyendo jerga local latinoamericana (lanzazo, motochorro, vacuna, gota a gota, sicariato, feminicidio, fosa clandestina, coima, testaferro…). Se puede extender fácilmente.

🔗 **Conexiones entre incidentes**  
- Por tipo y país (ej. 5 robos en México en 7 días).  
- Por modus operandi (detecta repetición de términos como “lanzazo” o “vacuna”).  
- Frecuencia temporal (incidentes/día).

🌐 **Interfaz web interactiva**  
- Gráficos de barras por país y tipo de delito.  
- Filtros por período (últimos 7, 30, 90 días).  
- Lista de los últimos 20 incidentes.  
- Botones para actualizar datos y exportar JSON/CSV.

🖥️ **Menú terminal completo**  
10 comandos que permiten ejecutar todas las funciones sin necesidad de abrir el navegador.

🌍 **Multilingüe** – Soporte español y portugués (selector al inicio).

---

### 🛠️ Tecnología y arquitectura

- **Lenguaje:** Python 3.8+  
- **Framework web:** Flask (servidor ligero)  
- **Scraping:** Requests + BeautifulSoup4  
- **Almacenamiento:** JSON local (sin bases de datos externas)  
- **Estructura modular:**  
  - `DetectorURLs`: verifica y corrige URLs de periódicos.  
  - `GestorDatos`: carga, guarda y procesa los incidentes.  
  - `ExtractorNoticias`: scraping con rotación de User‑Agent y paginación inteligente.  
- **Colores en terminal:** Códigos ANSI.

---

### 📥 Instalación y uso

#### En Termux (Android)
```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install requests beautifulsoup4 flask
git clone https://github.com/Condor2026/Diabolic_Latam
cd Diabolic_Latam
python Diabolic_Latam.py
