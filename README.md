# 🔥 DIABOLIC LATAM v7.0

![Version](https://img.shields.io/badge/version-7.0-red)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![OSINT](https://img.shields.io/badge/OSINT-Passive-blueviolet)
![Termux](https://img.shields.io/badge/Termux-Compatible-orange)
![Linux](https://img.shields.io/badge/Linux-Compatible-lightgrey)
![Windows](https://img.shields.io/badge/Windows-Compatible-brightgreen?logo=windows)
![Web Scraping](https://img.shields.io/badge/Web%20Scraping-Legal-brightgreen)
![GDPR](https://img.shields.io/badge/GDPR-Compliant-blue)
![LGPD](https://img.shields.io/badge/LGPD-Compliant-blueviolet)
![Crimen](https://img.shields.io/badge/Focus-Narco%20%26%20Cártel-red)

**DIABOLIC LATAM** es una herramienta OSINT pasiva y analítica diseñada para **monitorizar automáticamente más de 70 periódicos digitales de 18 países latinoamericanos**, extrayendo y procesando noticias de sucesos para detectar patrones delictivos, tendencias geográficas y conexiones entre incidentes, con **enfoque especial en narcotráfico, crimen organizado, violencia y corrupción**.

Nace con una filosofía clara: *“Un gran poder conlleva una gran responsabilidad”*. Por eso su diseño prioriza la transparencia, la ética y el respeto a la privacidad. Soporta **español y portugués**.

---

## 📌 Índice

- [🔍 ¿Qué hace DIABOLIC?](#-qué-hace-diabolic)
- [⚙️ Características clave](#️-características-clave)
- [🛠️ Tecnología y arquitectura](#️-tecnología-y-arquitectura)
- [⚖️ Web Scraping: marco legal](#️-web-scraping-marco-legal)
- [📥 Instalación y uso](#-instalación-y-uso)
- [🖥️ Modo terminal (10 comandos)](#️-modo-terminal-10-comandos)
- [🌐 Modo web interactivo](#-modo-web-interactivo)
- [📰 Fuentes monitorizadas](#-fuentes-monitorizadas)
- [🌎 Países cubiertos](#-países-cubiertos)
- [🧠 Léxico criminal latinoamericano](#-léxico-criminal-latinoamericano)
- [🧠 Tipo de OSINT y metodología](#-tipo-de-osint-y-metodología)
- [⚖️ Ética, legalidad y protección de datos](#️-ética-legalidad-y-protección-de-datos)
- [🤝 Contribuciones y futuro](#-contribuciones-y-futuro)
- [📜 Licencia](#-licencia)

---

## 🔍 ¿Qué hace DIABOLIC?

DIABOLIC LATAM automatiza el proceso de scraping de noticias de sucesos de medios latinoamericanos. En lugar de leer decenas de periódicos cada día, la herramienta:

- **Extrae** automáticamente titulares, fechas, fuentes y ubicación geográfica (país) de noticias relacionadas con delitos.
- **Clasifica** los incidentes en categorías especializadas: narcotráfico, sicariato, extorsión, lavado de activos, violencia, corrupción, desaparición forzada, ciberdelito, etc.
- **Almacena** los datos localmente en formato JSON, sin guardar ningún dato personal.
- **Analiza** tendencias temporales (7, 30, 90 días) y distribuciones por país y tipo de delito.
- **Detecta conexiones** entre incidentes: misma zona, fechas cercanas, mismo modus operandi (rutas de narcotráfico, puntos de alijo, etc.).
- **Visualiza** los resultados mediante una interfaz web interactiva con gráficos de barras y filtros dinámicos.
- **Exporta** los datos a CSV o JSON para análisis externos.

---

## ⚙️ Características clave

| Característica | Descripción |
|----------------|-------------|
| 🔁 Rotación de User‑Agent | Evita bloqueos simulando diferentes navegadores y versiones. |
| 🧠 Paginación inteligente | Prueba 12 formatos de paginación y recuerda el que funciona. |
| 🔎 Detector automático de URLs | Si falla, busca rutas alternativas (/policiales, /seguridad, /judicial...). |
| 📊 Clasificación avanzada | Léxico latinoamericano (más de 800 términos: cartel, narco, sicario, extorsión, fentanilo, etc.). |
| 🔗 Conexiones entre incidentes | Por país y tipo, por modus operandi, frecuencia temporal. |
| 🌐 Interfaz web interactiva | Gráficos, filtros, exportación. |
| 🖥️ Menú terminal completo | 10 comandos. |
| 🌍 Multilingüe | Español y portugués (selector al inicio). |

---

## 🛠️ Tecnología y arquitectura

- **Lenguaje**: Python 3.8+
- **Framework web**: Flask
- **Scraping**: Requests + BeautifulSoup4
- **Almacenamiento**: JSON local
- **Estructura modular**:
  - `DetectorURLs`: verifica y corrige URLs.
  - `GestorDatos`: carga, guarda y procesa incidentes.
  - `ExtractorNoticias`: scraping con rotación de User‑Agent y paginación inteligente.
- **Colores en terminal**: Códigos ANSI.

---

## ⚖️ Web Scraping: marco legal

El web scraping que realiza DIABOLIC LATAM es **completamente legal y ético** por las siguientes razones:

1. **Fuentes públicas**: Solo accede a contenido indexado y accesible sin autenticación. No vulnera sistemas de pago ni áreas restringidas.
2. **Cumplimiento del RGPD / LGPD**: No extrae, almacena ni procesa datos personales (nombres, direcciones, teléfonos, emails, IPs, cookies). Solo almacena metadatos anónimos: titular de la noticia, fecha, país aproximado, tipo de delito y fuente.
3. **Respeto a los términos de uso**: La herramienta respeta el archivo `robots.txt` de cada sitio (se puede configurar) y no sobrecarga los servidores con peticiones (limita la frecuencia y número de páginas).
4. **Sin republicación de contenido**: No copia íntegramente los artículos, solo extrae titulares y metadatos para análisis, citando siempre la fuente original.
5. **Uso legítimo**: La finalidad es exclusivamente académica, periodística, criminológica o de prevención comunitaria, sin ánimo de lucro ni vigilancia masiva.
6. **Transparencia total**: El código es abierto y auditable, lo que permite verificar que no se realizan prácticas lesivas.

> **Nota**: El scraping masivo o con fines de venta/redistribución de contenido puede vulnerar derechos de autor. Este proyecto se acoge al **uso justo** (fair use) y al **derecho a la información**.

---

## 📥 Instalación y uso

### En Termux (Android)

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install requests beautifulsoup4 flask
git clone https://github.com/Condor2026/Diabolic_Latam
cd Diabolic_Latam
python Diabolic_Latam.py
```

En Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-pip git -y
pip3 install requests beautifulsoup4 flask
git clone https://github.com/Condor2026/Diabolic_Latam
cd Diabolic_Latam
python3 Diabolic_Latam.py
```

En Windows (con Python instalado)

```bash
git clone https://github.com/Condor2026/Diabolic_Latam
cd Diabolic_Latam
pip install requests beautifulsoup4 flask
python Diabolic_Latam.py
```

---

🖥️ Modo terminal (10 comandos)

Al ejecutar Diabolic_Latam.py aparece un menú con las siguientes opciones:

```
╔════════════════════════════════════════════════════╗
║              M E N Ú   P R I N C I P A L           ║
╚════════════════════════════════════════════════════╝
[1] 🔍 Buscar noticias (narco/migración)
[2] 📊 Ver análisis completo
[3] 🔗 Ver conexiones entre incidentes
[4] 📈 Ver evolución mensual
[5] 🌐 Iniciar servidor web
[6] 📰 Ver últimos 20 incidentes
[7] 📥 Exportar datos (JSON/CSV)
[8] 🔍 Verificar periódicos
[9] 📊 Ver distribución por tipo
[0] 🗑️ Salir
```

Cada opción ejecuta la acción correspondiente y muestra los resultados en la terminal.

---

🌐 Modo web interactivo

La opción [5] lanza un servidor Flask local (por defecto en http://localhost:5013). Desde el navegador podrás:

· Ver gráficos de barras interactivos por país y tipo de delito.
· Filtrar por período (7, 30, 90 días).
· Consultar la lista de incidentes.
· Exportar los datos a CSV o JSON con un clic.

---

📰 Fuentes monitorizadas

La herramienta rastrea más de 70 periódicos digitales latinoamericanos, incluyendo:

· Argentina: Infobae, Clarín, La Nación, Página 12, Crónica, A24, Perfil, C5N, TN, La Voz.
· Chile: BioBioChile, La Tercera, Emol, Meganoticias, El Mostrador, Cooperativa, La Cuarta.
· Colombia: El Tiempo, El Espectador, El Colombiano, Semana, Blu Radio, Caracol, La FM, W Radio.
· México: El Universal, La Jornada, Reforma, Milenio, El Financiero, Proceso, Animal Político, Noroeste.
· Perú: El Comercio, La República, Perú 21, Correo, Gestión, Ojo, Expreso.
· Brasil: O Globo, Folha de S.Paulo, Estadão, Correio Braziliense, Estado de Minas, O Dia.
· Uruguay: El País, El Observador, Montevideo Portal.
· Bolivia: El Deber, La Razón, Los Tiempos.
· Paraguay: ABC Color, Última Hora, La Nación.
· Ecuador: El Universo, Primicias, Expreso.
· Costa Rica: La Nación, CRHoy.
· Panamá: La Prensa, Crítica.
· Guatemala: Prensa Libre, La Hora.
· El Salvador: La Prensa Gráfica, El Diario de Hoy.
· Honduras: La Prensa, El Heraldo.
· Nicaragua: La Prensa, El Nuevo Diario.
· República Dominicana: Listín Diario, El Caribe.
· Venezuela: El Nacional, El Universal, Últimas Noticias.

La lista completa se puede consultar/editando dentro del script (PERIODICOS_BASE).

---

🌎 Países cubiertos

Argentina, Bolivia, Brasil, Chile, Colombia, Costa Rica, Ecuador, El Salvador, Guatemala, Honduras, México, Nicaragua, Panamá, Paraguay, Perú, República Dominicana, Uruguay, Venezuela.

---

🧠 Léxico criminal latinoamericano

La herramienta incluye más de 800 términos específicos de la región:

· Narcotráfico: cartel, cártel, narco, capo, fentanilo, cocaína, crack, microtráfico, narcomenudeo, cocina de droga, punto de venta.
· Sicariato y violencia: sicario, ajuste de cuentas, ejecución, masacre, balacera, levantón, fosa clandestina.
· Extorsión: vacuna, cupo, gota a gota, cobro de piso, derecho de piso, halcón, campana.
· Corrupción: coima, mordida, lavado de activos, testaferro, enriquecimiento ilícito.
· Robos y hurtos: lanzazo, motochorro, alunizaje, butrón, secuestro express, portonazo.
· Delitos sexuales: violación, abuso sexual, grooming, sexting, pedofilia.
· Ciberdelito: phishing, ransomware, hackeo, estafa digital.

---

🧠 Tipo de OSINT y metodología

· OSINT Pasivo: No interactúa con los sistemas de los periódicos más allá de lo que un usuario normal haría.
· Extracción selectiva: Solo recoge información de sucesos policiales y judiciales.
· Anonimización: No almacena datos personales de los implicados, solo el lugar, fecha y tipo de delito.
· Enfoque analítico: Busca patrones para entender la criminalidad en Latinoamérica, especialmente redes de narcotráfico y crimen organizado.

---

⚖️ Ética, legalidad y protección de datos

DIABOLIC LATAM respeta las leyes locales, el RGPD y la LGPD:

· Solo accede a contenido público y no requiere autenticación.
· No almacena información personal (nombres, documentos, direcciones, IPs, cookies).
· El código es abierto y transparente.
· Se recomienda utilizar la herramienta únicamente con fines académicos, periodísticos o de investigación criminal legítima.

⚠️ ADVERTENCIA LEGAL
Esta herramienta es exclusivamente para fines educativos y de investigación legítima. No debe utilizarse para acosar, doxear, realizar actividades ilegales o violar la privacidad de las personas. El autor no se responsabiliza del mal uso. El usuario es el único responsable de cumplir con las leyes de su país.

---

🤝 Contribuciones y futuro

Las contribuciones son bienvenidas. Puedes:

· Reportar errores en Issues.
· Ampliar la lista de periódicos o países.
· Mejorar el detector automático de URLs.
· Añadir nuevas categorías de delitos (especialmente relacionados con el narcotráfico).
· Optimizar el análisis de conexiones entre carteles.

---

📜 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.

---

🙏 Agradecimientos

· BeautifulSoup4 – scraping.
· Flask – interfaz web.
· Inspiración: proyectos OSINT como Sherlock, Maigret.
· Comunidad de investigación OSINT en Latinoamérica.

⭐ ¡Si te gusta el proyecto, no olvides darle una estrella en GitHub!

```
