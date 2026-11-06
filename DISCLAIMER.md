# Aviso legal y directrices éticas — DIABOLIC LATAM

## Naturaleza de la herramienta

DIABOLIC LATAM es una herramienta **OSINT pasiva y analítica** para el estudio de noticias públicas sobre narcotráfico, crimen organizado, violencia armada, finanzas ilícitas y corrupción en América Latina.

- **No** accede a datos personales.
- **No** realiza vigilancia de individuos.
- **No** interactúa con los sistemas de las fuentes más allá de peticiones HTTP equivalentes a las de un lector humano.
- **No** vulnera accesos, credenciales ni medidas de seguridad.

## Datos tratados

Solo se almacenan metadatos públicos:

- Titular de la noticia.
- Fecha.
- Fuente.
- Ubicación aproximada (ciudad, estado/departamento o país).
- Tipo de delito, categoría, severidad y confianza.

No se almacenan nombres de personas, direcciones, teléfonos, correos ni identificadores.

## Cumplimiento normativo

- **RGPD / LGPD (Brasil) / LOPDGDD**: al no tratar datos personales, la herramienta queda fuera del ámbito de aplicación de estas normas.
- **Propiedad intelectual**: no se republica el contenido íntegro de las noticias; solo titulares y metadatos.

## Scraping

- Por defecto **no** se respeta `robots.txt` (heredado de la v1). Se puede activar con `--robots`.
- Se aplican delays aleatorios y rate limiting por host.
- El usuario es responsable de respetar los términos de uso de cada fuente.

## Alarma sonora

La herramienta puede emitir una **sirena** en el navegador cuando detecta violencia armada. El usuario debe poder silenciarla (botones "mute", "stop", "ack" en el panel).

## Alertas oficiales

Las alertas oficiales se muestran **tal cual** las publica el organismo emisor (DEA, OFAC, UNODC, fiscalías, policías, UIF, GAFILAT…). No son interpretación del proyecto ni constituyen asesoramiento legal.

## Exención de responsabilidad

La herramienta se proporciona **"tal cual"**, sin garantías de funcionamiento ininterrumpido ni de exactitud de los datos. Cualquier modificación que introduzca funcionalidades lesivas (recogida de datos personales, vigilancia encubierta) es responsabilidad exclusiva de quien la realice.

## Principios éticos

- **Transparencia**: código abierto, auditable.
- **No vigilancia**: sin perfilado de personas.
- **Responsabilidad**: el usuario es el único responsable del uso.
