#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Condor2026 / SpectrumSecurity

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🔪 DIABOLIC LATAM v8.0 · NARCO EDITION  (motor v3)                           ║
║  ═══════════════════════════════════════════════════════════════════════════  ║
║  🌎 Carteles · narcotráfico · sicariato · extorsión · lavado · desaparecidos  ║
║  🕷️  Scraping v1 (secuencial, 120+ UA, 2 intentos y se pasa a la siguiente)   ║
║  🔁 Auto-descubrimiento de URLs movidas + RSS de respaldo                     ║
║  🎯 Clasificador es/pt/en anti-falsos-positivos + confianza + relevancia      ║
║  🔗 Fusión multi-fuente · 🚨 alarma sonora de violencia armada                ║
║  🏛️  Alertas oficiales (DEA, OFAC, UNODC, fiscalías, policías, UIF…)          ║
║  📈 Indicadores estilo crypto (RSI, SMA, Bollinger, índice de amenaza)        ║
║  🗺️  Mapa 2D: Carto · OSM · satélite · calor · clusters · pulso · tooltips    ║
║  🌐 Idiomas: ES · EN             🖥️  Panel holográfico (puerto 5013)          ║
║                                                                               ║
║     - By Condor2026                                                           ║
║                                         •SpectrumSecurity•                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Dependencias:  pip install flask requests beautifulsoup4
Opcionales:    pip install matplotlib networkx      (gráficos estáticos PNG)

Uso:  python Diabolic_Latam.py                  (menú interactivo)
      python Diabolic_Latam.py --web --lang es  (panel web)
      python Diabolic_Latam.py --scan fd        (escaneo por línea de comandos)
Datos: lee y migra automáticamente tu diabolic_narco.json de la v7.
"""

import os
import sys
import io
import re
import csv
import json
import time
import math
import socket
import html as htmllib
import random
import hashlib
import logging
import argparse
import threading
import unicodedata
from datetime import datetime, timedelta
from collections import defaultdict, Counter, deque
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response, jsonify
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

try:
    import networkx as nx
    HAS_NX = True
except Exception:
    HAS_NX = False

# ============================================================================
# LOGGING  (fichier complet; console seulement les avertissements → terminal propre)
# ============================================================================

_fh = logging.FileHandler('diabolic_latam.log', encoding='utf-8')
_fh.setLevel(logging.INFO)
_ch = logging.StreamHandler()
_ch.setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[_fh, _ch])
logger = logging.getLogger('diabolic')
logging.getLogger('urllib3').setLevel(logging.ERROR)      # plus de bruit "Retrying (Retry(total=..."
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ============================================================================
# CONSTANTES  (valeurs v1 conservées pour le temps de scraping)
# ============================================================================

VERSION = "8.0"
PUERTO = 5013
ARCHIVO_DATOS = 'diabolic_narco.json'            # misma base que la v7 (migración automática)
ARCHIVO_CACHE = 'url_cache_narco.json'
ARCHIVO_ESTADO = 'estado_fuentes_narco.json'
ARCHIVO_BACKUP = 'diabolic_narco_backup.json'
DIR_ESTATICOS = 'graficos_estaticos'
PAGINAS_BUSQUEDA = 3
TIMEOUT = 25
MAX_INTENTOS = 3              # v1 (vérification des sources)
INTENTOS_ESCANEO = 2          # "deux essais et on passe à la source suivante"
DELAY_MIN = 1.3               # v1 = 0.8 (un poco más lento para no ser bloqueado)
DELAY_MAX = 3.2               # v1 = 2.0
PRESUPUESTO_FUENTE = 90       # secondes max par source (aucune source ne bloque le scan)
MAX_ELEMENTOS = 60            # v1 regardait 30 éléments par page
RESPETAR_ROBOTS = False       # v1 ne lisait pas robots.txt (activable: --robots)
UMBRAL_ALARMA = 6             # sévérité minimale d'un conflit de rue pour déclencher l'alarme
AUTO_REFRESH_MIN = 0          # 0 = pas de scan automatique (--auto 30 pour activer)
SENSIBILIDAD = 'equilibrado'  # amplio (≈ v1) | equilibrado | estricto
SCHEMA = 3
_UMBRAL_CONF = {'amplio': 20, 'equilibrado': 45, 'estricto': 60}

# ============================================================================
# IDIOMAS  (fr | es | en | it | de)
# ============================================================================

LANGS = ('es', 'en')
LANG_FLAGS = {'es': '🇪🇸', 'en': '🇬🇧'}
LANG_NAMES = {'es': 'Español', 'en': 'English'}
IDIOMA_ACTUAL = 'es'

_TXT = {
    # ---- general / CLI
    'app_sub': "Surveillance criminelle & cybercriminalité – France|Vigilancia criminal y cibercrimen – Francia|Crime & cybercrime monitoring – France|Monitoraggio di criminalità e cybercrimine – Francia|Überwachung von Kriminalität & Cybercrime – Frankreich",
    'menu_title': "MENU PRINCIPAL|MENÚ PRINCIPAL|MAIN MENU|MENU PRINCIPALE|HAUPTMENÜ",
    'm_search': "Rechercher crimes et cybercrimes|Buscar crímenes y cibercrimen|Search crimes and cybercrime|Cerca crimini e cybercrimine|Verbrechen & Cybercrime suchen",
    'm_analysis': "Analyse complète|Análisis completo|Full analysis|Analisi completa|Gesamtanalyse",
    'm_patterns': "Modèles et tendances|Patrones y tendencias|Patterns and trends|Modelli e tendenze|Muster und Trends",
    'm_evolution': "Évolution mensuelle|Evolución mensual|Monthly evolution|Evoluzione mensile|Monatliche Entwicklung",
    'm_web': "Serveur web (carte + graphes)|Servidor web (mapa + gráficos)|Web server (map + charts)|Server web (mappa + grafici)|Webserver (Karte + Diagramme)",
    'm_last': "20 derniers événements|Últimos 20 eventos|Last 20 events|Ultimi 20 eventi|Letzte 20 Ereignisse",
    'm_export': "Exporter données (JSON/CSV/HTML/GeoJSON)|Exportar datos (JSON/CSV/HTML/GeoJSON)|Export data (JSON/CSV/HTML/GeoJSON)|Esporta dati (JSON/CSV/HTML/GeoJSON)|Daten exportieren (JSON/CSV/HTML/GeoJSON)",
    'm_verify': "Vérifier sources|Verificar fuentes|Verify sources|Verifica fonti|Quellen prüfen",
    'm_types': "Distribution par type|Distribución por tipo|Distribution by type|Distribuzione per tipo|Verteilung nach Typ",
    'm_adv': "Statistiques avancées|Estadísticas avanzadas|Advanced statistics|Statistiche avanzate|Erweiterte Statistiken",
    'm_clean': "Nettoyer doublons|Limpiar duplicados|Remove duplicates|Pulisci duplicati|Duplikate entfernen",
    'm_quick': "Statistiques rapides|Estadísticas rápidas|Quick stats|Statistiche rapide|Schnellstatistik",
    'm_analytics': "Analytique: alertes, tendances, prévision|Analítica: alertas, tendencias, pronóstico|Analytics: alerts, trends, forecast|Analitica: allarmi, tendenze, previsioni|Analytik: Alarme, Trends, Prognose",
    'm_png': "Générer graphiques statiques PNG|Generar gráficos estáticos PNG|Generate static PNG charts|Genera grafici statici PNG|Statische PNG-Diagramme erzeugen",
    'm_exit': "Quitter|Salir|Exit|Esci|Beenden",
    'bye': "Au revoir!|¡Hasta pronto!|See you soon!|Arrivederci!|Auf Wiedersehen!",
    'invalid': "Option invalide|Opción no válida|Invalid option|Opzione non valida|Ungültige Option",
    'processing': "Traitement...|Procesando...|Processing...|Elaborazione...|Verarbeitung...",
    'press_enter': "Entrée pour continuer...|Enter para continuar...|Press Enter to continue...|Invio per continuare...|Eingabe zum Fortfahren...",
    'no_data': "Pas assez de données|Sin datos suficientes|Not enough data|Dati insufficienti|Nicht genug Daten",
    'new_events': "nouveaux événements|eventos nuevos|new events|nuovi eventi|neue Ereignisse",
    'top_type': "Type le plus fréquent|Tipo más común|Most common type|Tipo più comune|Häufigster Typ",
    'top_day': "Jour le plus actif|Día más activo|Most active day|Giorno più attivo|Aktivster Tag",
    'top_source': "Source la plus active|Fuente más activa|Most active source|Fonte più attiva|Aktivste Quelle",
    'top_dept': "Département critique|Departamento crítico|Critical département|Dipartimento critico|Kritisches Département",
    'trend': "Tendance|Tendencia|Trend|Andamento|Trend",
    'severity': "Sévérité|Severidad|Severity|Severità|Schweregrad",
    # ---- web
    'tab_dash': "Tableau de bord|Panel|Dashboard|Pannello|Dashboard",
    'tab_map': "Carte|Mapa|Map|Mappa|Karte",
    'tab_graphs': "Graphiques|Gráficos|Charts|Grafici|Diagramme",
    'tab_network': "Réseau|Red|Network|Rete|Netzwerk",
    'tab_static': "Statiques|Estáticos|Static|Statici|Statisch",
    'tab_feed': "Flux|Flujo|Feed|Flusso|Feed",
    'k_total': "Total événements|Total eventos|Total events|Totale eventi|Ereignisse gesamt",
    'k_7d': "7 derniers jours|Últimos 7 días|Last 7 days|Ultimi 7 giorni|Letzte 7 Tage",
    'k_30d': "30 derniers jours|Últimos 30 días|Last 30 days|Ultimi 30 giorni|Letzte 30 Tage",
    'k_sources': "Sources actives|Fuentes activas|Active sources|Fonti attive|Aktive Quellen",
    'k_depts': "Départements|Departamentos|Départements|Dipartimenti|Départements",
    'k_types': "Types détectés|Tipos detectados|Types detected|Tipi rilevati|Erkannte Typen",
    'k_sev': "Sévérité moyenne|Severidad media|Average severity|Severità media|Ø Schweregrad",
    'k_cyber': "Part cyber|Cuota cyber|Cyber share|Quota cyber|Cyber-Anteil",
    'f_all': "Tout|Todo|All|Tutto|Alle",
    'cat_all': "Tout|Todo|All|Tutto|Alle",
    'cat_phys': "Crime physique|Crimen físico|Physical crime|Crimine fisico|Physische Kriminalität",
    'cat_cyber': "Cybercrime|Cibercrimen|Cybercrime|Cybercrimine|Cybercrime",
    'all_types': "Tous les types|Todos los tipos|All types|Tutti i tipi|Alle Typen",
    'search_ph': "Rechercher...|Buscar...|Search...|Cerca...|Suchen...",
    'btn_update': "Mettre à jour|Actualizar|Update|Aggiorna|Aktualisieren",
    'updating': "Mise à jour en cours|Actualizando|Updating|Aggiornamento in corso|Aktualisierung läuft",
    'm_heat': "Chaleur|Calor|Heat|Calore|Hitze",
    'm_clusters': "Événements (clusters)|Eventos (clusters)|Events (clusters)|Eventi (cluster)|Ereignisse (Cluster)",
    'm_choro': "Choroplèthe départements|Coroplético departamentos|Département choropleth|Coropletica dipartimenti|Choroplethen Départements",
    'm_hot': "Hotspots|Hotspots|Hotspots|Hotspot|Hotspots",
    'c_dept': "Top départements|Top departamentos|Top départements|Top dipartimenti|Top Départements",
    'c_types': "Types de crime|Tipos de crimen|Crime types|Tipi di crimine|Verbrechenstypen",
    'c_monthly': "Évolution mensuelle (physique vs cyber)|Evolución mensual (físico vs cyber)|Monthly evolution (physical vs cyber)|Evoluzione mensile (fisico vs cyber)|Monatsverlauf (physisch vs. Cyber)",
    'c_radar': "Radar des types|Radar de tipos|Type radar|Radar dei tipi|Typ-Radar",
    'c_sev': "Distribution de la sévérité|Distribución de severidad|Severity distribution|Distribuzione severità|Schweregrad-Verteilung",
    'c_weekday': "Carte thermique jour × type|Mapa térmico día × tipo|Heatmap weekday × type|Mappa termica giorno × tipo|Heatmap Wochentag × Typ",
    'c_forecast': "Prévision hebdomadaire (Holt)|Pronóstico semanal (Holt)|Weekly forecast (Holt)|Previsione settimanale (Holt)|Wochenprognose (Holt)",
    'c_sankey': "Flux Sankey: catégorie → type → département|Flujo Sankey: categoría → tipo → departamento|Sankey flow: category → type → département|Flusso Sankey: categoria → tipo → dipartimento|Sankey-Fluss: Kategorie → Typ → Département",
    'c_anom': "Anomalies quotidiennes (z-score)|Anomalías diarias (z-score)|Daily anomalies (z-score)|Anomalie giornaliere (z-score)|Tägliche Anomalien (z-Score)",
    'c_trend': "Mots en tendance|Palabras en tendencia|Trending words|Parole in tendenza|Trendbegriffe",
    'c_net': "Réseau type ↔ département|Red tipo ↔ departamento|Type ↔ département network|Rete tipo ↔ dipartimento|Netzwerk Typ ↔ Département",
    'alerts': "Alertes|Alertas|Alerts|Allarmi|Alarme",
    'alert_ok': "Aucune anomalie détectée|Ninguna anomalía detectada|No anomalies detected|Nessuna anomalia rilevata|Keine Anomalien erkannt",
    'alert_spike': "Pic d'activité|Pico de actividad|Activity spike|Picco di attività|Aktivitätsspitze",
    'hotspots_t': "Zones chaudes|Zonas calientes|Hot zones|Zone calde|Hotspot-Zonen",
    'prev': "← Précédent|← Anterior|← Previous|← Precedente|← Zurück",
    'next': "Suivant →|Siguiente →|Next →|Successivo →|Weiter →",
    'page': "Page|Página|Page|Pagina|Seite",
    'events': "événements|eventos|events|eventi|Ereignisse",
    'open': "Ouvrir|Abrir|Open|Apri|Öffnen",
    'geo_note': "Points géolocalisés au niveau ville ou département (approximatif)|Puntos geolocalizados a nivel ciudad o departamento (aproximado)|Points geolocated at city or département level (approximate)|Punti geolocalizzati a livello città o dipartimento (approssimativo)|Punkte auf Stadt- oder Départementebene geokodiert (ungefähr)",
    'st_tipos': "Répartition par type|Reparto por tipo|Distribution by type|Distribuzione per tipo|Verteilung nach Typ",
    'st_mensual': "Évolution mensuelle|Evolución mensual|Monthly evolution|Evoluzione mensile|Monatsverlauf",
    'st_heatmap': "Jour × type|Día × tipo|Weekday × type|Giorno × tipo|Wochentag × Typ",
    'st_hexbin': "Densité géographique (hexbin)|Densidad geográfica (hexbin)|Geographic density (hexbin)|Densità geografica (hexbin)|Geografische Dichte (Hexbin)",
    'st_red': "Graphe type ↔ département (networkx)|Grafo tipo ↔ departamento (networkx)|Type ↔ département graph (networkx)|Grafo tipo ↔ dipartimento (networkx)|Graph Typ ↔ Département (networkx)",
    'st_missing': "Installez matplotlib (et networkx) pour ce graphique|Instala matplotlib (y networkx) para este gráfico|Install matplotlib (and networkx) for this chart|Installa matplotlib (e networkx) per questo grafico|Installieren Sie matplotlib (und networkx) für dieses Diagramm",
    'phys': "Physique|Físico|Physical|Fisico|Physisch",
    'cyber': "Cyber|Cyber|Cyber|Cyber|Cyber",
    'forecast_lbl': "Prévision|Pronóstico|Forecast|Previsione|Prognose",
    'history_lbl': "Historique|Histórico|History|Storico|Verlauf",
    'motto': "L'union fait la force|La unión hace la fuerza|Strength through unity|L'unione fa la forza|Einigkeit macht stark",
}
_TXT_V3 = {
    'app_sub': "Surveillance criminelle · rue · cybercriminalité – France|Vigilancia criminal · calle · cibercrimen – Francia|Crime · street · cybercrime monitoring – France|Monitoraggio crimine · strada · cybercrimine – Francia|Überwachung Kriminalität · Straße · Cybercrime – Frankreich",
    'm_search': "Scanner tout (crimes, rue, cyber, alertes)|Escanear todo (crimen, calle, cyber, alertas)|Scan everything (crime, street, cyber, alerts)|Scansiona tutto (crimine, strada, cyber, allerte)|Alles scannen (Verbrechen, Straße, Cyber, Warnungen)",
    'm_scan_sub': "Scan ciblé (type / département / source)|Escaneo dirigido (tipo / departamento / fuente)|Targeted scan (type / département / source)|Scansione mirata (tipo / dipartimento / fonte)|Gezielter Scan (Typ / Département / Quelle)",
    'm_gov': "Alertes officielles (CERT-FR, Intérieur…)|Alertas oficiales (CERT-FR, Interior…)|Official alerts (CERT-FR, Interior…)|Allerte ufficiali (CERT-FR, Interno…)|Offizielle Warnungen (CERT-FR, Inneres…)",
    'm_indic': "Indicateurs (RSI, SMA, indice de menace)|Indicadores (RSI, SMA, índice de amenaza)|Indicators (RSI, SMA, threat index)|Indicatori (RSI, SMA, indice di minaccia)|Indikatoren (RSI, SMA, Bedrohungsindex)",
    'm_alarm_test': "Tester l'alarme|Probar la alarma|Test the alarm|Prova l'allarme|Alarm testen",
    'm_health': "Santé des sources (diagnostic des zéros)|Salud de las fuentes (diagnóstico de ceros)|Source health (why zero?)|Salute delle fonti (diagnosi degli zeri)|Quellenstatus (warum null?)",
    'm_sens': "Sensibilité du filtre|Sensibilidad del filtro|Filter sensitivity|Sensibilità del filtro|Filterempfindlichkeit",
    'led_live': "Live|Live|Live|Live|Live",
    'led_scan': "Scan|Scan|Scan|Scan|Scan",
    'led_gov': "Officiel|Oficial|Official|Ufficiale|Offiziell",
    'alarm': "Alarme|Alarma|Alarm|Allarme|Alarm",
    'alarm_conflict': "CONFLIT DÉTECTÉ|CONFLICTO DETECTADO|CONFLICT DETECTED|CONFLITTO RILEVATO|KONFLIKT ERKANNT",
    'alarm_ack': "Couper la sirène|Detener sirena|Stop siren|Ferma sirena|Sirene stoppen",
    'alarm_test': "Test alarme|Probar alarma|Test alarm|Prova allarme|Alarm testen",
    'alarm_mute5': "Silence 5 min|Silenciar 5 min|Mute 5 min|Muto 5 min|Stumm 5 Min.",
    'alarm_vol': "Volume|Volumen|Volume|Volume|Lautstärke",
    'alarm_thr': "Seuil de sévérité|Umbral de severidad|Severity threshold|Soglia di gravità|Schweregrad-Schwelle",
    'alarm_sound': "Son|Sonido|Sound|Suono|Ton",
    'alarm_notif': "Notification navigateur|Notificación del navegador|Browser notification|Notifica del browser|Browser-Benachrichtigung",
    'alarm_hist': "HISTORIQUE|HISTORIAL|HISTORY|STORICO|VERLAUF",
    'alarm_arm': "Armer|Armar|Arm|Attiva|Scharfschalten",
    'alarm_disarm': "Désarmer|Desarmar|Disarm|Disattiva|Entschärfen",
    'alarm_off': "Éteinte|Apagada|Off|Spenta|Aus",
    'alarm_muted': "En sourdine|Silenciada|Muted|In muto|Stumm",
    'alarm_armed': "Armée|Armada|Armed|Attiva|Scharf",
    'alarm_ringing': "SONNE|SONANDO|RINGING|SUONA|ALARM",
    'alarm_click': "Cliquez Armer ou Test pour activer le son du navigateur|Pulsa Armar o Test para activar el sonido del navegador|Click Arm or Test to enable browser sound|Clicca Attiva o Prova per abilitare l'audio|Auf Scharfschalten oder Test klicken, um den Ton zu aktivieren",
    'gov_alerts': "ALERTES OFFICIELLES|ALERTAS OFICIALES|OFFICIAL ALERTS|ALLERTE UFFICIALI|OFFIZIELLE WARNUNGEN",
    'gov_none': "Aucune alerte officielle chargée — lancez le scan « Officiel »|Ninguna alerta oficial cargada — lanza el escaneo «Oficial»|No official alert loaded — run the “Official” scan|Nessuna allerta ufficiale — avvia la scansione «Ufficiale»|Keine offizielle Warnung geladen — „Offiziell“-Scan starten",
    'vig_set': "niveau à définir|nivel por definir|set level|imposta livello|Stufe setzen",
    'vig_1': "Vigilance|Vigilancia|Vigilance|Vigilanza|Wachsamkeit",
    'vig_2': "Sécurité renforcée – risque attentat|Seguridad reforzada – riesgo atentado|Reinforced security – attack risk|Sicurezza rafforzata – rischio attentato|Verstärkte Sicherheit – Anschlagsrisiko",
    'vig_3': "Urgence attentat|Urgencia atentado|Attack emergency|Emergenza attentato|Anschlagsnotstand",
    'vig_prompt': "Niveau Vigipirate en vigueur (1 Vigilance, 2 Sécurité renforcée, 3 Urgence attentat, 0 inconnu). Vérifiez sur info.gouv.fr|Nivel Vigipirate vigente (1 Vigilancia, 2 Seguridad reforzada, 3 Urgencia atentado, 0 desconocido). Verifica en info.gouv.fr|Current Vigipirate level (1 Vigilance, 2 Reinforced, 3 Attack emergency, 0 unknown). Check info.gouv.fr|Livello Vigipirate attuale (1 Vigilanza, 2 Rafforzata, 3 Emergenza, 0 sconosciuto). Verifica su info.gouv.fr|Aktuelle Vigipirate-Stufe (1 Wachsamkeit, 2 Verstärkt, 3 Notstand, 0 unbekannt). Prüfen auf info.gouv.fr",
    'btn_scan_all': "Scanner tout|Escanear todo|Scan all|Scansiona tutto|Alles scannen",
    'btn_scan_fd': "Faits divers + rue|Sucesos + calle|Crime + street|Cronaca + strada|Kriminalität + Straße",
    'btn_scan_cyber': "Cyber|Cyber|Cyber|Cyber|Cyber",
    'btn_scan_gov': "Officiel|Oficial|Official|Ufficiale|Offiziell",
    'btn_stop': "Stop|Parar|Stop|Ferma|Stopp",
    'btn_verify': "Vérifier sources|Verificar fuentes|Verify sources|Verifica fonti|Quellen prüfen",
    'btn_mute': "Sourdine|Silencio|Mute|Muto|Stumm",
    'btn_full': "Plein écran|Pantalla completa|Fullscreen|Schermo intero|Vollbild",
    'btn_copy': "Copier le lien|Copiar enlace|Copy link|Copia link|Link kopieren",
    'btn_reset': "Réinitialiser|Restablecer|Reset|Reimposta|Zurücksetzen",
    'copied': "Copié ✔|Copiado ✔|Copied ✔|Copiato ✔|Kopiert ✔",
    'tab_scan': "Scan / Sources|Escaneo / Fuentes|Scan / Sources|Scansione / Fonti|Scan / Quellen",
    'cat_all': "Tout|Todo|All|Tutto|Alle",
    'cat_phys': "Crime|Crimen|Crime|Crimine|Kriminalität",
    'cat_rue': "Conflits de rue|Conflictos callejeros|Street conflicts|Conflitti di strada|Straßenkonflikte",
    'cat_cyber': "Cybercrime|Cibercrimen|Cybercrime|Cybercrimine|Cybercrime",
    'conf_any': "Toute fiabilité|Cualquier fiabilidad|Any confidence|Qualsiasi affidabilità|Beliebige Verlässlichkeit",
    'conf_med': "Fiabilité ≥ 45%|Fiabilidad ≥ 45%|Confidence ≥ 45%|Affidabilità ≥ 45%|Verlässlichkeit ≥ 45%",
    'conf_high': "Fiabilité ≥ 60%|Fiabilidad ≥ 60%|Confidence ≥ 60%|Affidabilità ≥ 60%|Verlässlichkeit ≥ 60%",
    'k_conf24': "Conflits 24h|Conflictos 24h|Conflicts 24h|Conflitti 24h|Konflikte 24h",
    'k_multi': "Multi-sources|Multi-fuente|Multi-source|Multi-fonte|Mehrfachquellen",
    'k_sev': "Sévérité moyenne|Severidad media|Average severity|Severità media|Ø Schweregrad",
    'threat_idx': "Indice de menace|Índice de amenaza|Threat index|Indice di minaccia|Bedrohungsindex",
    'th_calm': "CALME|CALMA|CALM|CALMA|RUHIG",
    'th_watch': "VIGILANCE|VIGILANCIA|WATCH|VIGILANZA|WACHSAM",
    'th_tense': "TENDU|TENSO|TENSE|TESO|ANGESPANNT",
    'th_crit': "CRITIQUE|CRÍTICO|CRITICAL|CRITICO|KRITISCH",
    'vol': "Volatilité|Volatilidad|Volatility|Volatilità|Volatilität",
    'signal': "Signal|Señal|Signal|Segnale|Signal",
    'sig_up': "ESCALADE|ESCALADA|ESCALATION|ESCALATION|ESKALATION",
    'sig_dn': "APAISEMENT|DISTENSIÓN|DE-ESCALATION|DISTENSIONE|ENTSPANNUNG",
    'sig_neu': "NEUTRE|NEUTRO|NEUTRAL|NEUTRO|NEUTRAL",
    'c_boll': "Flux quotidien · SMA7/30 · Bollinger|Flujo diario · SMA7/30 · Bollinger|Daily flow · SMA7/30 · Bollinger|Flusso giornaliero · SMA7/30 · Bollinger|Tagesfluss · SMA7/30 · Bollinger",
    'c_street': "Conflits de rue récents|Conflictos callejeros recientes|Recent street conflicts|Conflitti di strada recenti|Aktuelle Straßenkonflikte",
    'c_toprel': "Les plus pertinents|Los más relevantes|Most relevant|I più rilevanti|Relevanteste",
    'c_weekly': "Hebdomadaire par catégorie|Semanal por categoría|Weekly by category|Settimanale per categoria|Wöchentlich nach Kategorie",
    'c_bubble': "Départements: volume × sévérité|Departamentos: volumen × severidad|Départements: volume × severity|Dipartimenti: volume × gravità|Départements: Volumen × Schweregrad",
    'c_monthly': "Évolution mensuelle par catégorie|Evolución mensual por categoría|Monthly evolution by category|Evoluzione mensile per categoria|Monatsverlauf nach Kategorie",
    'm_pulse': "Conflits de rue (pulsation)|Conflictos callejeros (pulso)|Street conflicts (pulse)|Conflitti di strada (pulsazione)|Straßenkonflikte (Puls)",
    'm_timelapse': "Timelapse 30j|Timelapse 30d|Timelapse 30d|Timelapse 30g|Zeitraffer 30T",
    'm_fit': "Voir sur la carte|Ver en el mapa|Show on map|Mostra sulla mappa|Auf Karte zeigen",
    'map_dark': "Carto sombre|Carto oscuro|Carto dark|Carto scuro|Carto dunkel",
    'map_street': "Plan réel (OpenStreetMap)|Plano real (OpenStreetMap)|Real street map (OpenStreetMap)|Mappa reale (OpenStreetMap)|Echter Stadtplan (OpenStreetMap)",
    'map_osmfr': "OSM France|OSM Francia|OSM France|OSM Francia|OSM Frankreich",
    'map_voyager': "Carto Voyager|Carto Voyager|Carto Voyager|Carto Voyager|Carto Voyager",
    'map_light': "Carto clair|Carto claro|Carto light|Carto chiaro|Carto hell",
    'map_sat': "Satellite (Esri)|Satélite (Esri)|Satellite (Esri)|Satellite (Esri)|Satellit (Esri)",
    'sort_by': "Trier par|Ordenar por|Sort by|Ordina per|Sortieren nach",
    'sort_date': "Date|Fecha|Date|Data|Datum",
    'sort_rel': "Pertinence|Relevancia|Relevance|Rilevanza|Relevanz",
    'sort_sev': "Sévérité|Severidad|Severity|Gravità|Schweregrad",
    'relevance': "Pertinence|Relevancia|Relevance|Rilevanza|Relevanz",
    'sources_lbl': "Sources|Fuentes|Sources|Fonti|Quellen",
    'confirmed_by': "Confirmé par|Confirmado por|Confirmed by|Confermato da|Bestätigt von",
    'scan_ctl': "Lancer un scan|Lanzar un escaneo|Launch a scan|Avvia una scansione|Scan starten",
    'scan_pages': "Pages|Páginas|Pages|Pagine|Seiten",
    'scan_sens': "Sensibilité|Sensibilidad|Sensitivity|Sensibilità|Empfindlichkeit",
    'sens_wide': "Large (≈ v1)|Amplia (≈ v1)|Wide (≈ v1)|Ampia (≈ v1)|Breit (≈ v1)",
    'sens_bal': "Équilibrée|Equilibrada|Balanced|Bilanciata|Ausgewogen",
    'sens_strict': "Stricte|Estricta|Strict|Rigida|Streng",
    'scan_dep': "Département|Departamento|Département|Dipartimento|Département",
    'scan_src': "Source|Fuente|Source|Fonte|Quelle",
    'scan_note': "Un scan à la fois. Deux essais par source puis on passe à la suivante; si le domaine ou la section change, l'URL est retrouvée automatiquement.|Un escaneo a la vez. Dos intentos por fuente y se pasa a la siguiente; si cambia el dominio o la sección, la URL se encuentra sola.|One scan at a time. Two tries per source, then on to the next; if the domain or section changes the URL is found automatically.|Una scansione alla volta. Due tentativi per fonte, poi si passa alla successiva; se cambia dominio o sezione l'URL viene ritrovato da solo.|Ein Scan gleichzeitig. Zwei Versuche pro Quelle, dann die nächste; ändert sich Domain oder Rubrik, wird die URL automatisch gefunden.",
    'scan_console': "Terminal en direct|Terminal en vivo|Live terminal|Terminale live|Live-Terminal",
    'scan_sources': "Sources|Fuentes|Sources|Fonti|Quellen",
    'scan_busy': "Un scan est déjà en cours|Ya hay un escaneo en curso|A scan is already running|Una scansione è già in corso|Ein Scan läuft bereits",
    'src_name': "Nom|Nombre|Name|Nome|Name",
    'src_type': "Type|Tipo|Type|Tipo|Typ",
    'src_note': "État|Estado|Status|Stato|Status",
    'src_dep': "Département|Departamento|Département|Dipartimento|Département",
    'add_source': "Ajouter une source|Añadir fuente|Add source|Aggiungi fonte|Quelle hinzufügen",
    'official_links': "Liens officiels|Enlaces oficiales|Official links|Link ufficiali|Offizielle Links",
    'status_ok': "OK|OK|OK|OK|OK",
    'status_empty': "0 résultat|0 resultados|0 results|0 risultati|0 Ergebnisse",
    'status_dns': "Domaine mort|Dominio muerto|Dead domain|Dominio morto|Domain tot",
    'status_blocked': "Bloquée|Bloqueada|Blocked|Bloccata|Blockiert",
    'status_gone': "URL disparue|URL desaparecida|URL gone|URL scomparso|URL verschwunden",
    'status_err': "Erreur|Error|Error|Errore|Fehler",
    'status_idle': "Jamais scannée|Sin escanear|Never scanned|Mai scansionata|Nie gescannt",
    'updating': "Scan en cours|Escaneando|Scanning|Scansione in corso|Scan läuft",
    'm_pulse_': "-|-|-|-|-",
}
_TXT.update(_TXT_V3)

def _L(es, en):
    return f"{es}|{es}|{en}|{en}|{en}"


_TXT_LATAM = {
    'app_sub': _L("Inteligencia criminal · narcotráfico · violencia armada · finanzas ilícitas – Latinoamérica", "Criminal intelligence · narcotrafficking · armed violence · illicit finance – Latin America"),
    'm_search': _L("Buscar incidentes narco y crimen organizado", "Search narco & organized crime incidents"),
    'm_scan_sub': _L("Escaneo dirigido (tipo / país / fuente)", "Targeted scan (type / country / source)"),
    'm_gov': _L("Alertas oficiales (DEA, OFAC, UNODC, fiscalías…)", "Official alerts (DEA, OFAC, UNODC, prosecutors…)"),
    'vig_set': _L("nivel por definir", "set level"),
    'vig_1': _L("Vigilancia", "Watch"),
    'vig_2': _L("Alerta alta – riesgo de violencia", "High alert – violence risk"),
    'vig_3': _L("Emergencia regional", "Regional emergency"),
    'vig_prompt': _L("Nivel de alerta regional (1 Vigilancia, 2 Alerta alta, 3 Emergencia, 0 desconocido). Se define manualmente.", "Regional alert level (1 Watch, 2 High, 3 Emergency, 0 unknown). Set manually."),
    'vigipirate': _L("Alerta", "Alert"),
    'btn_scan_fd': _L("Narco + violencia", "Narco + violence"),
    'btn_scan_cyber': _L("Finanzas ilícitas", "Illicit finance"),
    'cat_phys': _L("Narcotráfico y crimen organizado", "Narcotrafficking & organized crime"),
    'cat_rue': _L("Violencia armada", "Armed violence"),
    'cat_cyber': _L("Finanzas ilícitas y corrupción", "Illicit finance & corruption"),
    'phys': _L("Narco/crimen org.", "Narco/org. crime"),
    'cyber': _L("Finanzas/corrupción", "Finance/corruption"),
    'k_cyber': _L("Cuota finanzas ilícitas", "Illicit finance share"),
    'k_conf24': _L("Alertas de alarma 24h", "Alarm-level 24h"),
    'k_depts': _L("Países", "Countries"),
    'top_dept': _L("País crítico", "Critical country"),
    'm_choro': _L("Burbujas por país", "Country bubbles"),
    'c_dept': _L("Top países", "Top countries"),
    'c_bubble': _L("Países: volumen × severidad", "Countries: volume × severity"),
    'c_street': _L("Violencia armada reciente", "Recent armed violence"),
    'm_pulse': _L("Violencia armada (pulso)", "Armed violence (pulse)"),
    'alarm_conflict': _L("VIOLENCIA ARMADA DETECTADA", "ARMED VIOLENCE DETECTED"),
    'c_monthly': _L("Evolución mensual por categoría", "Monthly evolution by category"),
    'c_sankey': _L("Flujo Sankey: categoría → tipo → país", "Sankey flow: category → type → country"),
    'c_net': _L("Red tipo ↔ país", "Type ↔ country network"),
    'st_red': _L("Grafo tipo ↔ país (networkx)", "Type ↔ country graph (networkx)"),
    'geo_note': _L("Puntos geolocalizados a nivel ciudad, estado o país (aproximado)", "Points geolocated at city, state or country level (approximate)"),
    'scan_dep': _L("País", "Country"),
    'src_dep': _L("País", "Country"),
    'map_osmfr': _L("OSM Humanitario (HOT)", "OSM Humanitarian (HOT)"),
}
_TXT.update(_TXT_LATAM)

TEXTOS = {l: {} for l in LANGS}
for _k, _v in _TXT.items():
    _p = _v.split('|')
    _p = _p[1:3] if len(_p) >= 3 else _p
    for _i, _l in enumerate(LANGS):
        TEXTOS[_l][_k] = _p[_i] if _i < len(_p) else _p[0]


def t(clave):
    return TEXTOS.get(IDIOMA_ACTUAL, TEXTOS['es']).get(clave, TEXTOS['es'].get(clave, clave))

# ============================================================================
# COLORES / CONSOLA
# ============================================================================

class Color:
    BLACK = '\033[30m'; RED = '\033[91m'; DARK_RED = '\033[31m'
    GREEN = '\033[92m'; DARK_GREEN = '\033[32m'; YELLOW = '\033[93m'
    DARK_YELLOW = '\033[33m'; BLUE = '\033[94m'; DARK_BLUE = '\033[34m'
    MAGENTA = '\033[95m'; DARK_MAGENTA = '\033[35m'; CYAN = '\033[96m'
    DARK_CYAN = '\033[36m'; WHITE = '\033[97m'; GRAY = '\033[90m'; LIGHT_GRAY = '\033[37m'
    BOLD = '\033[1m'; DIM = '\033[2m'; ITALIC = '\033[3m'; UNDERLINE = '\033[4m'
    BLINK = '\033[5m'; REVERSE = '\033[7m'; RESET = '\033[0m'
    BG_RED = '\033[41m'


_COLOR_MAP = {
    'black': Color.BLACK, 'red': Color.RED, 'dark_red': Color.DARK_RED, 'green': Color.GREEN,
    'dark_green': Color.DARK_GREEN, 'yellow': Color.YELLOW, 'dark_yellow': Color.DARK_YELLOW,
    'blue': Color.BLUE, 'dark_blue': Color.DARK_BLUE, 'magenta': Color.MAGENTA,
    'dark_magenta': Color.DARK_MAGENTA, 'cyan': Color.CYAN, 'dark_cyan': Color.DARK_CYAN,
    'white': Color.WHITE, 'gray': Color.GRAY, 'light_gray': Color.LIGHT_GRAY,
}


def cprint(texto, color=None, bold=False, dim=False, italic=False, underline=False,
           blink=False, bg=False, end='\n'):
    s = ''
    if bold: s += Color.BOLD
    if dim: s += Color.DIM
    if italic: s += Color.ITALIC
    if underline: s += Color.UNDERLINE
    if blink: s += Color.BLINK
    col = _COLOR_MAP.get(color, '') if color else ''
    print(f"{Color.BG_RED if bg else ''}{s}{col}{texto}{Color.RESET}", end=end, flush=True)


# ============================================================================
# USER-AGENTS  (la liste complète de la v1, sans modification)
# ============================================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.42 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.62 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.129 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.42 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.62 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0.2',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0.2',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0.2',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0.2',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0.1',
    'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36 Edg/125.0.6422.60',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.42 Safari/537.36 Edg/125.0.6422.42',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36 Edg/124.0.6367.118',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36 Edg/124.0.6367.91',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.62 Safari/537.36 Edg/124.0.6367.62',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36 Edg/125.0.6422.60',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/110.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36 OPR/110.0.5322.60',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/109.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36 OPR/109.0.5322.118',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Android 14; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0',
    'Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0',
    'Mozilla/5.0 (Android 13; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0',
    'Mozilla/5.0 (Android 13; Mobile; rv:123.0) Gecko/123.0 Firefox/123.0',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
    'Mozilla/5.0 (compatible; DuckDuckBot-Https/1.1; https://duckduckgo.com/duckduckbot)',
    'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
    'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0.2',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
]

def get_random_ua():
    return random.choice(USER_AGENTS)


def get_random_delay():
    return random.uniform(DELAY_MIN, DELAY_MAX)

# ============================================================================
# BUS D'INFORMATION  (terminal + panneau web partagent le même flux)
# ============================================================================

LOG = deque(maxlen=800)
_LOG_SEQ = [0]
_LOG_LOCK = threading.Lock()
TERMINAL_OUT = True
STATE = {'version': 0, 'tick': 0, 'alarm_seq': 0, 'alarm': {'seq': 0, 'items': [], 'test': False}}
_NIVEL_COLOR = {'ok': 'green', 'warn': 'yellow', 'err': 'red', 'info': 'cyan', 'dim': 'gray', 'disc': 'magenta', 'alarm': 'red'}


def emit(nivel, msg, end='\n'):
    """Écrit dans le terminal ET dans le flux SSE du panneau."""
    with _LOG_LOCK:
        _LOG_SEQ[0] += 1
        LOG.append({'i': _LOG_SEQ[0], 't': datetime.now().strftime('%H:%M:%S'), 'l': nivel, 'm': msg})
        STATE['tick'] += 1
    if TERMINAL_OUT:
        if nivel == 'alarm':
            cprint(f"\a {msg} ", 'white', bold=True, bg=True, end=end)
        else:
            cprint(msg, _NIVEL_COLOR.get(nivel, 'white'), dim=(nivel == 'dim'), end=end)

# ============================================================================
# HTTP  (logique v1: UA aléatoire, 3 essais, pause entre essais; + échec rapide si DNS mort)
# ============================================================================

_SESSION = None
_ROBOTS = {}
_ROBOTS_LOCK = threading.Lock()
_DNS_CACHE = {}
_HOST_LAST = {}
_HOST_LOCK = threading.Lock()


def _session():
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        # v1: Retry(total=2, read=2, connect=2, backoff 0.5). On ajoute: pas de Retry-After (une source
        # qui répond "attends 1h" ne doit pas geler le scan) et pas d'exception sur statut.
        retry = Retry(total=2, read=2, connect=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504],
                      respect_retry_after_header=False, raise_on_status=False)
        ad = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        s.mount('http://', ad)
        s.mount('https://', ad)
        _SESSION = s
    return _SESSION


def _usa_proxy():
    return any(os.environ.get(k) for k in ('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'ALL_PROXY'))


def dns_ok(host):
    """Vérifie une fois (cache 10 min) que le domaine existe → un domaine mort ne coûte plus 6 essais."""
    if not host or _usa_proxy():
        return True
    c = _DNS_CACHE.get(host)
    if c and time.time() - c[1] < 600:
        return c[0]
    try:
        socket.getaddrinfo(host, 443)
        ok = True
    except socket.gaierror:
        ok = False
    except Exception:
        ok = True
    _DNS_CACHE[host] = (ok, time.time())
    return ok


def robots_ok(url):
    if not RESPETAR_ROBOTS:
        return True
    p = urlparse(url)
    base = f'{p.scheme}://{p.netloc}'
    with _ROBOTS_LOCK:
        rp = _ROBOTS.get(base, False)
    if rp is False:
        rp = None
        try:
            r = requests.get(base + '/robots.txt', timeout=10, headers={'User-Agent': get_random_ua()})
            if r.status_code == 200:
                rp = robotparser.RobotFileParser()
                rp.parse(r.text.splitlines())
        except Exception:
            rp = None
        with _ROBOTS_LOCK:
            _ROBOTS[base] = rp
    return True if rp is None else rp.can_fetch('*', url)


def _cortesia(host, minimo=1.1):
    with _HOST_LOCK:
        now = time.time()
        wait = minimo - (now - _HOST_LAST.get(host, 0))
        _HOST_LAST[host] = now + max(0.0, wait)
    if wait > 0:
        time.sleep(wait)


def fetch(url, intentos=MAX_INTENTOS, timeout=TIMEOUT):
    """-> (response|None, kind). kind: ok | dns | gone | blocked | timeout | ssl | conn | http | robots | error"""
    p = urlparse(url or '')
    if p.scheme not in ('http', 'https') or not p.netloc:
        return None, 'error'
    if not dns_ok(p.hostname):
        return None, 'dns'
    if not robots_ok(url):
        return None, 'robots'
    kind = 'error'
    for _ in range(intentos):
        _cortesia(p.netloc)
        try:
            headers = {'User-Agent': get_random_ua(), 'Accept-Language': 'fr-FR,fr;q=0.9',                 # idem v1 + cabeceras de navegador
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer': 'https://www.google.fr/', 'Upgrade-Insecure-Requests': '1', 'DNT': '1'}
            r = _session().get(url, timeout=timeout, headers=headers, allow_redirects=True)
            sc = r.status_code
            if sc == 200:
                return r, 'ok'
            if sc in (404, 410):
                return None, 'gone'
            kind = 'blocked' if sc in (401, 403, 406, 429, 451, 503) else 'http'
            time.sleep(get_random_delay() * (2 if sc == 429 else 1))
        except requests.exceptions.SSLError:
            kind = 'ssl'
            time.sleep(get_random_delay())
        except requests.exceptions.ConnectionError as e:
            s = str(e)
            if any(x in s for x in ('NameResolution', 'Name or service not known', 'getaddrinfo', 'nodename nor servname')):
                return None, 'dns'
            kind = 'conn'
            time.sleep(get_random_delay())
        except requests.exceptions.Timeout:
            kind = 'timeout'
            time.sleep(get_random_delay())
        except Exception:
            kind = 'error'
            time.sleep(get_random_delay())
    return None, kind


def http_get(url, timeout=TIMEOUT, intentos=MAX_INTENTOS):
    return fetch(url, intentos, timeout)[0]

# ============================================================================
# NORMALISATION
# ============================================================================

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[’'`\-_/]", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def limpiar(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\xa0', ' ')).strip()

# ============================================================================
# LÉXICO v7 (modo "amplio" = recall máximo, como la versión original)
# ============================================================================

PALABRAS_CLAVE_CRIMEN = [
    'narcotrafico', 'cartel', 'cártel', 'narco', 'narcos', 'capo', 'jefe de plaza',
    'sicariato', 'sicario', 'ajuste de cuentas', 'balacera', 'masacre', 'fosa clandestina',
    'levantón', 'secuestro', 'extorsión', 'cobro de piso', 'lavado de activos',
    'testaferro', 'cocaina', 'fentanilo', 'heroína', 'metanfetamina',
    'microtrafico', 'narcomenudeo', 'cocina de droga', 'laboratorio clandestino',
    'narcofosa', 'narcobloqueo', 'narcoviolencia', 'huachicol', 'trasiego', 'carfentanilo',
    'homicidio doloso', 'feminicidio', 'decapitado', 'descuartizado',
    'desaparición forzada', 'guerra de carteles', 'célula criminal', 'megabanda', 'banda criminal',
    'paramilitar', 'megadecomiso', 'narcoavioneta', 'narcosubmarino', 'narcotunel', 'extradición',
    'narcoterrorismo', 'motín', 'fuga de cárcel', 'megafuga',
    'tráfico de drogas', 'facção', 'chacina', 'tiroteio', 'lavagem de dinheiro', 'drug trafficking', 'money laundering',
]

# ============================================================================
# TIPOS (narco · violencia armada · finanzas ilícitas)
#   clave, icono, color, categoría, severidad, peso, nombres(es|en), fuerte, débil
#   fuerte = término inequívoco (basta solo)    débil = ambiguo (exige indicio policial/judicial)
#   Categorías internas: fisico = narcotráfico y crimen organizado · rue = violencia armada (alarma) · cyber = finanzas ilícitas y corrupción
# ============================================================================

_TIPOS = [
    # ------------------------------------------------ narcotráfico y crimen organizado
    ('narcotrafico', '💊', '#a78bfa', 'fisico', 5, 1.0, 'Narcotráfico / Drogas|Drug trafficking',
     r"narcotraf\w*|trafic\w* de (?:drogas?|estupefacientes|cocaina|fentanilo|marihuana|metanfetaminas?)|narcolaborator\w*|narcosubmarin\w*|narcoavion\w*|narcotunel\w*|narcolancha\w*|narcocultiv\w*|narcopist\w*|narcobodega\w*|narcomenudeo|microtrafico|narcocasa\w*|laboratorios? (?:clandestinos?|de drogas?|de cocaina|de metanfetaminas?)|cocinas? (?:clandestinas?|de droga)|"
     r"toneladas? de (?:cocaina|droga|drogas|marihuana|cannabis|metanfetaminas?)|(?:decomis\w*|incaut\w*|asegur\w*|apreend\w*|apreensao|apreensoes|secuestr\w*) (?:de |del |un |una |mas de |casi |cerca de )?(?:\d+ |\w+ ){0,4}(?:cocaina|fentanilo|metanfetaminas?|heroina|drogas?|marihuana|cannabis|cristal|pasta base|clorhidrato|tusi|maconha|alijos?|cargamentos? de droga)|"
     r"cargamentos? de (?:droga|cocaina|estupefacientes|fentanilo)|fentanilo|carfentanilo|metanfetaminas?|cocaina|pasta base|clorhidrato de cocaina|rutas? del narco|corredor del narco|cultivos? (?:ilicitos?|de coca|de amapola)|hoja de coca|plantios? de (?:marihuana|coca|maconha)|narcos?|narcotraficantes?|narcotrafico|narcoestado|narcodinero|narcocorridos?|"
     r"traficantes? de drogas?|trafico de drogas|drug (?:trafficking|traffickers?|lords?|cartels?|lab|labs|smuggling|bust|seizure)|narco sub\w*|cocaine|fentanyl|methamphetamine|maconha|cocaina apreendida",
     r"drogas?|estupefacientes|marihuana|cannabis|crack|heroina|cristal|pastillas|trafico|traficantes?|alijos?|narcotico\w*|sustancias ilicitas|narcomenudeo|dealers?"),
    ('cartel', '🕸️', '#7c3aed', 'fisico', 6, 1.1, 'Cártel / Organización criminal|Cartel / Criminal organization',
     r"carteles? (?:de|del|dos|los|las|la) \w+|cartel (?:criminal|narco|mexicano|colombiano|jalisco|sinaloa|del golfo|del noreste|del norte|de juarez|de tijuana|de medellin|de cali)|cjng|jalisco nueva generacion|cartel de sinaloa|chapitos|mayiza|mayo zambada|el mencho|chapo guzman|ovidio guzman|"
     r"zetas|cartel del golfo|cartel del noreste|familia michoacana|caballeros templarios|cartel santa rosa de lima|clan del golfo|autodefensas gaitanistas|agc|tren de aragua|tren de guayana|primer comando da capital|pcc|comando vermelho|terceiro comando|amigos dos amigos|familia do norte|"
     r"los choneros|los lobos|los lagartos|los tiguerones|los pipos|los ri\w+|latin kings|mara salvatrucha|ms 13|ms13|barrio 18|pandilla 18|maras?|pandillas?|sendero luminoso|eln|farc|disidencias? de las farc|segunda marquetalia|clan de oriente|los rastrojos|los urabenos|los pelusos|los caparros|"
     r"organizaciones? criminales?|organizacion criminal|crimen organizado|organizacao criminosa|crime organizado|bandas? criminales?|megabandas?|redes? criminales?|estructuras? criminales?|celulas? (?:criminales?|delictivas?)|grupos? (?:criminales?|delincuenciales?|armados? ilegales?|armados? organizados?)|facc(?:ao|oes|iones) criminosas?|facc(?:ao|oes)|"
     r"milicias?|milicianos?|jefes? de plaza|cabecillas?|lideres? de (?:la |el )?(?:banda|organizacion|cartel|pandilla)|capos?(?= de| del| del cartel)|criminal (?:organization|group|gang)s?|drug gangs?|cartel (?:leader|boss|member)s?|cartels?|extradita\w*|extradicion\w*",
     r"bandas?|delincuentes?|criminales?|pandilleros?|bandidos?|gangs?"),
    ('extorsion', '🗣️', '#d97706', 'fisico', 5, 1.0, 'Extorsión / Cobro de piso|Extortion / Protection racket',
     r"extorsion\w*|extorsionadores?|extorsionistas?|extorsionar\w*|extorquir\w*|cobros? de (?:piso|vacuna|cupos?)|derechos? de piso|cobro de cuota|cuotas? (?:criminales?|a comerciantes)|vacunas? (?:a|de) (?:comerciantes|transportistas|empresarios|negocios)|prestamos? gota a gota|gota a gota|prestamistas? gota|extortion|protection racket|extorsao",
     r"vacunas?|cupos?|usureros?|usura|cobranzas?"),
    ('secuestro', '⛓️', '#db2777', 'fisico', 6, 1.0, 'Secuestro / Levantón|Kidnapping',
     r"secuestr\w*|levanton\w*|levantad[oa]s?|privacion ilegal de la libertad|plagios?|plagiad\w*|sequestr\w*|kidnap\w*|rapto|raptad\w*|rehenes|toma de rehenes|autosecuestro",
     None),
    ('desaparicion', '❓', '#c084fc', 'fisico', 5, 1.0, 'Desaparición / Fosas clandestinas|Disappearance / Mass graves',
     r"fosas? (?:clandestinas?|comunes?)|narcofosas?|desaparicion (?:forzada|de personas)|desaparecidos|madres buscadoras|colectivos? de busqueda|buscadoras|crematorios? clandestinos?|campos? de exterminio|restos? humanos|cuerpos? (?:hallados|encontrados|localizados|enterrados|calcinados)|osamentas?|cementerios? clandestinos?|enterrados? clandestinamente|mass graves?|disappeared|clandestine graves?",
     r"desaparecid[oa]s?|desaparecio|desaparecen|desaparecieron"),
    ('trafico_armas', '🔫', '#be123c', 'fisico', 5, 1.0, 'Tráfico de armas|Arms trafficking',
     r"trafico (?:ilicito )?de armas|contrabando de armas|armas? de (?:alto poder|grueso calibre|guerra|uso exclusivo)|armamento (?:decomisado|asegurado|incautado)|arsenal (?:decomisado|asegurado|incautado|del cartel)|fusiles? de asalto|ak ?47|ar ?15|barrett|lanzagranadas?|trafico de municiones|arms (?:trafficking|smuggling)|trafico de explosivos",
     None),
    ('ilicitos', '⛏️', '#f59e0b', 'fisico', 4, 0.9, 'Economías ilícitas (huachicol, minería, trata)|Illicit economies (fuel theft, mining, trafficking)',
     r"huachicol\w*|robo de combustible|tomas? clandestinas?|mineria ilegal|mineros? ilegales?|garimpo ilegal|garimpeiros?|extraccion ilegal de (?:oro|minerales)|oro ilegal|tala ilegal|trata de personas|trafico de (?:personas|migrantes|especies)|polleros?|pesca ilegal|contrabando|robo de ganado|illegal (?:mining|logging)|human (?:trafficking|smuggling)|fuel theft|tráfico humano",
     r"coyotes?|migrantes? (?:rescatados|secuestrados)"),
    ('homicidio', '🔪', '#ef4444', 'fisico', 4, 0.9, 'Homicidio / Feminicidio|Homicide / Femicide',
     r"homicidios?|feminicidios?|femicidios?|asesinatos?|asesinad[oa]s?|asesinan|asesinaron|mataron a|matan a|muertes? violentas?|cuerpos? sin vida|cadaveres?|decapitad\w*|descuartizad\w*|encobijad\w*|encajuelad\w*|calcinad[oa]s?|encontrad[oa]s? (?:muert|sin vida)|homicidio doloso|assassinat\w*|assassinado|assassinada|murder\w*|homicide\w*|femicide\w*",
     r"muert[oa]s?|fallecid[oa]s?|victimas?|cuerpos?"),
    # ------------------------------------------------ violencia armada (dispara la alarma)
    ('sicariato', '🎯', '#dc2626', 'rue', 7, 1.2, 'Sicariato / Ejecución|Hitman killing / Execution',
     r"sicari\w*|ajustes? de cuentas|ejecutad[oa]s? (?:a|con) (?:balazos|tiros|disparos)|tiro de gracia|plomazo|ataques? sicarial\w*|asesinad[oa]s? a (?:balazos|tiros|disparos)|matan a (?:balazos|tiros)|mataron a (?:balazos|tiros)|acribillad\w*|pistoler\w*|pistoleiros?|executad[oa]s? a tiros|hitmen|hitman|contract killings?|gunned down|ataque armado contra|crimen de encargo",
     r"ejecutad[oa]s?|ejecucion|ejecuciones"),
    ('masacre', '💀', '#991b1b', 'rue', 9, 1.3, 'Masacre / Multihomicidio|Massacre / Mass killing',
     r"masacres?|matanzas?|multihomicidios?|chacinas?|(?:ataque|balacera|tiroteo|enfrentamiento|emboscada|ataque armado|ataque a balazos) (?:\w+ ){0,4}(?:deja|dejo|dejan|dejaron|con saldo de|saldo de|cobra|cobro|provoca|provoco) (?:al menos |mas de |casi |un saldo de )?(?:[3-9]|\d{2,}|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|varios|multiples|decenas) (?:\w+ ){0,2}(?:muert\w*|vidas|victimas|fallecid\w*|asesinad\w*|cuerpos)|"
     r"(?:asesinan|asesinaron|matan|mataron|ejecutan|ejecutaron|masacran|masacraron) a (?:\d+|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|varios|al menos \w+|mas de \w+)|(?:\d+|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince) (?:personas |jovenes |hombres |mujeres |policias |militares |soldados |mineros |campesinos |indigenas |presos |reos )?(?:asesinad[oa]s|muert[oa]s a (?:balazos|tiros)|ejecutad[oa]s|masacrad[oa]s)|"
     r"fosas con (?:\d+|\w+) cuerpos|mass (?:shooting|killing)|massacres?|mortos em (?:ataque|tiroteio|operacao)|operacao (?:policial )?(?:deixa|deixou) (?:\d+|\w+) mortos|multiple killings?",
     None),
    ('balacera', '💥', '#ef4444', 'rue', 6, 1.1, 'Balacera / Enfrentamiento armado|Shootout / Armed clash',
     r"balacer\w*|tiroteos?|tiroteios?|enfrentamientos? (?:armados?|a balazos|a tiros|entre (?:sicarios|grupos armados|bandas|carteles|fuerzas|militares|policias|delincuentes|criminales|pandillas|facciones)|con (?:sicarios|grupos armados|delincuentes|policias|militares|fuerzas de seguridad|el ejercito|la policia|criminales|pandilleros))|intercambio de (?:disparos|balazos|fuego)|"
     r"ataques? (?:armados?|a balazos|a tiros)|balazos|hombres armados|comando armado|comandos armados|sujetos armados|civiles armados|gatilleros?|persecucion (?:armada|con disparos|a balazos)|shootouts?|shootings?|gunfights?|gunmen|gunfire|armed (?:clash|attack|men)|troca\w* (?:de|con) disparos|confronto armado|troca de tiros|baleado|baleada|baleados",
     r"disparos?|detonaciones?|tiros?|heridos? de bala|herid\w* por arma de fuego|armas? de fuego"),
    ('narcobloqueo', '🚧', '#f97316', 'rue', 7, 1.2, 'Narcobloqueo / Jornada violenta|Narco-blockade / Violent day',
     r"narcobloqueos?|bloqueos? (?:con|y|de) (?:vehiculos|camiones|unidades|trailers?) (?:incendiad\w*|quemad\w*)|quema de (?:vehiculos|camiones|autobuses|unidades|negocios|tiendas|oxxos?|gasolineras)|vehiculos? (?:incendiad\w*|quemad\w*)|jornada(?:s)? (?:violenta|de violencia|negra)|ola de violencia|toque de queda|paro armado|plan pistola|plan balazo|ataques? incendiari\w*|queima de (?:onibus|veiculos)|ataques? coordinad\w*|ola de ataques|coordinated attacks?|violent (?:day|wave)|state of emergency over violence|estado de excepcion por violencia|estado de emergencia por (?:violencia|inseguridad)|ataque a (?:comisarias?|estaciones de policia)",
     r"bloqueos?|incendios? de vehiculos|disturbios"),
    ('ataque_fuerzas', '🛡️', '#e11d48', 'rue', 8, 1.2, 'Ataque a fuerzas de seguridad / periodistas|Attack on security forces / journalists',
     r"(?:policias?|militares?|soldados?|marinos?|agentes?|guardias?|carabineros?|gendarmes?|custodios?|penitenciarios?|fiscales?|jueces?|juezas?|magistrad\w*|periodistas?|comunicadores?|alcald\w*|candidat\w*|regidores?|concejales?|activistas?|lideres? (?:sociales?|indigenas?|comunitarios?)|defensores? (?:ambientales?|de derechos humanos)|elementos de la (?:guardia nacional|sedena|marina|policia))(?: (?:de|del|en) (?:\w+ ){1,3}?)? (?:fueron |son |es |era |ha sido |han sido |fue )?(?:asesinad\w*|emboscad\w*|atacad\w*|baleado\w*|ejecutad\w*|acribillad\w*|matad\w*|secuestrad\w*|abatid\w*)|"
     r"(?:asesinan|asesinaron|matan|mataron|ejecutan|ejecutaron|secuestran|secuestraron|atacan|atacaron|balean|baleaban|baleo) (?:a )?(?:un |una |el |la |dos |tres |otro |otra )?(?:periodista|comunicador\w*|alcalde|alcaldesa|candidat\w*|regidor\w*|concejal\w*|activista|lider\w* (?:social|indigena|comunitari\w*)|defensor\w* (?:ambiental|de derechos humanos)|fiscal|juez|jueza|policia|militar|soldado|marino|agente)|emboscadas?|ataques? (?:contra|a) (?:policias|militares|soldados|convoyes?|cuarteles?|estaciones? de policia|comisarias?|bases? militares?|patrullas?|instalaciones militares|agentes|elementos)|drones? (?:explosivos?|con explosivos|artillados)|minas? antipersonal(?:es)?|asesinato de (?:un |una |el |la |dos |tres )?(?:periodista|alcalde|alcaldesa|candidat\w*|fiscal|juez|jueza|policia|militar|lider\w*|activista|defensor\w*)|"
     r"policias? (?:muertos|asesinados|abatidos)|militares? (?:muertos|asesinados|abatidos)|soldados? (?:muertos|asesinados|abatidos)|journalists? (?:killed|murdered)|killing of (?:a |an )?(?:journalist|mayor|police\w*|soldier\w*|judge|prosecutor)|police (?:ambush|officers? killed)|soldiers? killed|policiais? (?:mortos|baleados|assassinados)",
     None),
    ('carcel', '🔓', '#fb923c', 'rue', 7, 1.1, 'Motín / Fuga / Cárcel|Prison riot / Escape',
     r"motines?|amotinad\w*|motim|motins|fugas? (?:masiva )?de (?:presos|reos|internos|reclusos|detenidos|la carcel|el penal|un penal|una carcel)|(?:presos|reos|reclusos|internos) (?:se fugan|se fugaron|fugados|evadidos)|megafugas?|evasion (?:de|masiva)|masacre (?:carcelaria|en (?:la |el )?(?:carcel|penal|prision|penitenciaria))|rina (?:en|entre) (?:presos|reos|internos|el penal|la carcel)|crisis carcelaria|rebelion (?:carcelaria|de presos)|fuga de presos|prison (?:riot|break|massacre)|jailbreak|rebeliao em presidio|toma del penal",
     r"penal|carcel|reclusorio|penitenciaria|presidio"),
    ('terrorismo', '💣', '#c026d3', 'rue', 9, 1.2, 'Atentado explosivo / Narcoterrorismo|Bombing / Narco-terrorism',
     r"atentados? (?:con|explosiv\w*|terrorista|con bomba|con explosivos|contra)|coches? bomba|carros? bomba|autobomba|explosion de (?:coche|carro|moto|artefacto|vehiculo) bomba|artefactos? explosivos?|explosivos? (?:detonad\w*|colocad\w*|lanzad\w*)|ataques? con (?:explosivos|drones|granadas)|granadazos?|granadas? (?:lanzad\w*|detonad\w*)|car bomb\w*|bomb attacks?|terrorist attacks?|narco ?terror\w*|motobomba|explosive (?:attack|device)s?",
     r"atentados?|explosiones?|bombas?"),
    # ------------------------------------------------ finanzas ilícitas y corrupción
    ('lavado', '💰', '#fbbf24', 'cyber', 5, 1.0, 'Lavado de dinero / Finanzas ilícitas|Money laundering / Illicit finance',
     r"lavado de (?:activos|dinero|capitales)|blanqueo de (?:capitales|dinero)|lavagem de dinheiro|money laundering|testaferros?|prestanombres|empresas? (?:fachada|pantalla)|shell compan\w+|operaciones con recursos de procedencia ilicita|orpi|financiamiento (?:del|al) (?:narcotrafico|terrorismo|crimen organizado)|extincion de dominio|casas? de cambio ilegales?|remesas? ilicitas?|narcodinero|fondos ilicitos|dinero ilicito|bienes (?:decomisados|incautados|asegurados) (?:al|a la|del) (?:cartel|narco)|sanciones? (?:de la ofac|del tesoro)|ofac (?:sanciona|sanctions)",
     r"lavado|blanqueo|ofac"),
    ('corrupcion', '💼', '#f97316', 'cyber', 4, 1.25, 'Corrupción / Narcopolítica|Corruption / Narco-politics',
     r"(?:policias?|funcionarios?|militares?|jueces?|alcaldes?|fiscales?|agentes?|politicos?|diputados?|senadores?|gobernadores?|exalcaldes?|exgobernadores?|comandantes?|generales?) (?:\w+ ){0,3}(?:ligad\w*|vinculad\w*|relacionad\w*|coludid\w*|aliad\w*|protegid\w*|al servicio) (?:al|a|con|del) (?:el )?(?:narco\w*|cartel\w*|crimen organizado|trafico de drogas)|narcopolitic\w*|narcogobern\w*|narcoalcald\w*|narcogeneral\w*|vinculos? con (?:el )?(?:narco\w*|crimen organizado|cartel\w*|trafico de drogas)|(?:nexos|lazos|ligas) (?:con|con el) (?:narco\w*|crimen organizado|cartel\w*)|sobornos? (?:a|para) (?:policias|jueces|funcionarios|militares|fiscales|autoridades)|policias? corruptos?|funcionarios? corruptos?|corrupcion policial|"
     r"protegian al (?:cartel|narco)|protegia al (?:cartel|narco)|pagos? (?:al|del) (?:narco|cartel|crimen organizado)|financiamiento criminal de campanas?|dinero del narco en (?:campanas?|politica)|narco (?:corruption|politicians?)|corrupcao policial|corrupt (?:police|officials?) (?:tied|linked) to (?:cartels?|drug)",
     None),
    # ------------------------------------------------ otros
]


def _rx(s):
    return re.compile(r'\b(?:' + s + r')\b')


TIPOS_CRIMEN = {}
for _k, _i, _c, _cat, _sev, _w, _n, _s, _wk in _TIPOS:
    _nm = _n.split('|')
    TIPOS_CRIMEN[_k] = {
        'icono': _i, 'color': _c, 'cat': _cat, 'sev': _sev, 'peso': _w,
        'nombre': _nm[0], 'es': _nm[0], 'en': _nm[1] if len(_nm) > 1 else _nm[0],
        'srx': _rx(_s), 'wrx': _rx(_wk) if _wk else None,
    }
TIPOS_CRIMEN['other'] = {'icono': '❓', 'color': '#6b7280', 'cat': 'fisico', 'sev': 2, 'peso': 0,
                         'nombre': 'Otro', 'es': 'Otro', 'en': 'Other',
                         'srx': re.compile(r'$^'), 'wrx': None}
CATEGORIAS = ('fisico', 'rue', 'cyber')

# ---- expresiones neutralizadas antes de analizar (usos no criminales de palabras ambiguas)
_SCRUB = re.compile(r"\b(?:cartel(?:es)? (?:de (?:cine|la pelicula|la serie|publicitario|publicidad|anuncio|bienvenida|conciertos?|festival|toros|fiestas|lucha)|electoral|politico|promocional)|cartelera|cartelitos?|"
                    r"narcos? (?:la serie|serie|temporada|netflix|capitulo|el musical)|narcos?:? mexico|"
                    r"plaza (?:de armas|mayor|publica|de toros|comercial|de la constitucion|de mayo|bolivar|san martin|italia|garibaldi)|"
                    r"banda (?:de musica|sonora|musical|norteña|ancha|municipal|sinfonica|de rock|de samba|de guerra|de sonido|de pop|de cumbia)|bandas? (?:de|del) (?:rock|pop|musica|jazz|heavy)|"
                    r"golpe (?:de calor|de suerte|de efecto|de estado|maestro|de timon|bajo)|golpes? de (?:calor|suerte)|"
                    r"masacre (?:deportiva|futbolistica|en el marcador|electoral|en la bolsa|de precios)|matanza (?:de cerdos|tradicional|del cerdo)|"
                    r"ataque (?:de ansiedad|de panico|cardiaco|epileptico|de risa|de asma|al corazon)|"
                    r"drogas? (?:de diseño en la serie|legales?)|marihuana (?:medicinal|terapeutica|recreativa)|legalizacion de (?:la )?(?:marihuana|cannabis)|cannabis (?:medicinal|terapeutico)|"
                    r"crack (?:del futbol|del equipo|de la liga)|el crack|cristal (?:de la ventana|roto|templado)|"
                    r"tiros? (?:libres?|de esquina|de media distancia|al arco|al aro|de tres|a puerta)|disparos? (?:al arco|a puerta|de tres|desde fuera)|balacera de goles|"
                    r"sicario[s]? (?:de la pelicula|de netflix)|guerra (?:comercial|de precios|de audiencias|de tarifas|de aranceles|fria|de las galaxias|de tronos)|"
                    r"lavado (?:de (?:autos?|ropa|manos|cara|cerebro|vehiculos|coches)|automatico)|lavadero|"
                    r"corrupcion (?:de menores?)|golpe de estado simulado|"
                    r"mina (?:de oro|de litio|de cobre|de plata|de carbon)|minas? (?:de|en) (?:el juego|minecraft))\b")
_POLICE = re.compile(r"\b(?:policia\w*|policial\w*|fiscali\w*|fiscal(?:es)?|ministerio publico|mp|detenid[oa]s?|capturad[oa]s?|arrestad[oa]s?|aprehendid[oa]s?|imputad[oa]s?|procesad[oa]s?|sentenciad[oa]s?|condenad[oa]s?|vinculad[oa]s? a proceso|"
                     r"juez\w*|juzgado|tribunal\w*|sentencia|operativo|allanamientos?|cateos?|autoridades|militares?|ejercito|marina|guardia nacional|gendarmeria|carabineros|pdi|dea|interpol|fbi|delegacia|policia federal|preso\w*|"
                     r"apreensao|prisao|presos?|reos?|sospechos[oa]s?|sospechosos?|acusad[oa]s?|investigacion|investigan|indagan|denuncia\w*|querella|victimas?|heridos?|lesionad[oa]s?|cadaver\w*|cuerpos?|sedena|sspc|fgr|fiscalia|"
                     r"police|prosecutors?|arrest\w*|suspects?|killed|gunmen|authorities|investigat\w*|sentenced|charged|indicted|seized)\b")
_SPORT = re.compile(r"\b(?:futbol|futbolistas?|liga mx|liga profesional|primera division|copa libertadores|copa sudamericana|copa america|mundial|seleccion|eliminatorias|goleada|goles?|partido|torneo|campeonato|entrenador|tecnico|dt|delantero|portero|arquero|mercado de pases|fichajes?|"
                    r"boca juniors|river plate|flamengo|corinthians|palmeiras|santos fc|club america|chivas|tigres|rayados|cruz azul|pumas|millonarios|nacional|junior|america de cali|colo colo|universidad de chile|penarol|olimpia|"
                    r"beisbol|basquetbol|baloncesto|tenis|golf|formula 1|ciclismo|boxeo|ufc|nba|nfl|mlb|olimpicos?|juegos olimpicos|atletismo|brasileirao|libertadores)\b")
_SPORT_OK = {'balacera', 'sicariato', 'masacre', 'ataque_fuerzas', 'homicidio', 'terrorismo', 'secuestro'}
_CULTURE = re.compile(r"\b(?:peliculas?|series?|telenovelas?|novelas?|libros?|albumes?|album|conciertos?|festivales?|espectaculos?|exposiciones?|museos?|teatro|cine|netflix|hbo|amazon prime|videojuegos?|documentales?|podcasts?|programas?|episodios?|actores?|actrices?|"
                      r"cantantes?|reggaeton|trap|corridos? tumbados|narcocorridos?|concierto|reality|miss universo|influencers?|tiktokers?|youtubers?|estreno|taquilla|premios?|alfombra roja|filme|filmes|musica)\b")
_LIFESTYLE = re.compile(r"\b(?:recetas?|horoscopo|clima|pronostico del tiempo|dolar|tipo de cambio|bolsa|loteria|chance|turismo|vacaciones|viajes?|ofertas?|promociones?|shopping|belleza|cocina|restaurantes?|jardineria|moda|dieta|salud|mascotas?)\b")
_ACCIDENT = re.compile(r"\b(?:accidentes? (?:de transito|vial|de carretera|automovilistico|aereo|laboral|de moto|de autobus|de trenes?|ferroviario|domestico)|choques?|volcaduras?|atropell\w*|colisiones?|carambolas?|ahogad\w*|inundaciones?|sismos?|terremotos?|huracanes?|tormentas?|deslaves?|derrumbes?|incendios? forestales?|"
                        r"sin vida por (?:ahogamiento|intoxicacion|electrocucion)|intoxicacion|electrocutad\w*|caida|cayo|derrumbe|explosion de gas|fuga de gas|accident\w*)\b")
_NAV = re.compile(r"\b(?:suscribete|suscribase|newsletter|iniciar sesion|mi cuenta|registrate|cookies|aviso legal|politica de privacidad|lee tambien|leer mas|ver mas|compartir|siguenos|publicidad|patrocinado|conectate|menu|"
                  r"todos los derechos reservados|terminos y condiciones|contactenos|quienes somos|descarga la app)\b")
_FOREIGN = re.compile(r"\b(?:espana|espanol(?:es|a|as)?|madrid|barcelona|valencia espana|sevilla|andalucia|galicia|europa|europeo|francia|paris|italia|roma|alemania|reino unido|londres|inglaterra|rusia|ucrania|gaza|israel|palestina|hamas|iran|china|japon|corea|india|africa|marruecos|nigeria|"
                      r"australia|canada|turquia|siria|afganistan|filipinas|tailandia|indonesia|texas|california|nueva york|florida|chicago|nueva jersey|arizona|nuevo mexico estados|washington|casa blanca|trump|biden|congreso de eeuu|senado de eeuu|"
                      r"spain|france|italy|germany|russia|ukraine|china|japan|india|africa|morocco|nigeria|australia|canada|uk|london|new york|texas|california|florida)\b")
_LATAM = re.compile(r"\b(?:mexic\w*|colombi\w*|brasil\w*|brazil\w*|argentin\w*|chile\w*|peru\w*|ecuador\w*|venezol\w*|venezuel\w*|bolivi\w*|paraguay\w*|uruguay\w*|salvador\w*|hondure\w*|guatemal\w*|nicaragu\w*|costarric\w*|costa rica|panam\w*|dominican\w*|haiti\w*|cuba\w*|jamaic\w*|latinoameric\w*|america latina|latin america|centroameric\w*|sudamerica\w*|caribe|"
                    r"sinaloa|jalisco|cjng|chapitos|zetas|tren de aragua|clan del golfo|pcc|comando vermelho|mara salvatrucha|ms ?13|barrio 18|choneros|chapo|mencho|zambada|farc|eln|sendero luminoso|culiacan|tijuana|juarez|medellin|guayaquil|rosario|favela|vraem|catatumbo|"
                    r"sedena|sspc|fgr|guardia nacional|carabineros|gendarmeria|policia federal|dea|ofac|cartel(?:es)? (?:de|del))\b")
_FRANCE = _LATAM                                   # (compat: nombre usado por el motor para "contexto del país")
_INC_STRONG = re.compile(r"\b(?:detenid\w*|capturad\w*|arrestad\w*|condenad\w*|sentenciad\w*|imputad\w*|vinculad\w*|asegurad\w*|decomisad\w*|incautad\w*|desmantel\w*|abatid\w*|asesinad\w*|ejecutad\w*|rescatad\w*|liberad\w*)\b")
_ADVICE = re.compile(r"\b(?:como (?:evitar|prevenir|protegerse|detectar|reconocer|denunciar)|consejos?|recomendaciones?|guia|tutorial|taller|seminario|webinar|capacitacion|curso|conferencia|foro|campana de prevencion|prevencion del delito)\b")
_VULN = re.compile(r"(?!x)x")                      # no aplica en Latam
_MOD_SEV = [
    (re.compile(r"\b(?:muert[oa]s?|fallecid\w*|asesinad\w*|ejecutad\w*|abatid\w*|sin vida|killed|dead|mortos)\b"), 1),
    (re.compile(r"\b(?:herid[oa]s?|lesionad\w*|hospitalizad\w*|injured|feridos)\b"), 1),
    (re.compile(r"\b(?:armas? de (?:alto poder|grueso calibre|guerra)|fusiles?|ak ?47|ar ?15|granadas?|explosivos?|drones?|lanzagranadas?|rehenes|ametralladoras?|barrett)\b"), 1),
    (re.compile(r"\b(?:ninos?|menores|ninas?|bebes?|familia|estudiantes|periodistas?|alcald\w*|candidat\w*|policias?|militares|soldados|marinos|mujeres|adolescentes)\b"), 1),
    (re.compile(r"\b(?:decenas|centenas|cientos|multiples?|varios muertos|al menos (?:\d+|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)|(?:\d{2,}) (?:muertos|asesinados|cuerpos)|masivo|masiva)\b"), 1),
]
_MENU_TITULOS = re.compile(r"^(?:inicio|menu|buscar|busqueda|suscripcion|contacto|policiales|policial|judicial|justicia|seguridad|sucesos|nacional|internacional|politica|economia|deportes|cronica|cronica roja|portada|ultimas noticias)$")


def clasificar_detalle(titulo, texto='', sens=None, geo_prec='none'):
    """Clasifica un titular (+resumen). Devuelve dict(tipo, cat, sev, conf, hits) o {'reject': motivo}."""
    sens = sens or SENSIBILIDAD
    thr = _UMBRAL_CONF.get(sens, 45)
    full = limpiar((titulo or '') + ' ' + (texto or ''))[:900]
    n = _SCRUB.sub(' ', norm(full))
    tn = _SCRUB.sub(' ', norm(titulo or ''))
    if len(tn) <= 45 and (_NAV.search(tn) or _MENU_TITULOS.match(tn)):
        return {'reject': 'nav'}
    cue = bool(_POLICE.search(n))
    best = None
    for k, d in TIPOS_CRIMEN.items():
        if k == 'other':
            continue
        ms = d['srx'].findall(n)
        if ms:
            nt = len(set(ms))
            intitle = bool(d['srx'].search(tn))
            cand = (min(nt, 3) * d['peso'] * (1.5 if intitle else 1.0), d['sev'], k, True, nt, intitle)
        elif d['wrx'] is not None and cue and d['wrx'].search(n):
            intitle = bool(d['wrx'].search(tn))
            cand = (0.4 * min(len(d['wrx'].findall(n)), 3) * d['peso'], d['sev'], k, False, 1, intitle)
        else:
            continue
        if best is None or cand[:2] > best[:2]:
            best = cand
    if best is None:
        if sens == 'amplio' and any(kw in full.lower() for kw in PALABRAS_CLAVE_CRIMEN):
            return {'tipo': 'other', 'cat': 'fisico', 'sev': 2, 'conf': 20, 'hits': 0}
        return {'reject': 'sin_keyword'}
    _, _, k, strong, nt, intitle = best
    d = TIPOS_CRIMEN[k]
    cat = d['cat']
    geo_txt = geo_prec in ('ciudad', 'depto')
    if _FOREIGN.search(n) and not _LATAM.search(n):
        return {'reject': 'foreign'}
    penalty = 0
    if _ADVICE.search(n) and not _INC_STRONG.search(n):
        return {'reject': 'advice'}
    if _ACCIDENT.search(n) and not strong:
        return {'reject': 'accident'}
    if _ACCIDENT.search(n) and strong and k in ('homicidio',) and not cue:
        return {'reject': 'accident'}
    if _CULTURE.search(n):
        if not cue:
            return {'reject': 'culture'}
        penalty += 10
    if _LIFESTYLE.search(n) and not strong:
        return {'reject': 'lifestyle'}
    if _SPORT.search(n):
        if k not in _SPORT_OK:
            return {'reject': 'sport'}
        penalty += 10
    conf = (45 + 5 * min(nt - 1, 3)) if strong else 30
    conf += (10 if intitle else 0) + (10 if cue else 0) + (10 if geo_txt else 0) - penalty
    conf = max(0, min(100, conf))
    if conf < thr:
        return {'reject': 'low_conf'}
    sev = d['sev']
    for rx, pts in _MOD_SEV:
        if rx.search(n):
            sev += pts
    return {'tipo': k, 'cat': cat, 'sev': max(1, min(10, sev)), 'conf': conf, 'hits': nt}


def clasificar(texto):
    """Compat v1 → (tipo, categoria, severidad) en modo equilibrado."""
    r = clasificar_detalle(texto, '', 'equilibrado')
    if 'reject' in r:
        return 'other', 'fisico', 1
    return r['tipo'], r['cat'], r['sev']


def es_conflicto(tipo, cat, sev, conf):
    """Un "conflicto" dispara la alarma: masacre, atentado explosivo o violencia armada ≥ umbral."""
    if conf < 45:
        return False
    if tipo in ('masacre', 'terrorismo'):
        return True
    return cat == 'rue' and sev >= UMBRAL_ALARMA

# ============================================================================
# GEOGRAFÍA LATAM: países (= "territorio" del motor) · estados/departamentos/provincias · ciudades
#   Cada evento se ubica: ciudad (precisa) > estado/depto (centroide) > país (centroide).  Siempre dentro del bbox del país.
# ============================================================================

# código|país|lat|lon|latmin|latmax|lonmin|lonmax|radio_jitter
_PAISES_RAW = """MX|México|23.60|-102.50|14.5|32.8|-118.5|-86.5|0.45
CO|Colombia|4.60|-74.10|-4.3|13.5|-82.0|-66.8|0.40
BR|Brasil|-14.20|-51.90|-33.8|5.3|-74.0|-34.7|0.60
AR|Argentina|-34.60|-64.00|-55.1|-21.7|-73.6|-53.6|0.60
CL|Chile|-33.45|-70.65|-56.0|-17.5|-75.7|-66.4|0.12
PE|Perú|-9.20|-75.00|-18.4|0.0|-81.4|-68.6|0.40
EC|Ecuador|-1.80|-78.20|-5.1|1.5|-92.1|-75.1|0.25
VE|Venezuela|7.10|-66.20|0.6|12.3|-73.4|-59.8|0.40
BO|Bolivia|-16.70|-64.70|-22.9|-9.6|-69.7|-57.4|0.50
PY|Paraguay|-23.40|-58.40|-27.6|-19.3|-62.7|-54.2|0.35
UY|Uruguay|-32.80|-56.00|-35.0|-30.0|-58.5|-53.0|0.25
SV|El Salvador|13.80|-88.90|13.1|14.5|-90.2|-87.6|0.12
HN|Honduras|14.80|-86.60|12.9|16.6|-89.4|-83.1|0.25
GT|Guatemala|15.50|-90.30|13.7|18.0|-92.3|-88.2|0.20
NI|Nicaragua|12.90|-85.20|10.7|15.1|-87.7|-82.5|0.25
CR|Costa Rica|9.90|-84.20|8.0|11.3|-86.0|-82.5|0.15
PA|Panamá|8.50|-80.00|7.1|9.7|-83.1|-77.1|0.15
DO|República Dominicana|18.90|-70.20|17.4|19.95|-72.1|-68.2|0.15
CU|Cuba|21.80|-79.00|19.8|23.3|-85.0|-74.1|0.30
HT|Haití|18.90|-72.70|18.0|20.1|-74.5|-71.6|0.15
JM|Jamaica|18.10|-77.30|17.7|18.6|-78.4|-76.2|0.10
TT|Trinidad y Tobago|10.60|-61.30|10.0|11.4|-61.95|-60.5|0.08
PR|Puerto Rico|18.22|-66.45|17.9|18.6|-67.3|-65.2|0.10
BZ|Belice|17.20|-88.70|15.9|18.5|-89.3|-87.5|0.15
GY|Guyana|4.90|-58.90|1.2|8.6|-61.4|-56.5|0.30
SR|Surinam|4.00|-56.00|1.8|6.0|-58.1|-53.9|0.25"""

PAISES = {}
_BBOX = {}
_JR = {}
for _ln in _PAISES_RAW.splitlines():
    _c, _n, _la, _lo, _a, _b, _d, _e, _j = _ln.split('|')
    PAISES[_c] = (_n, float(_la), float(_lo))
    _BBOX[_c] = (float(_a), float(_b), float(_d), float(_e))
    _JR[_c] = float(_j)
DEPS = PAISES                                    # en Latam, "departamento" del motor = país
DEP_BY_NAME = {norm(v[0]): k for k, v in PAISES.items()}
DEP_BY_NAME.update({'republica dominicana': 'DO', 'rep dominicana': 'DO', 'brasil': 'BR', 'brazil': 'BR', 'mexico': 'MX',
                    'peru': 'PE', 'panama': 'PA', 'belize': 'BZ', 'surinam': 'SR', 'suriname': 'SR', 'trinidad y tobago': 'TT',
                    'ee uu': None})
DEP_BY_NAME = {k: v for k, v in DEP_BY_NAME.items() if v}
# países citables en el texto (nombre propio, sin ambigüedad)
_PAIS_TXT = {n: c for n, c in DEP_BY_NAME.items() if n not in ('panama',)}
_PAIS_TXT['panama'] = 'PA'
_PAIS_RX = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, _PAIS_TXT), key=len, reverse=True)) + r')\b')

# código|estado/depto/provincia|lat|lon|país
_ADM1_RAW = """MX|Aguascalientes|21.88|-102.30
MX|Baja California|31.90|-115.30
MX|Baja California Sur|25.00|-111.70
MX|Campeche|18.80|-90.40
MX|Chiapas|16.50|-92.50
MX|Chihuahua|28.80|-106.40
MX|Ciudad de México|19.43|-99.13
MX|Coahuila|27.30|-102.00
MX|Colima|19.10|-103.90
MX|Durango|24.90|-104.90
MX|Guanajuato|21.00|-101.00
MX|Guerrero|17.50|-100.00
MX|Hidalgo|20.50|-98.90
MX|Jalisco|20.60|-103.60
MX|Estado de México|19.35|-99.60
MX|Michoacán|19.20|-101.90
MX|Morelos|18.75|-99.10
MX|Nayarit|21.80|-104.90
MX|Nuevo León|25.60|-99.90
MX|Oaxaca|17.00|-96.70
MX|Puebla|19.00|-97.90
MX|Querétaro|20.80|-100.00
MX|Quintana Roo|19.60|-88.00
MX|San Luis Potosí|22.50|-100.40
MX|Sinaloa|25.00|-107.40
MX|Sonora|29.60|-110.90
MX|Tabasco|17.90|-92.60
MX|Tamaulipas|24.00|-98.80
MX|Tlaxcala|19.40|-98.20
MX|Veracruz|19.40|-96.70
MX|Yucatán|20.80|-89.00
MX|Zacatecas|23.20|-102.90
CO|Amazonas|-1.50|-71.90
CO|Antioquia|6.70|-75.50
CO|Arauca|6.60|-70.80
CO|Atlántico|10.70|-74.90
CO|Bolívar|8.90|-74.50
CO|Boyacá|5.50|-73.40
CO|Caldas|5.30|-75.30
CO|Caquetá|1.00|-74.00
CO|Casanare|5.30|-71.70
CO|Cauca|2.40|-76.80
CO|Cesar|9.50|-73.40
CO|Chocó|5.90|-76.90
CO|Córdoba|8.30|-75.70
CO|Cundinamarca|5.00|-74.20
CO|Guainía|2.60|-68.50
CO|Guaviare|2.00|-72.30
CO|Huila|2.50|-75.60
CO|La Guajira|11.50|-72.50
CO|Magdalena|10.00|-74.30
CO|Meta|3.90|-73.00
CO|Nariño|1.30|-77.80
CO|Norte de Santander|8.00|-72.90
CO|Putumayo|0.40|-76.50
CO|Quindío|4.50|-75.70
CO|Risaralda|5.00|-75.90
CO|Santander|6.70|-73.20
CO|Sucre|9.00|-75.10
CO|Tolima|4.00|-75.30
CO|Valle del Cauca|3.80|-76.60
CO|Vaupés|0.90|-70.80
CO|Vichada|4.70|-69.40
CO|San Andrés y Providencia|12.55|-81.70
CO|Bogotá D.C.|4.71|-74.07
BR|Acre|-9.00|-70.50
BR|Alagoas|-9.60|-36.80
BR|Amapá|1.40|-51.80
BR|Amazonas|-3.50|-65.00
BR|Bahia|-12.50|-41.70
BR|Ceará|-5.20|-39.30
BR|Distrito Federal|-15.80|-47.90
BR|Espírito Santo|-19.60|-40.60
BR|Goiás|-15.90|-49.80
BR|Maranhão|-5.00|-45.30
BR|Mato Grosso|-12.60|-55.40
BR|Mato Grosso do Sul|-20.50|-54.60
BR|Minas Gerais|-18.50|-44.60
BR|Pará|-3.80|-52.00
BR|Paraíba|-7.10|-36.80
BR|Paraná|-24.60|-51.60
BR|Pernambuco|-8.30|-37.90
BR|Piauí|-7.70|-42.70
BR|Rio de Janeiro|-22.30|-42.70
BR|Rio Grande do Norte|-5.80|-36.60
BR|Rio Grande do Sul|-29.70|-53.50
BR|Rondônia|-10.90|-62.80
BR|Roraima|2.00|-61.40
BR|Santa Catarina|-27.30|-50.40
BR|São Paulo|-22.20|-48.80
BR|Sergipe|-10.60|-37.40
BR|Tocantins|-10.20|-48.30
AR|Buenos Aires|-36.50|-60.00
AR|Catamarca|-27.30|-66.90
AR|Chaco|-26.50|-60.90
AR|Chubut|-43.80|-68.80
AR|Córdoba|-32.10|-63.80
AR|Corrientes|-28.80|-57.80
AR|Entre Ríos|-32.00|-59.20
AR|Formosa|-24.90|-60.20
AR|Jujuy|-23.30|-65.70
AR|La Pampa|-37.10|-65.40
AR|La Rioja|-29.70|-67.20
AR|Mendoza|-34.60|-68.50
AR|Misiones|-26.90|-54.60
AR|Neuquén|-38.60|-70.10
AR|Río Negro|-40.10|-67.30
AR|Salta|-24.80|-65.40
AR|San Juan|-30.90|-68.90
AR|San Luis|-33.70|-66.00
AR|Santa Cruz|-48.80|-70.00
AR|Santa Fe|-31.00|-61.00
AR|Santiago del Estero|-27.80|-63.30
AR|Tierra del Fuego|-54.30|-67.50
AR|Tucumán|-26.90|-65.30
CL|Arica y Parinacota|-18.50|-69.80
CL|Tarapacá|-20.00|-69.50
CL|Antofagasta|-23.70|-69.30
CL|Atacama|-27.50|-70.30
CL|Coquimbo|-30.60|-71.00
CL|Valparaíso|-32.80|-71.00
CL|Región Metropolitana|-33.45|-70.65
CL|O'Higgins|-34.40|-71.00
CL|Maule|-35.50|-71.50
CL|Ñuble|-36.60|-72.00
CL|Biobío|-37.50|-72.50
CL|La Araucanía|-38.70|-72.40
CL|Los Ríos|-39.80|-72.40
CL|Los Lagos|-42.00|-73.00
CL|Aysén|-46.00|-73.50
CL|Magallanes|-52.00|-71.50
PE|Amazonas|-5.10|-78.00
PE|Áncash|-9.50|-77.70
PE|Apurímac|-14.00|-73.00
PE|Arequipa|-15.80|-72.50
PE|Ayacucho|-13.20|-74.20
PE|Cajamarca|-6.40|-78.60
PE|Callao|-12.05|-77.12
PE|Cusco|-13.00|-72.00
PE|Huancavelica|-13.00|-75.00
PE|Huánuco|-9.40|-76.20
PE|Ica|-14.10|-75.70
PE|Junín|-11.50|-75.00
PE|La Libertad|-7.90|-78.50
PE|Lambayeque|-6.40|-79.90
PE|Lima|-11.90|-76.60
PE|Loreto|-4.50|-74.50
PE|Madre de Dios|-12.00|-70.50
PE|Moquegua|-16.80|-70.90
PE|Pasco|-10.40|-75.30
PE|Piura|-5.20|-80.00
PE|Puno|-15.00|-70.00
PE|San Martín|-7.00|-76.70
PE|Tacna|-17.80|-70.20
PE|Tumbes|-3.80|-80.40
PE|Ucayali|-9.80|-73.50
EC|Azuay|-2.90|-79.00
EC|Bolívar|-1.70|-79.10
EC|Cañar|-2.50|-78.90
EC|Carchi|0.80|-77.90
EC|Chimborazo|-1.70|-78.70
EC|Cotopaxi|-0.80|-78.60
EC|El Oro|-3.40|-79.70
EC|Esmeraldas|0.95|-79.70
EC|Galápagos|-0.70|-90.40
EC|Guayas|-2.20|-79.90
EC|Imbabura|0.35|-78.10
EC|Loja|-4.00|-79.60
EC|Los Ríos|-1.40|-79.50
EC|Manabí|-1.00|-80.20
EC|Morona Santiago|-2.30|-78.10
EC|Napo|-1.00|-77.80
EC|Orellana|-0.50|-76.90
EC|Pastaza|-1.50|-77.90
EC|Pichincha|-0.15|-78.50
EC|Santa Elena|-2.20|-80.70
EC|Santo Domingo de los Tsáchilas|-0.25|-79.20
EC|Sucumbíos|0.10|-76.50
EC|Tungurahua|-1.25|-78.60
EC|Zamora Chinchipe|-4.00|-78.90
VE|Amazonas|3.40|-65.70
VE|Anzoátegui|8.80|-64.30
VE|Apure|7.20|-68.60
VE|Aragua|10.20|-67.40
VE|Barinas|8.50|-70.00
VE|Bolívar|6.50|-63.50
VE|Carabobo|10.10|-68.00
VE|Cojedes|9.50|-68.30
VE|Delta Amacuro|8.70|-61.40
VE|Distrito Capital|10.50|-66.90
VE|Falcón|11.20|-69.80
VE|Guárico|8.90|-66.60
VE|La Guaira|10.60|-66.95
VE|Lara|10.10|-69.80
VE|Mérida|8.60|-71.20
VE|Miranda|10.30|-66.40
VE|Monagas|9.40|-63.00
VE|Nueva Esparta|10.99|-64.00
VE|Portuguesa|9.10|-69.30
VE|Sucre|10.40|-63.50
VE|Táchira|7.90|-72.00
VE|Trujillo|9.40|-70.40
VE|Yaracuy|10.30|-68.70
VE|Zulia|10.00|-72.10
BO|Beni|-14.00|-65.00
BO|Chuquisaca|-20.00|-64.50
BO|Cochabamba|-17.40|-66.20
BO|La Paz|-16.50|-68.20
BO|Oruro|-18.00|-67.50
BO|Pando|-11.30|-67.50
BO|Potosí|-20.50|-66.80
BO|Santa Cruz|-17.80|-63.20
BO|Tarija|-21.50|-64.20
PY|Alto Paraguay|-20.50|-58.50
PY|Alto Paraná|-25.50|-55.00
PY|Amambay|-23.00|-56.00
PY|Boquerón|-22.00|-60.00
PY|Caaguazú|-25.40|-56.00
PY|Caazapá|-26.20|-56.20
PY|Canindeyú|-24.20|-55.20
PY|Central|-25.40|-57.50
PY|Concepción|-23.40|-57.40
PY|Cordillera|-25.20|-57.00
PY|Guairá|-25.80|-56.20
PY|Itapúa|-26.90|-55.80
PY|Misiones|-27.00|-57.00
PY|Ñeembucú|-26.80|-57.80
PY|Paraguarí|-26.00|-57.10
PY|Presidente Hayes|-24.00|-58.50
PY|San Pedro|-24.00|-56.50
UY|Artigas|-30.60|-56.80
UY|Canelones|-34.50|-56.00
UY|Cerro Largo|-32.40|-54.20
UY|Colonia|-34.10|-57.50
UY|Durazno|-33.00|-56.00
UY|Flores|-33.60|-56.90
UY|Florida|-34.10|-56.20
UY|Lavalleja|-33.90|-55.20
UY|Maldonado|-34.70|-54.90
UY|Montevideo|-34.85|-56.20
UY|Paysandú|-32.30|-57.60
UY|Río Negro|-32.80|-57.40
UY|Rivera|-31.40|-55.50
UY|Rocha|-34.00|-54.00
UY|Salto|-31.40|-57.50
UY|San José|-34.30|-56.70
UY|Soriano|-33.50|-57.70
UY|Tacuarembó|-31.70|-55.98
UY|Treinta y Tres|-33.20|-54.40
GT|Alta Verapaz|15.50|-90.00
GT|Baja Verapaz|15.10|-90.30
GT|Chimaltenango|14.65|-90.80
GT|Chiquimula|14.80|-89.50
GT|El Progreso|14.90|-89.90
GT|Escuintla|14.30|-90.80
GT|Guatemala|14.64|-90.50
GT|Huehuetenango|15.50|-91.50
GT|Izabal|15.50|-88.80
GT|Jalapa|14.60|-89.99
GT|Jutiapa|14.30|-89.90
GT|Petén|16.80|-90.00
GT|Quetzaltenango|14.85|-91.50
GT|Quiché|15.40|-91.00
GT|Retalhuleu|14.55|-91.70
GT|Sacatepéquez|14.55|-90.70
GT|San Marcos|15.00|-91.80
GT|Santa Rosa|14.20|-90.30
GT|Sololá|14.80|-91.20
GT|Suchitepéquez|14.40|-91.40
GT|Totonicapán|14.90|-91.35
GT|Zacapa|14.97|-89.50
HN|Atlántida|15.60|-87.00
HN|Choluteca|13.30|-87.20
HN|Colón|15.60|-85.70
HN|Comayagua|14.60|-87.70
HN|Copán|14.90|-88.90
HN|Cortés|15.40|-88.00
HN|El Paraíso|13.90|-86.60
HN|Francisco Morazán|14.10|-87.20
HN|Gracias a Dios|15.20|-84.00
HN|Intibucá|14.30|-88.20
HN|Islas de la Bahía|16.30|-86.50
HN|La Paz|14.30|-87.70
HN|Lempira|14.50|-88.60
HN|Ocotepeque|14.45|-89.10
HN|Olancho|14.80|-85.80
HN|Santa Bárbara|14.90|-88.20
HN|Valle|13.50|-87.60
HN|Yoro|15.00|-87.20
SV|Ahuachapán|13.90|-89.85
SV|Cabañas|13.85|-88.75
SV|Chalatenango|14.05|-88.90
SV|Cuscatlán|13.85|-89.05
SV|La Libertad|13.60|-89.30
SV|La Paz|13.45|-88.95
SV|La Unión|13.50|-87.85
SV|Morazán|13.75|-88.10
SV|San Miguel|13.50|-88.20
SV|San Salvador|13.75|-89.20
SV|San Vicente|13.60|-88.80
SV|Santa Ana|14.00|-89.50
SV|Sonsonate|13.70|-89.70
SV|Usulután|13.30|-88.50
NI|Boaco|12.50|-85.70
NI|Carazo|11.75|-86.20
NI|Chinandega|12.70|-87.00
NI|Chontales|12.10|-85.10
NI|Estelí|13.10|-86.40
NI|Granada|11.90|-85.95
NI|Jinotega|13.10|-85.90
NI|León|12.40|-86.90
NI|Madriz|13.50|-86.50
NI|Managua|12.15|-86.30
NI|Masaya|11.95|-86.10
NI|Matagalpa|12.90|-85.60
NI|Nueva Segovia|13.70|-86.30
NI|Río San Juan|11.20|-84.50
NI|Rivas|11.40|-85.80
CR|Alajuela|10.30|-84.50
CR|Cartago|9.85|-83.90
CR|Guanacaste|10.60|-85.50
CR|Heredia|10.10|-84.10
CR|Limón|9.90|-83.00
CR|Puntarenas|9.50|-84.50
CR|San José|9.90|-84.10
PA|Bocas del Toro|9.20|-82.20
PA|Chiriquí|8.50|-82.30
PA|Coclé|8.40|-80.50
PA|Colón|9.35|-79.90
PA|Darién|8.10|-77.90
PA|Herrera|7.95|-80.70
PA|Los Santos|7.50|-80.40
PA|Panamá Oeste|8.85|-79.80
PA|Veraguas|8.20|-81.00"""

# provincias/estados con nombre genérico o común: sólo se reconocen con "estado de / departamento de / provincia de / región de"
_ADM1_AMB = {'central', 'valle', 'bolivar', 'sucre', 'colon', 'cortes', 'la paz', 'santa cruz', 'san jose', 'guatemala', 'lima',
             'amazonas', 'cordoba', 'misiones', 'atlantida', 'meta', 'sucre', 'flores', 'florida', 'rivera', 'salto', 'colonia',
             'rio negro', 'san pedro', 'san luis', 'santa rosa', 'santa fe', 'santa ana', 'san miguel', 'la union', 'la libertad',
             'cordillera', 'concepcion', 'maldonado', 'herrera', 'granada', 'leon', 'rocha', 'soriano', 'lara', 'central',
             'acre', 'para', 'parana', 'distrito federal', 'tolima', 'huila', 'cauca'}
_ADM1_AMB -= {'parana', 'tolima', 'huila', 'cauca', 'maldonado', 'rocha', 'soriano', 'lara', 'meta', 'acre', 'para'}
_ADM1_AMB |= {'meta', 'acre', 'para', 'cauca'}

ADM1 = {}                   # nombre normalizado → [(código_país, nombre, lat, lon)]
for _ln in _ADM1_RAW.splitlines():
    _c, _n, _la, _lo = _ln.split('|')
    ADM1.setdefault(norm(_n), []).append((_c, _n, float(_la), float(_lo)))
_PREP = r"(?:en|de|del|desde|hacia|por|entre|tras|sobre|na|no|em|in|to)(?: (?:la|el|los|las|o|a))?"
_CTX = r"(?:estado|estados|departamento|departamentos|provincia|provincias|region|regiao|state|province|dept\.?)"
_ADM1_SAFE = sorted((k for k in ADM1 if k not in _ADM1_AMB), key=len, reverse=True)
_ADM1_AMBL = sorted((k for k in ADM1 if k in _ADM1_AMB), key=len, reverse=True)
_ADM1_RX = re.compile(r'\b' + _PREP + r' (' + '|'.join(map(re.escape, _ADM1_SAFE)) + r')\b')
_ADM1_CTX_RX = re.compile(r'\b' + _CTX + r' (?:de |del |do |da |of )?(' + '|'.join(map(re.escape, list(ADM1))) + r')\b')
_ADM1_AMB_RX = re.compile(r'\b(?:estado|departamento|provincia|region|regiao|state|province) (?:de |del |do |da |of )?(' + '|'.join(map(re.escape, _ADM1_AMBL)) + r')\b')

# nombre|lat|lon|país   (ciudades; las ambiguas se resuelven con el país de la fuente)
_CITIES_RAW = """Ciudad de México|19.4326|-99.1332|MX
CDMX|19.4326|-99.1332|MX
Tijuana|32.5149|-117.0382|MX
Mexicali|32.6245|-115.4523|MX
Ensenada|31.8667|-116.5964|MX
Rosarito|32.3333|-117.0500|MX
Tecate|32.5667|-116.6258|MX
Ciudad Juárez|31.6904|-106.4245|MX
Cd. Juárez|31.6904|-106.4245|MX
Chihuahua|28.6353|-106.0889|MX
Parral|26.9333|-105.6667|MX
Guadalupe y Calvo|26.1000|-106.9667|MX
Culiacán|24.8091|-107.3940|MX
Navolato|24.7667|-107.7000|MX
Mazatlán|23.2494|-106.4111|MX
Los Mochis|25.7903|-108.9858|MX
Guasave|25.5667|-108.4667|MX
Badiraguato|25.3667|-107.5167|MX
Hermosillo|29.0729|-110.9559|MX
Ciudad Obregón|27.4828|-109.9304|MX
Cajeme|27.4828|-109.9304|MX
Navojoa|27.0833|-109.4500|MX
Nogales|31.3086|-110.9422|MX
Caborca|30.7167|-112.1500|MX
San Luis Río Colorado|32.4561|-114.7719|MX
Durango|24.0277|-104.6532|MX
Gómez Palacio|25.5611|-103.4981|MX
Torreón|25.5428|-103.4068|MX
Saltillo|25.4232|-100.9921|MX
Monclova|26.9000|-101.4208|MX
Piedras Negras|28.7000|-100.5233|MX
Monterrey|25.6866|-100.3161|MX
Apodaca|25.7817|-100.1883|MX
Guadalupe Nuevo León|25.6770|-100.2560|MX
Reynosa|26.0508|-98.2979|MX
Matamoros|25.8695|-97.5027|MX
Nuevo Laredo|27.4763|-99.5164|MX
Ciudad Victoria|23.7369|-99.1411|MX
Tampico|22.2331|-97.8610|MX
Madero|22.2667|-97.8333|MX
San Fernando Tamaulipas|24.8467|-98.1550|MX
Guadalajara|20.6597|-103.3496|MX
Zapopan|20.7214|-103.3918|MX
Tlaquepaque|20.6408|-103.3126|MX
Tonalá|20.6244|-103.2339|MX
Puerto Vallarta|20.6534|-105.2253|MX
Colima|19.2433|-103.7250|MX
Manzanillo|19.1138|-104.3385|MX
Tecomán|18.9167|-103.8667|MX
Morelia|19.7060|-101.1950|MX
Uruapan|19.4167|-102.0667|MX
Apatzingán|19.0833|-102.3500|MX
Zamora|19.9833|-102.2833|MX
Zitácuaro|19.4333|-100.3500|MX
Lázaro Cárdenas|17.9583|-102.2000|MX
Acapulco|16.8531|-99.8237|MX
Chilpancingo|17.5506|-99.5058|MX
Iguala|18.3456|-99.5392|MX
Taxco|18.5567|-99.6053|MX
Zihuatanejo|17.6417|-101.5514|MX
Cuernavaca|18.9242|-99.2216|MX
Cuautla|18.8122|-98.9544|MX
Toluca|19.2826|-99.6557|MX
Ecatepec|19.6018|-99.0507|MX
Nezahualcóyotl|19.4006|-99.0148|MX
Tlalnepantla|19.5400|-99.1950|MX
Naucalpan|19.4786|-99.2397|MX
Iztapalapa|19.3574|-99.0670|MX
Puebla|19.0414|-98.2063|MX
Tehuacán|18.4667|-97.3833|MX
Tlaxcala|19.3139|-98.2404|MX
Veracruz|19.1738|-96.1342|MX
Xalapa|19.5438|-96.9102|MX
Coatzacoalcos|18.1500|-94.4167|MX
Minatitlán|17.9833|-94.5500|MX
Poza Rica|20.5333|-97.4500|MX
Córdoba Veracruz|18.8933|-96.9333|MX
Villahermosa|17.9893|-92.9475|MX
Tuxtla Gutiérrez|16.7528|-93.1152|MX
Tapachula|14.9050|-92.2631|MX
San Cristóbal de las Casas|16.7370|-92.6376|MX
Comitán|16.2500|-92.1333|MX
Frontera Comalapa|15.6667|-92.1500|MX
Oaxaca de Juárez|17.0732|-96.7266|MX
Salina Cruz|16.1667|-95.2000|MX
Cancún|21.1619|-86.8515|MX
Playa del Carmen|20.6296|-87.0739|MX
Tulum|20.2114|-87.4654|MX
Chetumal|18.5001|-88.2961|MX
Mérida Yucatán|20.9674|-89.5926|MX
Campeche|19.8301|-90.5349|MX
León Guanajuato|21.1250|-101.6860|MX
Celaya|20.5230|-100.8157|MX
Irapuato|20.6767|-101.3563|MX
Salamanca|20.5719|-101.1950|MX
Silao|20.9439|-101.4278|MX
Guanajuato capital|21.0190|-101.2574|MX
Querétaro|20.5888|-100.3899|MX
San Luis Potosí capital|22.1565|-100.9855|MX
Zacatecas capital|22.7709|-102.5832|MX
Fresnillo|23.1750|-102.8667|MX
Aguascalientes capital|21.8853|-102.2916|MX
Pachuca|20.1011|-98.7591|MX
Tepic|21.5042|-104.8946|MX
La Paz Baja California Sur|24.1426|-110.3128|MX
Los Cabos|22.8905|-109.9167|MX
Cabo San Lucas|22.8905|-109.9167|MX
Bogotá|4.7110|-74.0721|CO
Medellín|6.2442|-75.5812|CO
Cali|3.4516|-76.5320|CO
Barranquilla|10.9685|-74.7813|CO
Cartagena de Indias|10.3910|-75.4794|CO
Cartagena|10.3910|-75.4794|CO
Cúcuta|7.8939|-72.5078|CO
Bucaramanga|7.1254|-73.1198|CO
Buenaventura|3.8801|-77.0312|CO
Tumaco|1.7986|-78.8156|CO
Santa Marta|11.2408|-74.1990|CO
Pereira|4.8133|-75.6961|CO
Manizales|5.0703|-75.5138|CO
Ibagué|4.4389|-75.2322|CO
Villavicencio|4.1420|-73.6266|CO
Pasto|1.2136|-77.2811|CO
Popayán|2.4382|-76.6132|CO
Neiva|2.9273|-75.2819|CO
Montería|8.7479|-75.8814|CO
Quibdó|5.6947|-76.6611|CO
Riohacha|11.5444|-72.9072|CO
Valledupar|10.4631|-73.2532|CO
Sincelejo|9.3047|-75.3978|CO
Apartadó|7.8833|-76.6250|CO
Caucasia|7.9833|-75.1944|CO
Tibú|8.6361|-72.7358|CO
Ocaña|8.2372|-73.3578|CO
Florencia Caquetá|1.6144|-75.6062|CO
Mocoa|1.1478|-76.6472|CO
Yopal|5.3378|-72.3959|CO
Armenia Quindío|4.5339|-75.6811|CO
Soacha|4.5794|-74.2168|CO
Bello|6.3373|-75.5579|CO
Envigado|6.1759|-75.5917|CO
Jamundí|3.2606|-76.5400|CO
Barrancabermeja|7.0653|-73.8547|CO
Turbo|8.0933|-76.7285|CO
El Bagre|7.5953|-74.8000|CO
Puerto Asís|0.5000|-76.5000|CO
San José del Guaviare|2.5667|-72.6400|CO
Leticia|-4.2153|-69.9406|CO
Catatumbo|8.5000|-73.0000|CO
Río de Janeiro|-22.9068|-43.1729|BR
Rio de Janeiro cidade|-22.9068|-43.1729|BR
São Paulo capital|-23.5505|-46.6333|BR
Brasília|-15.7939|-47.8828|BR
Salvador de Bahía|-12.9777|-38.5016|BR
Salvador Bahia|-12.9777|-38.5016|BR
Fortaleza|-3.7319|-38.5267|BR
Recife|-8.0476|-34.8770|BR
Belo Horizonte|-19.9167|-43.9345|BR
Manaus|-3.1190|-60.0217|BR
Belém|-1.4558|-48.5044|BR
Porto Alegre|-30.0346|-51.2177|BR
Curitiba|-25.4284|-49.2733|BR
Goiânia|-16.6869|-49.2648|BR
Natal Rio Grande do Norte|-5.7945|-35.2110|BR
São Luís|-2.5307|-44.3068|BR
Maceió|-9.6658|-35.7353|BR
João Pessoa|-7.1195|-34.8450|BR
Teresina|-5.0892|-42.8019|BR
Campo Grande|-20.4697|-54.6201|BR
Cuiabá|-15.6014|-56.0979|BR
Florianópolis|-27.5954|-48.5480|BR
Vitória Espírito Santo|-20.3155|-40.3128|BR
Aracaju|-10.9472|-37.0731|BR
Porto Velho|-8.7612|-63.9039|BR
Macapá|0.0349|-51.0694|BR
Boa Vista|2.8235|-60.6758|BR
Santos|-23.9608|-46.3336|BR
Campinas|-22.9099|-47.0626|BR
Guarulhos|-23.4543|-46.5333|BR
Duque de Caxias|-22.7856|-43.3117|BR
Niterói|-22.8833|-43.1036|BR
São Gonçalo|-22.8269|-43.0539|BR
Ribeirão Preto|-21.1775|-47.8103|BR
Foz do Iguaçu|-25.5163|-54.5854|BR
Ponta Porã|-22.5361|-55.7258|BR
Corumbá|-19.0078|-57.6511|BR
Tabatinga|-4.2500|-69.9400|BR
Buenos Aires ciudad|-34.6037|-58.3816|AR
CABA|-34.6037|-58.3816|AR
Rosario|-32.9442|-60.6505|AR
Córdoba capital|-31.4201|-64.1888|AR
Mendoza capital|-32.8895|-68.8458|AR
La Plata|-34.9205|-57.9536|AR
Mar del Plata|-38.0055|-57.5426|AR
San Miguel de Tucumán|-26.8083|-65.2176|AR
Salta capital|-24.7821|-65.4232|AR
Santa Fe capital|-31.6333|-60.7000|AR
Neuquén capital|-38.9516|-68.0591|AR
Bahía Blanca|-38.7196|-62.2724|AR
Resistencia|-27.4606|-58.9839|AR
Posadas|-27.3671|-55.8961|AR
Quilmes|-34.7203|-58.2694|AR
La Matanza|-34.7700|-58.6300|AR
Lomas de Zamora|-34.7600|-58.4000|AR
Comodoro Rivadavia|-45.8641|-67.4966|AR
Ushuaia|-54.8019|-68.3030|AR
Bariloche|-41.1335|-71.3103|AR
Santiago de Chile|-33.4489|-70.6693|CL
Santiago capital|-33.4489|-70.6693|CL
Valparaíso ciudad|-33.0472|-71.6127|CL
Viña del Mar|-33.0153|-71.5500|CL
Concepción Chile|-36.8201|-73.0444|CL
Antofagasta ciudad|-23.6509|-70.3975|CL
Iquique|-20.2133|-70.1503|CL
Arica|-18.4783|-70.3126|CL
Temuco|-38.7359|-72.5904|CL
Rancagua|-34.1708|-70.7444|CL
La Serena|-29.9027|-71.2520|CL
Puerto Montt|-41.4693|-72.9424|CL
Punta Arenas|-53.1638|-70.9171|CL
Calama|-22.4667|-68.9333|CL
Copiapó|-27.3668|-70.3323|CL
Puente Alto|-33.6117|-70.5758|CL
Maipú|-33.5100|-70.7600|CL
San Antonio Chile|-33.5933|-71.6122|CL
Lima ciudad|-12.0464|-77.0428|PE
Callao ciudad|-12.0566|-77.1181|PE
Arequipa ciudad|-16.4090|-71.5375|PE
Trujillo|-8.1116|-79.0288|PE
Chiclayo|-6.7714|-79.8409|PE
Piura ciudad|-5.1945|-80.6328|PE
Iquitos|-3.7437|-73.2516|PE
Cusco ciudad|-13.5319|-71.9675|PE
Huancayo|-12.0651|-75.2049|PE
Pucallpa|-8.3791|-74.5539|PE
Tacna ciudad|-18.0146|-70.2536|PE
Chimbote|-9.0853|-78.5783|PE
Tumbes ciudad|-3.5669|-80.4515|PE
Sullana|-4.9039|-80.6853|PE
Tarapoto|-6.4883|-76.3597|PE
Juliaca|-15.5000|-70.1333|PE
VRAEM|-12.5000|-73.7000|PE
Guayaquil|-2.1710|-79.9224|EC
Quito|-0.1807|-78.4678|EC
Cuenca Ecuador|-2.9001|-79.0059|EC
Machala|-3.2581|-79.9554|EC
Manta|-0.9677|-80.7089|EC
Esmeraldas ciudad|0.9592|-79.6542|EC
Portoviejo|-1.0546|-80.4545|EC
Ambato|-1.2417|-78.6197|EC
Loja ciudad|-3.9931|-79.2042|EC
Santo Domingo de los Colorados|-0.2530|-79.1754|EC
Babahoyo|-1.8022|-79.5344|EC
Quevedo|-1.0225|-79.4604|EC
Durán|-2.1700|-79.8333|EC
Milagro|-2.1342|-79.5942|EC
Ibarra|0.3517|-78.1223|EC
Riobamba|-1.6636|-78.6546|EC
Latacunga|-0.9352|-78.6155|EC
Lago Agrio|0.0847|-76.8950|EC
Puerto Bolívar|-3.2667|-79.9833|EC
Tulcán|0.8119|-77.7172|EC
Caracas|10.4806|-66.9036|VE
Maracaibo|10.6427|-71.6125|VE
Valencia Venezuela|10.1620|-68.0077|VE
Barquisimeto|10.0647|-69.3570|VE
Maracay|10.2469|-67.5958|VE
Ciudad Guayana|8.3596|-62.6412|VE
Puerto Ordaz|8.2967|-62.7236|VE
Barcelona Venezuela|10.1333|-64.7000|VE
Maturín|9.7457|-63.1832|VE
Cumaná|10.4536|-64.1675|VE
San Cristóbal Venezuela|7.7669|-72.2250|VE
Ciudad Bolívar|8.1222|-63.5497|VE
Puerto Cabello|10.4731|-68.0125|VE
Los Teques|10.3447|-67.0433|VE
Guarenas|10.4667|-66.6167|VE
Puerto Ayacucho|5.6639|-67.6236|VE
La Paz ciudad|-16.4897|-68.1193|BO
Santa Cruz de la Sierra|-17.7833|-63.1821|BO
Cochabamba ciudad|-17.3895|-66.1568|BO
El Alto|-16.5000|-68.1500|BO
Sucre capital|-19.0196|-65.2619|BO
Oruro ciudad|-17.9647|-67.1060|BO
Potosí ciudad|-19.5836|-65.7531|BO
Tarija ciudad|-21.5355|-64.7296|BO
Trinidad Beni|-14.8333|-64.9000|BO
Cobija|-11.0267|-68.7692|BO
Yacuiba|-22.0167|-63.6833|BO
Villazón|-22.0833|-65.5964|BO
Chapare|-16.9500|-65.4000|BO
Asunción|-25.2637|-57.5759|PY
Ciudad del Este|-25.5167|-54.6167|PY
Pedro Juan Caballero|-22.5472|-55.7333|PY
Encarnación|-27.3306|-55.8667|PY
Salto del Guairá|-24.0500|-54.3000|PY
Luque|-25.2667|-57.4833|PY
San Lorenzo Paraguay|-25.3400|-57.5100|PY
Pilar Paraguay|-26.8667|-58.3000|PY
Montevideo ciudad|-34.9011|-56.1645|UY
Punta del Este|-34.9500|-54.9500|UY
Paysandú ciudad|-32.3214|-58.0756|UY
Ciudad de Guatemala|14.6349|-90.5069|GT
Mixco|14.6333|-90.6061|GT
Villa Nueva|14.5269|-90.5875|GT
Puerto Barrios|15.7278|-88.5944|GT
Puerto San José|13.9167|-90.8167|GT
Huehuetenango ciudad|15.3197|-91.4744|GT
San Pedro Sula|15.5000|-88.0333|HN
Tegucigalpa|14.0723|-87.1921|HN
La Ceiba|15.7833|-86.7833|HN
Choloma|15.6144|-87.9525|HN
Tela|15.7833|-87.4500|HN
Puerto Cortés|15.8333|-87.9500|HN
El Progreso Honduras|15.4000|-87.8000|HN
San Salvador ciudad|13.6929|-89.2182|SV
Soyapango|13.7100|-89.1400|SV
Santa Ana ciudad|13.9942|-89.5597|SV
San Miguel ciudad|13.4833|-88.1833|SV
Apopa|13.8000|-89.1800|SV
Managua ciudad|12.1364|-86.2514|NI
Bluefields|12.0133|-83.7633|NI
Matagalpa ciudad|12.9167|-85.9167|NI
San José Costa Rica|9.9281|-84.0907|CR
Limón Costa Rica|9.9907|-83.0360|CR
Puntarenas ciudad|9.9763|-84.8384|CR
Ciudad de Panamá|8.9824|-79.5199|PA
Panamá ciudad|8.9824|-79.5199|PA
Colón Panamá|9.3592|-79.9014|PA
David Chiriquí|8.4273|-82.4308|PA
Santo Domingo República Dominicana|18.4861|-69.9312|DO
Santiago de los Caballeros|19.4517|-70.6970|DO
Punta Cana|18.5820|-68.4055|DO
San Pedro de Macorís|18.4539|-69.3086|DO
Puerto Príncipe|18.5944|-72.3074|HT
Port-au-Prince|18.5944|-72.3074|HT
Cap-Haïtien|19.7578|-72.2042|HT
La Habana|23.1136|-82.3666|CU
Kingston Jamaica|17.9712|-76.7928|JM
Puerto España|10.6549|-61.5019|TT
San Juan Puerto Rico|18.4655|-66.1057|PR
Georgetown Guyana|6.8013|-58.1551|GY
Paramaribo|5.8520|-55.2038|SR
Ciudad de Belice|17.4995|-88.1976|BZ"""

# ciudades con nombre ambiguo: se aceptan solo si el país de la fuente coincide (o con "ciudad de X")
_CIUDAD_ALIAS = {'cartagena': 'CO', 'guadalajara': 'MX', 'nogales': 'MX', 'cali': 'CO', 'santos': 'BR', 'madero': 'MX', 'zamora': 'MX',
                 'campeche': 'MX', 'durango': 'MX', 'puebla': 'MX', 'colima': 'MX', 'veracruz': 'MX', 'queretaro': 'MX', 'chihuahua': 'MX',
                 'tlaxcala': 'MX', 'oaxaca': 'MX', 'cuernavaca': 'MX', 'monterrey': 'MX', 'tijuana': 'MX', 'toluca': 'MX'}
_CITY_AMB = {'cartagena', 'guadalajara', 'cali', 'santos', 'madero', 'zamora', 'salamanca', 'granada', 'leon', 'cordoba', 'valencia',
             'merida', 'santiago', 'trinidad', 'armenia', 'salvador', 'natal', 'vitoria', 'tulum', 'iguala', 'celaya', 'toluca',
             'mazatlan', 'apodaca', 'tecate', 'rosarito', 'maipu', 'durán', 'duran', 'tacna', 'arica', 'bello', 'envigado', 'sullana',
             'resistencia', 'posadas', 'cobija', 'luque', 'pilar', 'apopa', 'david', 'tela', 'colon', 'limon', 'matagalpa', 'managua'}
_CITY_AMB -= {'mazatlan', 'apodaca', 'tecate', 'rosarito', 'maipu', 'duran', 'tacna', 'arica', 'bello', 'envigado', 'sullana',
              'resistencia', 'posadas', 'cobija', 'luque', 'apopa', 'tela', 'matagalpa', 'managua', 'toluca', 'celaya', 'iguala', 'tulum'}

# alias de búsqueda → nombre normalizado de la ciudad (para variantes sin sufijo de aclaración)
_SUFIJOS = (' ciudad', ' capital', ' cidade', ' mexico', ' venezuela', ' chile', ' ecuador', ' beni', ' guyana', ' jamaica',
            ' puerto rico', ' costa rica', ' panama', ' chiriqui', ' paraguay', ' honduras', ' veracruz', ' yucatan', ' quindio',
            ' caqueta', ' guanajuato', ' nuevo leon', ' tamaulipas', ' baja california sur', ' rio grande do norte', ' espirito santo',
            ' bahia', ' republica dominicana')
CITIES = {}                 # clave normalizada → [(nombre, lat, lon, país)]
LUGARES = []                # (nombre, lat, lon, país) para etiquetar hotspots
for _ln in _CITIES_RAW.splitlines():
    _n, _la, _lo, _c = _ln.split('|')
    _full = norm(_n)
    _keys = {_full}
    for _s in _SUFIJOS:
        if _full.endswith(_s) and len(_full) > len(_s) + 3:
            _keys.add(_full[:-len(_s)])
    _short = _n
    for _s in _SUFIJOS:
        if norm(_n).endswith(_s) and len(_n) > len(_s) + 3:
            _short = _n[:len(_n) - len(_s)]
    for _k in _keys:
        CITIES.setdefault(_k, []).append((_short, float(_la), float(_lo), _c))
    LUGARES.append((_short, float(_la), float(_lo), _c))
for _k, (_n, _la, _lo, _c) in ((norm(a[1]), (a[1], a[2], a[3], a[0])) for v in ADM1.values() for a in v):
    LUGARES.append((_n, _la, _lo, _c))
# abreviaturas/gentilicios de uso común
for _k, _t in (('cd juarez', 'ciudad juarez'), ('cdmx', 'ciudad de mexico'), ('d f', 'ciudad de mexico')):
    if _t in CITIES:
        CITIES.setdefault(_k, CITIES[_t])
_CITY_SAFE = sorted((k for k in CITIES if k not in _CITY_AMB and len(k) >= 4), key=len, reverse=True)
_CITY_AMBL = sorted((k for k in CITIES if k in _CITY_AMB), key=len, reverse=True)
_CITY_RX_SAFE = re.compile(r'\b(' + '|'.join(map(re.escape, _CITY_SAFE)) + r')\b')
_CITY_AMB_RX = re.compile(r'\b(?:en|de|del|desde|hacia|por|na|no|em|in)(?: (?:la|el|los|las|o|a))? (' + '|'.join(map(re.escape, _CITY_AMBL)) + r')\b')
_CODE_RX = re.compile(r'(?!x)x')                  # sin códigos numéricos en Latam


def dep_code_fuente(fuente):
    d = fuente.get('departement', '')
    if d in ('Regional', 'Internacional', '', None):
        return None
    return DEP_BY_NAME.get(norm(d))


def _jitter(seed, amp):
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    return (((h & 0xffff) / 65535) - .5) * 2 * amp, ((((h >> 16) & 0xffff) / 65535) - .5) * 2 * amp


def _clamp(code, la, lo):
    a, b, d, e = _BBOX[code]
    return round(min(max(la, a), b), 5), round(min(max(lo, d), e), 5)


def _elige(cands, pref):
    """Varias ciudades/estados con el mismo nombre: gana el del país preferido (texto o fuente); si no, el primero."""
    for c in cands:
        if c[-4 if len(c) == 4 and isinstance(c[0], str) and len(c[0]) == 2 else -1] == pref:
            return c
    return cands[0]


def geolocalizar(texto, code_fuente=None, seed=''):
    """Devuelve dict(lat, lon, departement[=país], dep_code[=ISO2], precision, lugar).  Ciudad > estado > país > país de la fuente."""
    n = norm(texto)
    mp = _PAIS_RX.search(n)
    pref = code_fuente or (_PAIS_TXT.get(mp.group(1)) if mp else None)
    if mp and not code_fuente:
        pref = _PAIS_TXT[mp.group(1)]
    elif mp and code_fuente and _PAIS_TXT[mp.group(1)] != code_fuente:
        pref = _PAIS_TXT[mp.group(1)]                         # el texto menciona otro país: manda el texto
    # 1) ciudad
    m = _CITY_RX_SAFE.search(n) or _CITY_AMB_RX.search(n)
    if m:
        cands = CITIES[m.group(1)]
        if len(cands) == 1 or any(c[3] == pref for c in cands) or not pref or m.group(1) not in _CITY_AMB:
            sel = next((c for c in cands if c[3] == pref), cands[0])
            if not (m.group(1) in _CITY_AMB and pref and sel[3] != pref):
                nombre, la, lo, code = sel
                dx, dy = _jitter(seed or n, 0.03)
                la, lo = _clamp(code, la + dx, lo + dy)
                return {'lat': la, 'lon': lo, 'departement': PAISES[code][0], 'dep_code': code, 'precision': 'ciudad', 'lugar': nombre}
    # 2) estado / departamento / provincia
    ma = _ADM1_CTX_RX.search(n) or _ADM1_AMB_RX.search(n) or _ADM1_RX.search(n)
    if ma:
        cands = ADM1[ma.group(1)]
        sel = next((c for c in cands if c[0] == pref), cands[0])
        if len(cands) == 1 or sel[0] == pref or not pref:
            code, nombre, la, lo = sel
            dx, dy = _jitter(seed or n, 0.25)
            la, lo = _clamp(code, la + dx, lo + dy)
            return {'lat': la, 'lon': lo, 'departement': PAISES[code][0], 'dep_code': code, 'precision': 'depto', 'lugar': nombre}
    # 3) país nombrado en el texto / país de la fuente
    code = (_PAIS_TXT.get(mp.group(1)) if mp else None) or code_fuente
    prec = 'depto' if (mp and code == _PAIS_TXT.get(mp.group(1))) else 'fuente'
    if code:
        nombre, la, lo = PAISES[code]
        r = _JR[code]
        dx, dy = _jitter(seed or n, r)
        la, lo = _clamp(code, la + dx, lo + dy)
        return {'lat': la, 'lon': lo, 'departement': nombre, 'dep_code': code, 'precision': 'pais' if prec else prec, 'lugar': ''}
    return {'lat': None, 'lon': None, 'departement': 'Regional', 'dep_code': None, 'precision': 'none', 'lugar': ''}


# ============================================================================
# FUENTES  (v1: 45 médias faits-divers · + cyber · + alertes officielles)
# ============================================================================


# ============================================================================
# FUENTES  (original v7: 61 medios · + análisis/finanzas · + fuentes oficiales)   (nombre, url, país)
# ============================================================================

_FUENTES_RAW = [
    # ARGENTINA
    ('Infobae Policiales', 'https://www.infobae.com/sociedad/policiales/', 'Argentina'),
    ('La Nación Seguridad', 'https://www.lanacion.com.ar/seguridad/', 'Argentina'),
    ('Clarín Policiales', 'https://www.clarin.com/policiales/', 'Argentina'),
    ('Crónica Policiales', 'https://www.cronica.com.ar/policiales/', 'Argentina'),
    ('TN Policiales', 'https://tn.com.ar/policiales/', 'Argentina'),
    ('Río Negro Policiales', 'https://www.rionegro.com.ar/policiales/', 'Argentina'),
    ('El Territorio Policiales', 'https://www.elterritorio.com.ar/policiales', 'Argentina'),
    ('Rosario3 Policiales', 'https://www.rosario3.com/policiales/', 'Argentina'),
    ('La Capital Rosario Policiales', 'https://www.lacapital.com.ar/policiales', 'Argentina'),
    ('Perfil Policiales', 'https://www.perfil.com/seccion/policiales', 'Argentina'),
    ('La Voz Sucesos', 'https://www.lavoz.com.ar/sucesos/', 'Argentina'),
    ('Los Andes Policiales', 'https://www.losandes.com.ar/policiales/', 'Argentina'),
    # COLOMBIA
    ('El Tiempo Justicia', 'https://www.eltiempo.com/justicia', 'Colombia'),
    ('El Colombiano Judicial', 'https://www.elcolombiano.com/judicial', 'Colombia'),
    ('El Espectador Judicial', 'https://www.elespectador.com/judicial/', 'Colombia'),
    ('Semana Justicia', 'https://www.semana.com/justicia/', 'Colombia'),
    ('El Heraldo Judicial', 'https://www.elheraldo.co/judicial', 'Colombia'),
    ('Vanguardia Judicial', 'https://www.vanguardia.com/judicial', 'Colombia'),
    ('El País Cali Judicial', 'https://www.elpais.com.co/judicial', 'Colombia'),
    ('Verdad Abierta', 'https://verdadabierta.com/', 'Colombia'),
    ('Infobae Colombia', 'https://www.infobae.com/colombia/', 'Colombia'),
    # MÉXICO
    ('Milenio Policía', 'https://www.milenio.com/policia', 'México'),
    ('El Universal Seguridad', 'https://www.eluniversal.com.mx/nacion/seguridad/', 'México'),
    ('Reforma Seguridad', 'https://www.reforma.com/', 'México'),
    ('Excélsior Seguridad', 'https://www.excelsior.com.mx/seguridad', 'México'),
    ('La Jornada Policía', 'https://www.jornada.com.mx/categoria/policia', 'México'),
    ('Proceso Narcotráfico', 'https://www.proceso.com.mx/etiquetas/narcotrafico', 'México'),
    ('Animal Político Seguridad', 'https://www.animalpolitico.com/categoria/seguridad/', 'México'),
    ('Infobae México Policiales', 'https://www.infobae.com/mexico/policiales/', 'México'),
    ('Ríodoce (Sinaloa)', 'https://riodoce.mx/', 'México'),
    ('Zeta Tijuana', 'https://zetatijuana.com/', 'México'),
    ('Noroeste (Sinaloa)', 'https://www.noroeste.com.mx/policiaca', 'México'),
    ('Sin Embargo', 'https://www.sinembargo.mx/', 'México'),
    ('Aristegui Noticias', 'https://aristeguinoticias.com/', 'México'),
    ('El Debate (Culiacán)', 'https://www.debate.com.mx/policiacas/', 'México'),
    ('Quadratín Michoacán', 'https://www.quadratin.com.mx/', 'México'),
    ('El Heraldo de México Justicia', 'https://heraldodemexico.com.mx/nacional/', 'México'),
    # CHILE
    ('Emol Nacional', 'https://www.emol.com/nacional/', 'Chile'),
    ('Meganoticias Policial', 'https://www.meganoticias.cl/policial/', 'Chile'),
    ('La Tercera Crónica', 'https://www.latercera.com/categoria/cronica/', 'Chile'),
    ('BioBioChile Policial', 'https://www.biobiochile.cl/noticias/category/nacional/policial', 'Chile'),
    ('Chilevisión Casos Policiales', 'https://www.chilevision.cl/noticias/casos-policiales/', 'Chile'),
    ('T13 Policial', 'https://www.t13.cl/policial', 'Chile'),
    ('24horas Policial', 'https://www.24horas.cl/actualidad/policial', 'Chile'),
    ('Cooperativa Policial', 'https://www.cooperativa.cl/noticias/pais/policial/', 'Chile'),
    # PERÚ
    ('El Comercio Sucesos', 'https://elcomercio.pe/lima/sucesos/', 'Perú'),
    ('La República Sucesos', 'https://larepublica.pe/sucesos/', 'Perú'),
    ('Perú 21 Sucesos', 'https://peru21.pe/sucesos/', 'Perú'),
    ('Correo Policiales', 'https://diariocorreo.pe/policiales/', 'Perú'),
    ('Ojo Policial', 'https://ojo.pe/policial/', 'Perú'),
    ('RPP Policiales', 'https://rpp.pe/lima/policiales/', 'Perú'),
    ('Infobae Perú', 'https://www.infobae.com/peru/', 'Perú'),
    ('Exitosa Policiales', 'https://exitosanoticias.pe/policiales', 'Perú'),
    # ECUADOR
    ('El Universo Seguridad', 'https://www.eluniverso.com/noticias/seguridad/', 'Ecuador'),
    ('Diario Extra Judiciales', 'https://www.extra.ec/temas/judiciales/', 'Ecuador'),
    ('Crónica Policial', 'https://cronica.com.ec/category/policial/', 'Ecuador'),
    ('El Comercio Ecuador Seguridad', 'https://www.elcomercio.com/', 'Ecuador'),
    ('Metro Ecuador Judicial', 'https://www.metroecuador.com.ec/tags/judicial/', 'Ecuador'),
    ('Primicias Seguridad', 'https://www.primicias.ec/seguridad/', 'Ecuador'),
    ('Expreso Seguridad', 'https://www.expreso.ec/actualidad/seguridad', 'Ecuador'),
    ('Ecuavisa Seguridad', 'https://www.ecuavisa.com/noticias/seguridad', 'Ecuador'),
    # VENEZUELA
    ('El Nacional Sucesos', 'https://www.elnacional.com/categoria/sucesos/', 'Venezuela'),
    ('El Universal Sucesos', 'https://www.eluniversal.com/sucesos/', 'Venezuela'),
    ('Últimas Noticias Sucesos', 'https://ultimasnoticias.com.ve/', 'Venezuela'),
    ('La Calle Sucesos', 'https://lacalle.com.ve/category/sucesos', 'Venezuela'),
    ('Noticia al Minuto Sucesos', 'https://noticiaalminuto.com/', 'Venezuela'),
    ('Diario Versión Final Sucesos', 'https://diarioversionfinal.com/categoria/sucesos/', 'Venezuela'),
    ('El Pitazo Sucesos', 'https://elpitazo.net/sucesos/', 'Venezuela'),
    # BRASIL
    ('O Globo Polícia', 'https://oglobo.globo.com/rio-de-janeiro/policia/', 'Brasil'),
    ('Folha Cotidiano', 'https://www1.folha.uol.com.br/cotidiano/', 'Brasil'),
    ('Estadão Polícia', 'https://www.estadao.com.br/', 'Brasil'),
    ('UOL Segurança', 'https://noticias.uol.com.br/', 'Brasil'),
    ('g1 Rio de Janeiro', 'https://g1.globo.com/rj/rio-de-janeiro/', 'Brasil'),
    ('g1 São Paulo', 'https://g1.globo.com/sp/sao-paulo/', 'Brasil'),
    ('g1 Brasil', 'https://g1.globo.com/brasil/', 'Brasil'),
    ('Metrópoles Brasil', 'https://www.metropoles.com/brasil', 'Brasil'),
    ('CNN Brasil Segurança', 'https://www.cnnbrasil.com.br/nacional/', 'Brasil'),
    ('Correio Braziliense Brasil', 'https://www.correiobraziliense.com.br/brasil/', 'Brasil'),
    # BOLIVIA, PARAGUAY, URUGUAY
    ('El Deber Policial', 'https://eldeber.com.bo/policial', 'Bolivia'),
    ('Los Tiempos Seguridad', 'https://www.lostiempos.com/actualidad/seguridad', 'Bolivia'),
    ('ABC Color Policiales', 'https://www.abc.com.py/policiales', 'Paraguay'),
    ('Última Hora Policiales', 'https://www.ultimahora.com/policiales', 'Paraguay'),
    ('La Nación PY Policiales', 'https://www.lanacion.com.py/policiales/', 'Paraguay'),
    ('Montevideo Portal Policiales', 'https://www.montevideo.com.uy/policiales', 'Uruguay'),
    ('El País Uruguay Policiales', 'https://www.elpais.com.uy/informacion/policiales', 'Uruguay'),
    # CENTROAMÉRICA Y CARIBE
    ('La Prensa Gráfica Judicial', 'https://www.laprensagrafica.com/judicial/', 'El Salvador'),
    ('El Mundo El Salvador', 'https://diario.elmundo.sv/', 'El Salvador'),
    ('El Faro', 'https://elfaro.net/', 'El Salvador'),
    ('La Tribuna Sucesos', 'https://www.latribuna.hn/', 'Honduras'),
    ('El Heraldo Sucesos', 'https://www.elheraldo.hn/sucesos', 'Honduras'),
    ('La Prensa Honduras Sucesos', 'https://www.laprensa.hn/sucesos/', 'Honduras'),
    ('La Hora Guatemala', 'https://lahora.gt/', 'Guatemala'),
    ('Prensa Libre Guatemala', 'https://www.prensalibre.com/guatemala/sucesos/', 'Guatemala'),
    ('Soy502 Nacionales', 'https://www.soy502.com/', 'Guatemala'),
    ('La Prensa Panamá Judiciales', 'https://www.prensa.com/judiciales/', 'Panamá'),
    ('La Estrella de Panamá Sucesos', 'https://www.laestrella.com.pa/nacional/sucesos', 'Panamá'),
    ('CRHoy Sucesos', 'https://www.crhoy.com/nacionales/sucesos/', 'Costa Rica'),
    ('La Nación Costa Rica Sucesos', 'https://www.nacion.com/sucesos/', 'Costa Rica'),
    ('Listín Diario Sucesos', 'https://listindiario.com/la-republica/sucesos', 'República Dominicana'),
    ('Diario Libre Justicia', 'https://www.diariolibre.com/actualidad/justicia', 'República Dominicana'),
    ('Confidencial Nicaragua', 'https://confidencial.digital/', 'Nicaragua'),
    # REGIONALES Y ANÁLISIS
    ('Insight Crime', 'https://insightcrime.org/', 'Regional'),
    ('BBC Mundo', 'https://www.bbc.com/mundo', 'Regional'),
    ('DW Español Latinoamérica', 'https://www.dw.com/es/latinoamérica/s-30588', 'Regional'),
    ('El País América', 'https://elpais.com/america/', 'Regional'),
    ('CNN en Español', 'https://cnnespanol.cnn.com/', 'Regional'),
    ('France 24 Español', 'https://www.france24.com/es/', 'Regional'),
]

# análisis / finanzas ilícitas / medio ambiente criminal: (nombre, url, país, rss|None)
_FUENTES_CYBER_RAW = [
    ('Insight Crime - Investigaciones', 'https://insightcrime.org/investigations/', 'Regional', 'https://insightcrime.org/feed/'),
    ('Mongabay Latam - Crimen ambiental', 'https://es.mongabay.com/', 'Regional', 'https://es.mongabay.com/feed/'),
    ('Connectas', 'https://www.connectas.org/', 'Regional', None),
    ('Crisis Group - América Latina', 'https://www.crisisgroup.org/latin-america-caribbean', 'Regional', None),
    ('Infodefensa / Seguridad regional', 'https://www.infodefensa.com/', 'Regional', None),
    ('Latinus Investigaciones', 'https://latinus.us/', 'México', None),
    ('Mexicanos Contra la Corrupción', 'https://contralacorrupcion.mx/', 'México', None),
    ('CIPER Chile', 'https://www.ciperchile.cl/', 'Chile', None),
    ('Ojo Público', 'https://ojo-publico.com/', 'Perú', None),
    ('Agência Pública', 'https://apublica.org/', 'Brasil', None),
]

# alertas oficiales: (nombre, url, país, ctx, rss|None, filtro|None)
#  ctx 'crime' → seguridad / justicia / alertas de viaje · ctx 'cyber' → finanzas ilícitas (OFAC, UIF, GAFILAT…)
_FUENTES_GOV_RAW = [
    ('EE.UU. Depto. de Estado - Alertas de viaje', 'https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html', 'Regional', 'crime',
     'https://travel.state.gov/_res/rss/TAsTWs.xml', r"mexico|colombia|brazil|venezuela|ecuador|honduras|guatemala|el salvador|haiti|peru|bolivia|paraguay|argentina|chile|panama|nicaragua|costa rica|dominican|cuba|jamaica|trinidad|belize|guyana|suriname|uruguay"),
    ('DEA - Comunicados', 'https://www.dea.gov/press-releases', 'Regional', 'crime', None,
     r"cartel|cocaine|fentanyl|methamphetamine|mexico|colombia|venezuela|ecuador|peru|brazil|sinaloa|jalisco|tren de aragua|trafficking|drug"),
    ('UNODC - Noticias', 'https://www.unodc.org/unodc/es/press/releases.html', 'Regional', 'crime', None,
     r"america latina|cocaina|narcotrafico|crimen organizado|drogas|colombia|mexico|ecuador|peru|bolivia|brasil|latin america|cocaine|trafficking"),
    ('OEA - CICAD', 'https://www.oas.org/es/sms/cicad/', 'Regional', 'crime', None, None),
    ('México - SSPC (Seguridad)', 'https://www.gob.mx/sspc/prensa', 'México', 'crime', None, None),
    ('México - FGR Comunicados', 'https://www.gob.mx/fgr/prensa', 'México', 'crime', None, None),
    ('México - Defensa (SEDENA)', 'https://www.gob.mx/defensa/prensa', 'México', 'crime', None, None),
    ('México - Guardia Nacional', 'https://www.gob.mx/guardianacional/prensa', 'México', 'crime', None, None),
    ('Colombia - Policía Nacional', 'https://www.policia.gov.co/noticias', 'Colombia', 'crime', None, None),
    ('Colombia - Fiscalía General', 'https://www.fiscalia.gov.co/colombia/noticias/', 'Colombia', 'crime', None, None),
    ('Colombia - Ministerio de Defensa', 'https://www.mindefensa.gov.co/', 'Colombia', 'crime', None,
     r"narco|cartel|clan del golfo|eln|farc|disidencia|secuestro|extorsion|masacre|ataque|terror|erradicacion|cocaina"),
    ('Argentina - Ministerio de Seguridad', 'https://www.argentina.gob.ar/seguridad/noticias', 'Argentina', 'crime', None, None),
    ('Brasil - Polícia Federal', 'https://www.gov.br/pf/pt-br/assuntos/noticias', 'Brasil', 'crime', None, None),
    ('Brasil - Ministério da Justiça', 'https://www.gov.br/mj/pt-br/assuntos/noticias', 'Brasil', 'crime', None,
     r"trafico|facc|crime organizado|drogas|lavagem|operacao|seguranca|pcc|comando vermelho"),
    ('Perú - Mininter', 'https://www.gob.pe/institucion/mininter/noticias', 'Perú', 'crime', None, None),
    ('Perú - DEVIDA', 'https://www.gob.pe/institucion/devida/noticias', 'Perú', 'crime', None, None),
    ('Ecuador - Ministerio del Interior', 'https://www.ministeriodelinterior.gob.ec/noticias/', 'Ecuador', 'crime', None, None),
    ('Chile - Fiscalía', 'https://www.fiscaliadechile.cl/Fiscalia/sala_prensa/index.jsp', 'Chile', 'crime', None, None),
    ('Chile - PDI', 'https://www.pdichile.cl/centro-de-prensa/noticias', 'Chile', 'crime', None, None),
    ('Guatemala - Policía Nacional Civil', 'https://www.pnc.gob.gt/', 'Guatemala', 'crime', None, None),
    ('Guatemala - Ministerio Público', 'https://www.mp.gob.gt/noticias/', 'Guatemala', 'crime', None, None),
    ('El Salvador - PNC', 'https://www.pnc.gob.sv/', 'El Salvador', 'crime', None, None),
    ('Paraguay - SENAD', 'https://www.senad.gov.py/', 'Paraguay', 'crime', None, None),
    ('Panamá - Ministerio de Seguridad', 'https://www.minseg.gob.pa/', 'Panamá', 'crime', None, None),
    ('Costa Rica - OIJ', 'https://sitiooij.poder-judicial.go.cr/', 'Costa Rica', 'crime', None, None),
    ('Rep. Dominicana - DNCD', 'https://dncd.gob.do/', 'República Dominicana', 'crime', None, None),
    ('OFAC - Sanciones (Tesoro EE.UU.)', 'https://ofac.treasury.gov/recent-actions', 'Regional', 'cyber', None,
     r"narcotic|cartel|counter narcotics|mexico|colombia|venezuela|ecuador|peru|brazil|sinaloa|jalisco|tren de aragua|clan del golfo|fentanyl|trafficking"),
    ('Tesoro EE.UU. - Comunicados', 'https://home.treasury.gov/news/press-releases', 'Regional', 'cyber', None,
     r"cartel|narcotic|fentanyl|launder|mexico|colombia|venezuela|ecuador|tren de aragua|sinaloa|jalisco"),
    ('FinCEN - Noticias', 'https://www.fincen.gov/news-room', 'Regional', 'cyber', None,
     r"cartel|fentanyl|launder|mexico|colombia|latin|narcotic|trafficking"),
    ('GAFILAT - Noticias', 'https://www.gafilat.org/index.php/es/noticias', 'Regional', 'cyber', None, None),
    ('México - UIF', 'https://www.gob.mx/uif/prensa', 'México', 'cyber', None, None),
    ('Colombia - UIAF', 'https://www.uiaf.gov.co/', 'Colombia', 'cyber', None, None),
    ('Chile - UAF', 'https://www.uaf.cl/', 'Chile', 'cyber', None, None),
    ('Argentina - UIF', 'https://www.argentina.gob.ar/uif', 'Argentina', 'cyber', None, None),
    ('Brasil - COAF', 'https://www.gov.br/coaf/pt-br', 'Brasil', 'cyber', None, None),
]

# RSS conocidos (se leen primero: suelen pasar aunque la web bloquee). Si alguno ya no existe, solo cuesta una petición.
_RSS_CONOCIDOS = {
    'Clarín Policiales': 'https://www.clarin.com/rss/policiales/',
    'La Nación Seguridad': 'https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/seguridad/?outputType=xml',
    'Infobae Policiales': 'https://www.infobae.com/arc/outboundfeeds/rss/category/sociedad/policiales/?outputType=xml',
    'Perfil Policiales': 'https://www.perfil.com/feed/policiales',
    'El Tiempo Justicia': 'https://www.eltiempo.com/rss/justicia.xml',
    'El Espectador Judicial': 'https://www.elespectador.com/arc/outboundfeeds/rss/category/judicial/?outputType=xml',
    'Verdad Abierta': 'https://verdadabierta.com/feed/',
    'El Universal Seguridad': 'https://www.eluniversal.com.mx/rss.xml',
    'Milenio Policía': 'https://www.milenio.com/rss',
    'La Jornada Policía': 'https://www.jornada.com.mx/rss/edicion.xml?v=1',
    'Animal Político Seguridad': 'https://www.animalpolitico.com/feed',
    'Ríodoce (Sinaloa)': 'https://riodoce.mx/feed/',
    'Zeta Tijuana': 'https://zetatijuana.com/feed/',
    'Sin Embargo': 'https://www.sinembargo.mx/feed',
    'Aristegui Noticias': 'https://aristeguinoticias.com/feed/',
    'Excélsior Seguridad': 'https://www.excelsior.com.mx/rss.xml',
    'Emol Nacional': 'https://www.emol.com/rss/nacional.asmx',
    'La Tercera Crónica': 'https://www.latercera.com/arc/outboundfeeds/rss/category/nacional/?outputType=xml',
    'El Comercio Sucesos': 'https://elcomercio.pe/arc/outboundfeeds/rss/category/lima/sucesos/?outputType=xml',
    'El Universo Seguridad': 'https://www.eluniverso.com/arc/outboundfeeds/rss/category/noticias/seguridad/?outputType=xml',
    'Primicias Seguridad': 'https://www.primicias.ec/feed/',
    'Folha Cotidiano': 'https://feeds.folha.uol.com.br/cotidiano/rss091.xml',
    'g1 Rio de Janeiro': 'https://g1.globo.com/rss/g1/rio-de-janeiro/',
    'g1 São Paulo': 'https://g1.globo.com/rss/g1/sao-paulo/',
    'g1 Brasil': 'https://g1.globo.com/rss/g1/brasil/',
    'UOL Segurança': 'https://rss.uol.com.br/feed/noticias.xml',
    'El País Uruguay Policiales': 'https://www.elpais.com.uy/rss/informacion/policiales.xml',
    'Insight Crime': 'https://insightcrime.org/feed/',
    'BBC Mundo': 'https://feeds.bbci.co.uk/mundo/rss.xml',
    'DW Español Latinoamérica': 'https://rss.dw.com/xml/rss-sp-lat',
    'El País América': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada',
    'CNN en Español': 'https://cnnespanol.cnn.com/feed/',
    'France 24 Español': 'https://www.france24.com/es/rss',
}


def _mk_fuentes():
    out = []

    def base(u):
        p = urlparse(u)
        return f'{p.scheme}://{p.netloc}'
    for n, u, d in _FUENTES_RAW:
        out.append({'nombre': n, 'url': u, 'base': base(u), 'departement': d, 'activo': True, 'tipo': 'faits_divers', 'ctx': 'crime',
                    'rss': _RSS_CONOCIDOS.get(n)})
    for n, u, d, rss in _FUENTES_CYBER_RAW:
        out.append({'nombre': n, 'url': u, 'base': base(u), 'departement': d, 'activo': True, 'tipo': 'cyber', 'ctx': 'cyber', 'rss': rss})
    for n, u, d, ctx, rss, flt in _FUENTES_GOV_RAW:
        out.append({'nombre': n, 'url': u, 'base': base(u), 'departement': d, 'activo': True, 'tipo': 'gov', 'ctx': ctx, 'rss': rss, 'filtro': flt})
    return out


FUENTES_BASE = _mk_fuentes()


# ============================================================================
# GESTOR DE DATOS  (fusion multi-sources, pertinence, alertes officielles)
# ============================================================================

_RLOCK = threading.RLock()


def _fecha_ok(s):
    return bool(s) and re.match(r'^\d{4}-\d{2}-\d{2}', s) is not None


def _parse_fecha(c):
    try:
        return datetime.strptime((c.get('fecha') or '')[:10], '%Y-%m-%d')
    except Exception:
        return None


def _tokens(s):
    return set(re.findall(r'[a-z]{4,}', norm(s)))


def _csv_safe(v):
    v = '' if v is None else str(v).replace('\n', ' ')
    return "'" + v if v[:1] in ('=', '+', '-', '@') else v


def relevancia(c, hoy=None):
    """0-100: sévérité + confiance + nombre de sources qui confirment + fraîcheur."""
    hoy = hoy or datetime.now()
    nf = len(c.get('fuentes') or []) or 1
    dt = _parse_fecha(c)
    dias = max(0, (hoy - dt).days) if dt else 30
    rec = max(0.0, 1 - dias / 14.0)
    r = 4.5 * c.get('severidad', 1) + 0.25 * c.get('confianza', 50) + 20 * min(1.0, (nf - 1) / 3.0) + 10 * rec
    return int(max(0, min(100, round(r))))


def ser(c, hoy=None):
    """Représentation JSON d'un événement pour l'API."""
    return {'id': c.get('id'), 'titulo': c.get('titulo', ''), 'fecha': c.get('fecha', ''), 'departement': c.get('departement', ''),
            'tipo': c.get('tipo', 'other'), 'categoria': c.get('categoria', 'fisico'), 'fuente': c.get('fuente', ''),
            'severidad': c.get('severidad', 1), 'confianza': c.get('confianza', 50), 'relevancia': relevancia(c, hoy),
            'url': c.get('url', ''), 'fuentes': [[f.get('n', ''), f.get('u', '')] for f in (c.get('fuentes') or [])],
            'conflicto': bool(c.get('conflicto'))}


class GestorDatos:
    def __init__(self, archivo=None):
        self.archivo = archivo or ARCHIVO_DATOS
        self.datos = self.cargar()

    # ---- persistencia
    def cargar(self):
        data = {'crimes': [], 'alertas': [], 'ultima_actualizacion': None, 'estadisticas_historicas': {},
                'alarma_ids': [], 'alarma_hist': [], 'config': {}, 'schema': SCHEMA}
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    data.update(json.load(f))
            except Exception as e:
                logger.error(f'Error cargando {self.archivo}: {e}')
        if data.get('incidentes') and not data.get('crimes'):          # formato v7 (diabolic_narco.json)
            for inc in data.pop('incidentes'):
                pais = inc.get('isla') or inc.get('pais') or ''
                data['crimes'].append({'id': inc.get('id') or hashlib.md5(inc.get('titulo', '').encode()).hexdigest()[:16],
                                       'titulo': inc.get('titulo', ''), 'fecha': inc.get('fecha') or datetime.now().strftime('%Y-%m-%d'),
                                       'departement': pais, 'fuente': inc.get('fuente', ''), 'tipo': inc.get('tipo', 'other')})
        for k, v in (('crimes', []), ('alertas', []), ('alarma_ids', []), ('alarma_hist', []), ('config', {})):
            data.setdefault(k, v)
        self._migrar(data)
        return data

    def _migrar(self, data):
        """v1/v2 → v3: catégorie (physique/rue/cyber), géo, confiance, liste de sources."""
        n = 0
        for c in data['crimes']:
            if c.get('v') == SCHEMA:
                continue
            c.setdefault('url', '')
            c.setdefault('fuente', '')
            r = clasificar_detalle(c.get('titulo', ''), '', 'amplio')
            if 'reject' not in r:
                c['tipo'], c['categoria'], c['severidad'], c['confianza'] = r['tipo'], r['cat'], r['sev'], max(50, r['conf'])
            else:
                tp = c.get('tipo') if c.get('tipo') in TIPOS_CRIMEN else 'other'
                c['tipo'] = tp
                c['categoria'] = TIPOS_CRIMEN[tp]['cat']
                c['severidad'] = c.get('severidad') or TIPOS_CRIMEN[tp]['sev']
                c['confianza'] = 40
            if not c.get('dep_code') and c.get('lat') is None:
                _pc = DEP_BY_NAME.get(norm(c.get('departement', '')))
                c.update(geolocalizar(c.get('titulo', ''), _pc, c.get('id', '')))
            c.setdefault('precision', 'none')
            c['fuentes'] = c.get('fuentes') or ([{'n': c['fuente'], 'u': c.get('url', ''), 'f': c.get('fecha', '')}] if c.get('fuente') else [])
            c['conflicto'] = es_conflicto(c['tipo'], c['categoria'], c['severidad'], c['confianza'])
            c['v'] = SCHEMA
            n += 1
        data['schema'] = SCHEMA
        if n:
            logger.info(f'Migrados {n} registros al esquema v{SCHEMA}')

    def guardar(self):
        with _RLOCK:
            self.datos['ultima_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            tmp = self.archivo + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=1, ensure_ascii=False)
            if os.path.exists(self.archivo):
                try:
                    os.replace(self.archivo, ARCHIVO_BACKUP)
                except Exception:
                    pass
            os.replace(tmp, self.archivo)

    # ---- altas con fusión multi-fuente
    @staticmethod
    def _similar(c, recientes):
        tk = _tokens(c['titulo'])
        if not tk:
            return None
        dc = _parse_fecha(c)
        for tk2, e in reversed(recientes):
            if not tk2:
                continue
            j = len(tk & tk2) / len(tk | tk2)
            if j >= 0.8:
                return e
            if j >= 0.5 and e.get('categoria') == c.get('categoria'):
                de = _parse_fecha(e)
                if dc and de and abs((dc - de).days) > 3:
                    continue
                if e.get('dep_code') == c.get('dep_code') or not e.get('dep_code') or not c.get('dep_code'):
                    return e
        return None

    @staticmethod
    def _fusionar(e, c):
        names = {f.get('n') for f in e.get('fuentes', [])}
        changed = False
        for f in c.get('fuentes', []):
            if f.get('n') not in names:
                e.setdefault('fuentes', []).append(f)
                names.add(f.get('n'))
                changed = True
        if changed:
            e['confianza'] = min(100, e.get('confianza', 50) + 8)
            if not e.get('url') and c.get('url'):
                e['url'] = c['url']
            if c.get('severidad', 0) > e.get('severidad', 0):
                e['severidad'] = c['severidad']
            e['conflicto'] = es_conflicto(e['tipo'], e['categoria'], e['severidad'], e['confianza'])
        return changed

    def agregar_crimes(self, nuevos):
        """-> {'added': [events], 'merged': [events]}  (un doublon n'est plus jeté: il devient une source de plus)."""
        res = {'added': [], 'merged': []}
        if not nuevos:
            return res
        with _RLOCK:
            crimes = self.datos['crimes']
            por_id = {c['id']: c for c in crimes}
            recientes = [(_tokens(c['titulo']), c) for c in crimes[-1500:]]
            for c in nuevos:
                e = por_id.get(c['id']) or self._similar(c, recientes)
                if e is not None:
                    if self._fusionar(e, c) and e not in res['merged'] and e not in res['added']:
                        res['merged'].append(e)
                    continue
                crimes.append(c)
                por_id[c['id']] = c
                recientes.append((_tokens(c['titulo']), c))
                res['added'].append(c)
            if res['added']:
                self._actualizar_historicas(res['added'])
            if res['added'] or res['merged']:
                self.guardar()
        return res

    def _actualizar_historicas(self, nuevos):
        h = self.datos.setdefault('estadisticas_historicas', {})
        for c in nuevos:
            f = c.get('fecha', '')
            if len(f) >= 7:
                m = h.setdefault(f[:7], {'total': 0, 'tipos': {}, 'departements': {}})
                m['total'] += 1
                m['tipos'][c.get('tipo', 'other')] = m['tipos'].get(c.get('tipo', 'other'), 0) + 1
                d = c.get('departement', 'Regional')
                m['departements'][d] = m['departements'].get(d, 0) + 1

    # ---- alertas oficiales
    def agregar_alertas(self, nuevas):
        with _RLOCK:
            al = self.datos['alertas']
            ids = {a['id'] for a in al}
            fresh = []
            for a in nuevas:
                if a['id'] not in ids:
                    al.append(a)
                    ids.add(a['id'])
                    fresh.append(a)
            if fresh:
                al.sort(key=lambda a: (a.get('fecha', ''), a.get('nivel', 0)))
                del al[:-500]
                self.guardar()
            return fresh

    def alertas(self, ctx='all'):
        with _RLOCK:
            al = list(self.datos.get('alertas', []))
        if ctx in ('crime', 'cyber'):
            al = [a for a in al if a.get('ctx') == ctx]
        return sorted(al, key=lambda a: (a.get('fecha', ''), a.get('nivel', 0)), reverse=True)

    # ---- alarma / config
    def alarma_ya_vista(self, _id):
        return _id in set(self.datos.get('alarma_ids', []))

    def registrar_alarma(self, items, test=False):
        with _RLOCK:
            if not test:
                ids = self.datos.setdefault('alarma_ids', [])
                ids.extend(i['id'] for i in items)
                del ids[:-2000]
            h = self.datos.setdefault('alarma_hist', [])
            for i in items:
                h.insert(0, {'ts': datetime.now().strftime('%Y-%m-%d %H:%M'), 'titulo': ('[TEST] ' if test else '') + i.get('titulo', ''), 'id': i.get('id')})
            del h[100:]
            self.guardar()

    def cfg(self, k, d=None):
        return self.datos.get('config', {}).get(k, d)

    def set_cfg(self, k, v):
        with _RLOCK:
            self.datos.setdefault('config', {})[k] = v
            self.guardar()

    def copia(self):
        with _RLOCK:
            return list(self.datos.get('crimes', []))

    # ---- compat v1
    def detectar_tipo_crimen(self, texto):
        return clasificar(texto)[0]

    def calcular_severidad(self, texto):
        return clasificar(texto)[2]

    # ---- estadísticas
    def estadisticas(self, crimes=None):
        crimes = self.copia() if crimes is None else crimes
        hoy = datetime.now()
        s = {'total': len(crimes), 'departements': defaultdict(int), 'tipos': defaultdict(int), 'fuentes': defaultdict(int),
             'categorias': defaultdict(int), 'ultimos_7dias': 0, 'prev_7dias': 0, 'ultimos_30dias': 0, 'prev_30dias': 0, 'ultimos_90dias': 0,
             'tendencia': defaultdict(int), 'mensual': defaultdict(lambda: {'fisico': 0, 'rue': 0, 'cyber': 0}),
             'sev_hist': [0] * 10, 'weekday_type': defaultdict(lambda: [0] * 7), 'severidad_promedio': 0.0,
             'conflictos_24h': 0, 'multi_fuente': 0}
        d = lambda n: (hoy - timedelta(days=n)).strftime('%Y-%m-%d')
        h1, h7, h14, h30, h60, h90 = d(1), d(7), d(14), d(30), d(60), d(90)
        lunes = (hoy - timedelta(days=hoy.weekday())).date()
        sem = [(lunes - timedelta(weeks=i)) for i in range(11, -1, -1)]
        semk = {w: {'fisico': 0, 'rue': 0, 'cyber': 0} for w in sem}
        dep_sev = defaultdict(lambda: [0, 0.0])
        ssum, scnt = 0.0, 0
        for c in crimes:
            dep = c.get('departement')
            if dep and dep != 'Regional':
                s['departements'][dep] += 1
                dep_sev[dep][0] += 1
                dep_sev[dep][1] += c.get('severidad', 1)
            if c.get('tipo'):
                s['tipos'][c['tipo']] += 1
            if c.get('fuente'):
                s['fuentes'][c['fuente']] += 1
            cat = c.get('categoria', 'fisico')
            cat = cat if cat in CATEGORIAS else 'fisico'
            s['categorias'][cat] += 1
            if len(c.get('fuentes') or []) > 1:
                s['multi_fuente'] += 1
            sv = c.get('severidad')
            if sv:
                ssum += sv
                scnt += 1
                s['sev_hist'][max(1, min(10, int(sv))) - 1] += 1
            f = c.get('fecha', '')
            if f:
                if f >= h7: s['ultimos_7dias'] += 1
                elif f >= h14: s['prev_7dias'] += 1
                if f >= h30: s['ultimos_30dias'] += 1
                elif f >= h60: s['prev_30dias'] += 1
                if f >= h90: s['ultimos_90dias'] += 1
                if f >= h1 and c.get('conflicto'): s['conflictos_24h'] += 1
                if len(f) >= 7:
                    s['tendencia'][f[:7]] += 1
                    s['mensual'][f[:7]][cat] += 1
                dt = _parse_fecha(c)
                if dt:
                    s['weekday_type'][c.get('tipo', 'other')][dt.weekday()] += 1
                    w = dt.date() - timedelta(days=dt.weekday())
                    if w in semk:
                        semk[w][cat] += 1
        if scnt:
            s['severidad_promedio'] = ssum / scnt
        s['semanal'] = {'labels': [w.strftime('%d/%m') for w in sem], **{k: [semk[w][k] for w in sem] for k in CATEGORIAS}}
        s['dept_bubble'] = [{'d': k, 'n': v[0], 'sev': round(v[1] / v[0], 1)} for k, v in sorted(dep_sev.items(), key=lambda x: -x[1][0])[:15]]
        return s

    def evolucion_mensual(self):
        m = {}
        for c in self.copia():
            f = c.get('fecha', '')
            if len(f) >= 7:
                m[f[:7]] = m.get(f[:7], 0) + 1
        return dict(sorted(m.items()))

    def limpiar_duplicados(self):
        """Fusionne les quasi-doublons existants (les sources s'additionnent)."""
        with _RLOCK:
            antes = len(self.datos['crimes'])
            out, recientes = [], []
            for c in self.datos['crimes']:
                e = self._similar(c, recientes[-1200:]) if c.get('titulo') else None
                if e is not None:
                    self._fusionar(e, c)
                    continue
                out.append(c)
                recientes.append((_tokens(c['titulo']), c))
            self.datos['crimes'] = out
            if len(out) != antes:
                self.guardar()
            return antes - len(out)

    def estadisticas_rapidas(self):
        crimes = self.copia()
        st = self.estadisticas(crimes)
        if not st['total']:
            return {}
        tm = max(st['tipos'].items(), key=lambda x: x[1]) if st['tipos'] else ('other', 0)
        dias = Counter(c['fecha'][:10] for c in crimes if c.get('fecha'))
        dm = dias.most_common(1)[0] if dias else ('-', 0)
        fm = max(st['fuentes'].items(), key=lambda x: x[1]) if st['fuentes'] else ('-', 0)
        dc = max(st['departements'].items(), key=lambda x: x[1]) if st['departements'] else ('-', 0)
        tend = 0.0
        ms = sorted(st['tendencia'])
        if len(ms) >= 2 and st['tendencia'][ms[-2]] > 0:
            tend = (st['tendencia'][ms[-1]] - st['tendencia'][ms[-2]]) / st['tendencia'][ms[-2]] * 100
        return {'tipo_mas_comun': tm[0], 'tipo_mas_comun_count': tm[1], 'tipo_mas_comun_porcentaje': tm[1] / st['total'] * 100,
                'dia_mas_activo': dm[0], 'dia_mas_activo_count': dm[1], 'fuente_mas_activa': fm[0], 'fuente_mas_activa_count': fm[1],
                'departamento_critico': dc[0], 'departamento_critico_count': dc[1], 'tendencia': tend}

    # ---- exportaciones
    def exportar_json(self):
        return json.dumps(self.datos, indent=2, ensure_ascii=False)

    def exportar_csv(self, crimes=None):
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(['ID', 'Titulo', 'Fecha', 'Pais', 'Codigo', 'Tipo', 'Categoria', 'Fuente', 'Severidad', 'Confianza', 'Relevancia', 'N fuentes', 'Fuentes', 'Lat', 'Lon', 'URL'])
        for c in (self.copia() if crimes is None else crimes):
            fs = c.get('fuentes') or []
            w.writerow([c['id'], _csv_safe(c.get('titulo')), c.get('fecha', ''), _csv_safe(c.get('departement')), c.get('dep_code') or '',
                        c.get('tipo', ''), c.get('categoria', ''), _csv_safe(c.get('fuente')), c.get('severidad', 0), c.get('confianza', ''),
                        relevancia(c), len(fs), _csv_safe(' | '.join(f.get('n', '') for f in fs)), c.get('lat') or '', c.get('lon') or '', c.get('url', '')])
        return out.getvalue()

    def exportar_geojson(self, crimes=None):
        feats = []
        for c in (self.copia() if crimes is None else crimes):
            if c.get('lat') is None:
                continue
            p = {k: c.get(k) for k in ('id', 'titulo', 'fecha', 'departement', 'tipo', 'categoria', 'fuente', 'severidad', 'confianza', 'url', 'precision')}
            p['relevancia'] = relevancia(c)
            p['fuentes'] = [{'n': f.get('n'), 'u': f.get('u')} for f in (c.get('fuentes') or [])]
            feats.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [c['lon'], c['lat']]}, 'properties': p})
        return json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False)

    def exportar_html(self):
        st = self.estadisticas()
        e = htmllib.escape
        h = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>DIABOLIC LATAM - Reporte</title>
<style>body{{background:#03050c;color:#e6f4ff;font-family:'Segoe UI',sans-serif;padding:20px}}h1{{color:#00e5ff;text-align:center}}h2{{color:#ff2bd6;margin-top:30px}}
.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}}.c{{background:#0a1630;padding:14px;border-radius:10px;text-align:center;border-left:4px solid #00e5ff}}.n{{font-size:2em;color:#00e5ff;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin:14px 0}}th,td{{border:1px solid #16304f;padding:7px;text-align:left}}th{{background:#0a1630;color:#ff2bd6}}a{{color:#00e5ff}}</style></head><body>
<h1>🔪 DIABOLIC LATAM v{VERSION}</h1><p style="text-align:center">{datetime.now():%Y-%m-%d %H:%M:%S}</p>
<div class="g"><div class="c">Total<div class="n">{st['total']}</div></div><div class="c">7 d<div class="n">{st['ultimos_7dias']}</div></div>
<div class="c">Violencia<div class="n">{st['categorias'].get('rue', 0)}</div></div><div class="c">Finanzas<div class="n">{st['categorias'].get('cyber', 0)}</div></div></div>
<h2>Países</h2><table><tr><th>País</th><th>#</th></tr>"""
        for d, n in sorted(st['departements'].items(), key=lambda x: -x[1])[:15]:
            h += f"<tr><td>{e(d)}</td><td>{n}</td></tr>"
        h += "</table><h2>Tipos</h2><table><tr><th>Tipo</th><th>#</th></tr>"
        for k, n in sorted(st['tipos'].items(), key=lambda x: -x[1]):
            dd = TIPOS_CRIMEN.get(k, TIPOS_CRIMEN['other'])
            h += f"<tr><td>{dd['icono']} {e(dd['es'])}</td><td>{n}</td></tr>"
        h += "</table><h2>Últimos (25) por relevancia</h2><table><tr><th>Fecha</th><th>País</th><th>Tipo</th><th>Título</th><th>Rel.</th><th>Sources</th></tr>"
        for c in sorted(self.copia(), key=lambda x: (x.get('fecha', ''), relevancia(x)), reverse=True)[:25]:
            srcs = ', '.join((f'<a href="{e(f["u"])}">{e(f["n"])}</a>' if re.match(r'^https?://', f.get('u') or '') else e(f.get('n', ''))) for f in (c.get('fuentes') or []))
            h += f"<tr><td>{e(c.get('fecha',''))}</td><td>{e(c.get('departement','?'))}</td><td>{e(c.get('tipo','?'))}</td><td>{e(c['titulo'][:140])}</td><td>{relevancia(c)}</td><td>{srcs}</td></tr>"
        return h + "</table></body></html>"

# ============================================================================
# ANALÍTICA  (z-score, tendencias, Holt, hotspots, grafos, INDICADORES estilo crypto)
# ============================================================================

STOP = set("""para como pero sobre entre desde hasta este esta estos estas luego donde cuando quien segun tras ante cada
tambien porque mientras ayer hoy manana semana mes anos dias dia video fotos foto lee leer nota noticia noticias ultima
ultimo nuevo nueva policia policial fiscalia investigacion mais pelo pela uma uns como quando onde apos sobre entre
the with from that this have been after into over their about police news report today""".split())


def _hav(la1, lo1, la2, lo2):
    return math.hypot(la1 - la2, (lo1 - lo2) * math.cos(math.radians((la1 + la2) / 2)))


def _sma(a, w):
    out = []
    for i in range(len(a)):
        seg = a[max(0, i - w + 1): i + 1]
        out.append(sum(seg) / len(seg))
    return out


def _std(a):
    if not a:
        return 0.0
    m = sum(a) / len(a)
    return math.sqrt(sum((x - m) ** 2 for x in a) / len(a))


def _rsi(a, n=14):
    """RSI de Wilder sur la série des comptes quotidiens (0-100; >70 escalade, <30 apaisement)."""
    out = [50.0] * len(a)
    if len(a) <= n:
        return out
    gains = [max(0, a[i] - a[i - 1]) for i in range(1, len(a))]
    loss = [max(0, a[i - 1] - a[i]) for i in range(1, len(a))]
    ag, al = sum(gains[:n]) / n, sum(loss[:n]) / n
    for i in range(n, len(a)):
        if i > n:
            ag = (ag * (n - 1) + gains[i - 1]) / n
            al = (al * (n - 1) + loss[i - 1]) / n
        out[i] = 100.0 if al == 0 and ag > 0 else (50.0 if al == 0 else 100 - 100 / (1 + ag / al))
    return out


def _threat(counts, sev7, rue_share):
    base = counts[:-7] or counts
    mu, sd = (sum(base) / len(base), _std(base)) if base else (0, 0)
    last7 = sum(counts[-7:]) / 7.0
    z = (last7 - mu) / sd if sd > 0 else 0.0
    idx = 38 + 16 * max(-2.0, min(3.0, z)) + 3.0 * (sev7 - 4) + 14 * rue_share
    return max(0.0, min(100.0, idx))


class Analitica:
    @staticmethod
    def serie_diaria(crimes, dias=60):
        hoy = datetime.now().date()
        base = {(hoy - timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(dias - 1, -1, -1)}
        for c in crimes:
            f = (c.get('fecha') or '')[:10]
            if f in base:
                base[f] += 1
        vals = list(base.values())
        mu = sum(vals) / len(vals) if vals else 0
        sd = _std(vals)
        return [{'date': d, 'count': n, 'z': round((n - mu) / sd, 2) if sd > 0 else 0.0} for d, n in base.items()]

    @staticmethod
    def holt(series, alpha=.5, beta=.3, h=4):
        if len(series) < 4:
            return []
        lv, b = series[0], series[1] - series[0]
        for y in series[1:]:
            lp = lv
            lv = alpha * y + (1 - alpha) * (lv + b)
            b = beta * (lv - lp) + (1 - beta) * b
        return [max(0.0, round(lv + (i + 1) * b, 1)) for i in range(h)]

    @staticmethod
    def pronostico(crimes, semanas=16, h=4):
        hoy = datetime.now().date()
        lunes_act = hoy - timedelta(days=hoy.weekday())
        wk = [lunes_act - timedelta(weeks=i) for i in range(semanas, 0, -1)]
        cnt = Counter()
        for c in crimes:
            dt = _parse_fecha(c)
            if dt:
                d = dt.date()
                cnt[d - timedelta(days=d.weekday())] += 1
        hist = [cnt.get(w, 0) for w in wk]
        pred = Analitica.holt(hist, h=h)
        fut = [(lunes_act + timedelta(weeks=i)).strftime('%Y-%m-%d') for i in range(h)]
        return {'hist_labels': [w.strftime('%Y-%m-%d') for w in wk], 'hist': hist, 'pred_labels': fut, 'pred': pred}

    @staticmethod
    def tendencias(crimes, n=28):
        hoy = datetime.now()
        h7 = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
        h60 = (hoy - timedelta(days=60)).strftime('%Y-%m-%d')
        a, b = Counter(), Counter()
        for c in crimes:
            f = c.get('fecha', '')
            toks = [w for w in re.findall(r'[a-z]{4,}', norm(c['titulo'])) if w not in STOP]
            if f >= h7:
                a.update(set(toks))
            elif f >= h60:
                b.update(set(toks))
        out = []
        for w, ca in a.items():
            if ca < 3:
                continue
            esperado = b.get(w, 0) * 7 / 53
            out.append({'word': w, 'count': ca, 'score': round((ca + 1) / (esperado + 1), 2)})
        out.sort(key=lambda x: (-x['score'], -x['count']))
        return out[:n]

    @staticmethod
    def hotspots(crimes, celda=0.4, top=8):
        g = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
        for c in crimes:
            if c.get('lat') is None or c.get('lon') is None:
                continue
            k = (round(c['lat'] / celda), round(c['lon'] / celda))
            v = g[k]
            v[0] += 1; v[1] += c['lat']; v[2] += c['lon']; v[3] += c.get('severidad', 1)
        res = []
        for k, (n, sl, so, ss) in g.items():
            la, lo = sl / n, so / n
            code = min(DEPS, key=lambda d: _hav(la, lo, DEPS[d][1], DEPS[d][2]))
            res.append({'lat': round(la, 4), 'lon': round(lo, 4), 'count': n, 'sev': round(ss / n, 1),
                        'score': round(n * (1 + ss / n / 5), 1), 'label': DEPS[code][0]})
        res.sort(key=lambda x: -x['score'])
        return res[:top]

    @staticmethod
    def red(crimes, max_edges=45):
        cnt = Counter((c['tipo'], c['departement']) for c in crimes if c.get('dep_code') and c.get('tipo') != 'other')
        edges = cnt.most_common(max_edges)
        nodes, tv, dv = {}, Counter(), Counter()
        for (tp, dp), n in edges:
            tv[tp] += n; dv[dp] += n
        for tp, n in tv.items():
            nodes['t:' + tp] = {'id': 't:' + tp, 'key': tp, 'group': 'tipo', 'label': tp, 'value': n}
        for dp, n in dv.items():
            nodes['d:' + dp] = {'id': 'd:' + dp, 'key': dp, 'group': 'dep', 'label': dp, 'value': n}
        return {'nodes': list(nodes.values()), 'edges': [{'from': 't:' + tp, 'to': 'd:' + dp, 'value': n} for (tp, dp), n in edges]}

    @staticmethod
    def sankey(crimes, top_deps=8):
        deps = Counter(c['departement'] for c in crimes if c.get('dep_code'))
        top = {d for d, _ in deps.most_common(top_deps)}
        a, b = Counter(), Counter()
        for c in crimes:
            if c.get('tipo') == 'other':
                continue
            a[('cat:' + c.get('categoria', 'fisico'), 'tipo:' + c['tipo'])] += 1
            if c.get('departement') in top:
                b[('tipo:' + c['tipo'], 'dep:' + c['departement'])] += 1
        return {'flows': [[x, y, n] for (x, y), n in list(a.items()) + list(b.items())]}

    @staticmethod
    def indicadores(crimes, dias=90):
        """Indicateurs façon marché crypto appliqués au flux criminel: SMA, Bollinger, RSI, indice de menace, tickers."""
        hoy = datetime.now().date()
        ds = [(hoy - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(dias - 1, -1, -1)]
        pos = {d: i for i, d in enumerate(ds)}
        counts = [0] * dias
        bycat = {k: [0] * dias for k in CATEGORIAS}
        bytipo = defaultdict(lambda: [0] * dias)
        sev = [[] for _ in range(dias)]
        for c in crimes:
            i = pos.get((c.get('fecha') or '')[:10])
            if i is None:
                continue
            counts[i] += 1
            cat = c.get('categoria') if c.get('categoria') in CATEGORIAS else 'fisico'
            bycat[cat][i] += 1
            bytipo[c.get('tipo', 'other')][i] += 1
            sev[i].append(c.get('severidad', 1))
        sma7, sma30 = _sma(counts, 7), _sma(counts, 30)
        bb_up, bb_dn = [], []
        for i in range(dias):
            seg = counts[max(0, i - 19): i + 1]
            m, sd = sum(seg) / len(seg), _std(seg)
            bb_up.append(round(m + 2 * sd, 2)); bb_dn.append(round(max(0.0, m - 2 * sd), 2))
        rsi = _rsi(counts)
        mom = (sma7[-1] / sma30[-1] - 1) * 100 if sma30[-1] > 0 else 0.0
        signal = 'up' if (rsi[-1] > 65 or mom > 15) else 'dn' if (rsi[-1] < 35 or mom < -15) else 'fl'
        l14 = counts[-14:]
        vol = (_std(l14) / (sum(l14) / 14)) if sum(l14) > 0 else 0.0
        flat = lambda L: [x for s in L[-7:] for x in s]
        sv7 = flat(sev)
        sev7 = sum(sv7) / len(sv7) if sv7 else 4.0
        sv_prev = [x for s in sev[-14:-7] for x in s]
        sevp = sum(sv_prev) / len(sv_prev) if sv_prev else sev7
        n7 = sum(counts[-7:])
        share = (sum(bycat['rue'][-7:]) / n7) if n7 else 0.0
        idx = _threat(counts, sev7, share)
        n7p = sum(counts[-14:-7])
        sev_p = [x for s in sev[:-7] for x in s]
        idx_prev = _threat(counts[:-7], sevp, (sum(bycat['rue'][-14:-7]) / n7p) if n7p else 0.0) if dias > 21 else idx
        dl = lambda a, b: ((a - b) / b * 100) if b > 0 else (100.0 if a > 0 else 0.0)
        T = []
        T.append({'key': 'idx', 'kind': 'idx', 'label': 'threat_idx', 'value': round(idx, 1), 'delta': round(dl(idx, idx_prev), 1), 'series': [round(_threat(counts[:len(counts) - k], sev7, share), 1) for k in range(13, -1, -1)]})
        T.append({'key': 'all', 'kind': 'all', 'label': 'f_all', 'value': n7, 'delta': round(dl(n7, n7p), 1), 'series': counts[-14:]})
        for k in CATEGORIAS:
            a, b = sum(bycat[k][-7:]), sum(bycat[k][-14:-7])
            T.append({'key': k, 'kind': 'cat', 'value': a, 'delta': round(dl(a, b), 1), 'series': bycat[k][-14:]})
        top = sorted(((sum(v[-30:]), k) for k, v in bytipo.items() if k != 'other'), reverse=True)[:6]
        for _, k in top:
            a, b = sum(bytipo[k][-7:]), sum(bytipo[k][-14:-7])
            T.append({'key': k, 'kind': 'tipo', 'value': a, 'delta': round(dl(a, b), 1), 'series': bytipo[k][-14:]})
        T.append({'key': 'rsi', 'kind': 'rsi', 'label': 'RSI', 'value': round(rsi[-1], 1), 'delta': round(dl(rsi[-1], rsi[-8]), 1), 'series': [round(x, 1) for x in rsi[-14:]]})
        T.append({'key': 'sev', 'kind': 'sev', 'label': 'k_sev', 'value': round(sev7, 1), 'delta': round(dl(sev7, sevp), 1), 'series': [round(sum(s) / len(s), 1) if s else 0 for s in sev[-14:]]})
        return {'tickers': T, 'rsi': round(rsi[-1], 1), 'momentum': round(mom, 1), 'signal': signal, 'volatility': round(vol, 2),
                'threat': {'idx': round(idx, 1), 'level': 0 if idx < 25 else 1 if idx < 50 else 2 if idx < 75 else 3},
                'series': {'dates': ds, 'counts': counts, 'sma7': [round(x, 2) for x in sma7], 'sma30': [round(x, 2) for x in sma30],
                           'up': bb_up, 'dn': bb_dn, 'rsi': [round(x, 1) for x in rsi]}}

    @staticmethod
    def analytics(crimes):
        diaria = Analitica.serie_diaria(crimes)
        return {'daily': diaria, 'anomalies': [d for d in diaria if d['z'] >= 2 and d['count'] >= 3],
                'forecast': Analitica.pronostico(crimes), 'trending': Analitica.tendencias(crimes), 'hotspots': Analitica.hotspots(crimes)}

# ============================================================================
# GRÁFICOS ESTÁTICOS (matplotlib / networkx)
# ============================================================================

def render_estatico(kind, crimes, lang='es'):
    """Devuelve bytes PNG, o None si falta matplotlib (o networkx para 'red')."""
    if not HAS_MPL or (kind == 'red' and not HAS_NX):
        return None
    lang = lang if lang in LANGS else 'es'
    bg, fg, grid = '#0b0f1a', '#d7dbe5', '#222a3d'
    plt.rcParams.update({'text.color': fg, 'axes.labelcolor': fg, 'xtick.color': fg, 'ytick.color': fg,
                         'axes.edgecolor': grid, 'axes.facecolor': bg, 'figure.facecolor': bg, 'font.size': 9})
    fig, ax = plt.subplots(figsize=(9, 5.2))
    tn = lambda k: TIPOS_CRIMEN.get(k, TIPOS_CRIMEN['other'])[lang]
    try:
        if kind == 'tipos':
            cnt = Counter(c['tipo'] for c in crimes if c.get('tipo') != 'other').most_common()[::-1]
            if not cnt: raise ValueError('empty')
            ax.barh([tn(k) for k, _ in cnt], [n for _, n in cnt], color=[TIPOS_CRIMEN[k]['color'] for k, _ in cnt])
            ax.set_title(TEXTOS[lang]['st_tipos'])
            ax.grid(axis='x', color=grid)
        elif kind == 'mensual':
            m = defaultdict(lambda: [0, 0])
            for c in crimes:
                f = c.get('fecha', '')[:7]
                if len(f) == 7:
                    m[f][1 if c.get('categoria') == 'cyber' else 0] += 1
            if not m: raise ValueError('empty')
            ks = sorted(m)[-18:]
            ax.bar(ks, [m[k][0] for k in ks], color='#ff2d55', label=TEXTOS[lang]['phys'])
            ax.bar(ks, [m[k][1] for k in ks], bottom=[m[k][0] for k in ks], color='#2f5bff', label=TEXTOS[lang]['cyber'])
            ax.legend(facecolor=bg, edgecolor=grid)
            ax.set_title(TEXTOS[lang]['st_mensual'])
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            ax.grid(axis='y', color=grid)
        elif kind == 'heatmap':
            cnt = Counter(c['tipo'] for c in crimes if c.get('tipo') != 'other')
            tipos = [k for k, _ in cnt.most_common(12)]
            if not tipos: raise ValueError('empty')
            mat = [[0] * 7 for _ in tipos]
            for c in crimes:
                if c.get('tipo') in tipos:
                    dt = _parse_fecha(c)
                    if dt: mat[tipos.index(c['tipo'])][dt.weekday()] += 1
            im = ax.imshow(mat, cmap='inferno', aspect='auto')
            ax.set_yticks(range(len(tipos))); ax.set_yticklabels([tn(k) for k in tipos])
            ax.set_xticks(range(7)); ax.set_xticklabels(['L', 'M', 'X', 'J', 'V', 'S', 'D'] if lang == 'es'
                                                        else ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'])
            for i in range(len(tipos)):
                for j in range(7):
                    ax.text(j, i, mat[i][j], ha='center', va='center', color='white', fontsize=7)
            fig.colorbar(im, ax=ax)
            ax.set_title(TEXTOS[lang]['st_heatmap'])
        elif kind == 'hexbin':
            pts = [(c['lon'], c['lat']) for c in crimes if c.get('lat') is not None and -6 < c['lon'] < 10 and 41 < c['lat'] < 52]
            if not pts: raise ValueError('empty')
            hb = ax.hexbin([p[0] for p in pts], [p[1] for p in pts], gridsize=34, cmap='inferno', mincnt=1,
                           extent=(-5.5, 9.8, 41, 51.5))
            ax.set_aspect(1 / math.cos(math.radians(46)))
            ax.set_xlim(-5.5, 9.8); ax.set_ylim(41, 51.5)
            fig.colorbar(hb, ax=ax)
            for code in ('75', '13', '69', '31', '06', '33', '59', '67', '44', '35'):
                n, la, lo = DEPS[code]
                ax.annotate(n, (lo, la), color='#9aa3b2', fontsize=7)
            ax.set_title(TEXTOS[lang]['st_hexbin'])
        elif kind == 'red':
            red = Analitica.red(crimes, 40)
            if not red['edges']: raise ValueError('empty')
            G = nx.Graph()
            for n in red['nodes']:
                G.add_node(n['id'], **n)
            for e in red['edges']:
                G.add_edge(e['from'], e['to'], weight=e['value'])
            pos = nx.spring_layout(G, seed=7, k=0.9)
            cols = [TIPOS_CRIMEN[G.nodes[n]['key']]['color'] if n.startswith('t:') else '#475569' for n in G]
            sizes = [180 + 55 * G.nodes[n]['value'] for n in G]
            nx.draw_networkx_edges(G, pos, ax=ax, alpha=.35, edge_color='#64748b',
                                   width=[0.5 + .4 * G[u][v]['weight'] for u, v in G.edges()])
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=cols, node_size=sizes, linewidths=0)
            nx.draw_networkx_labels(G, pos, ax=ax, font_color='#e5e7eb', font_size=7,
                                    labels={n: tn(G.nodes[n]['key']) if n.startswith('t:') else G.nodes[n]['label'] for n in G})
            ax.axis('off')
            ax.set_title(TEXTOS[lang]['st_red'])
        else:
            plt.close(fig)
            return None
    except ValueError:
        ax.text(.5, .5, TEXTOS[lang]['no_data'], ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=130, facecolor=bg)
    plt.close(fig)
    return buf.getvalue()


# ============================================================================
# ESTADO DE LAS FUENTES (salud, URL descubierta, fuentes añadidas desde el panel)
# ============================================================================

_ESTADO_LOCK = threading.RLock()
ESTADO = {'fuentes': {}, 'custom': []}


def cargar_estado():
    """Lee el estado; acepta el formato plano de la v2 ({nombre: {url, activo}})."""
    global ESTADO
    try:
        with open(ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        d = {}
    if 'fuentes' not in d:
        d = {'fuentes': {k: v for k, v in d.items() if isinstance(v, dict)}, 'custom': []}
    d.setdefault('custom', [])
    ESTADO = d
    return ESTADO


def guardar_estado():
    with _ESTADO_LOCK:
        try:
            tmp = ARCHIVO_ESTADO + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(ESTADO, f, indent=1, ensure_ascii=False)
            os.replace(tmp, ARCHIVO_ESTADO)
        except Exception as e:
            logger.warning(f'estado: {e}')


def aplicar_estado(fuentes):
    cargar_estado()
    nombres = {f['nombre'] for f in fuentes}
    for c in ESTADO.get('custom', []):
        if c.get('nombre') not in nombres:
            fuentes.append(c)
    for f in fuentes:
        e = ESTADO['fuentes'].get(f['nombre'])
        if e:
            f['url'] = e.get('url') or f['url']
            f['activo'] = e.get('activo', True)
            if e.get('rss_auto') and not f.get('rss'):
                f['rss_auto'] = e['rss_auto']
            p = urlparse(f['url'])
            f['base'] = f'{p.scheme}://{p.netloc}'
    return fuentes


def registrar_salud(f, info=None):
    with _ESTADO_LOCK:
        e = ESTADO['fuentes'].setdefault(f['nombre'], {})
        e['url'] = f['url']
        e['activo'] = f.get('activo', True)
        if f.get('rss_auto'):
            e['rss_auto'] = f['rss_auto']
        if info is not None:
            ok = info.get('kind') == 'ok'
            e['last'] = {'n': info.get('n', 0), 'cand': info.get('cand', 0), 'kind': info.get('kind', ''), 'dur': info.get('dur', 0),
                         'note': info.get('note', ''), 'ts': datetime.now().isoformat(timespec='seconds')}
            e['fails'] = 0 if ok else e.get('fails', 0) + 1
    guardar_estado()

# ============================================================================
# AUTO-DISCOVERY DE URLs   (la herramienta se repara sola cuando una fuente cambia de cabecera/subdominio/sección)
# ============================================================================

_SEC_CRIME = {'policiales': 12, 'policial': 12, 'policia': 8, 'sucesos': 12, 'judicial': 10, 'judiciales': 10, 'justicia': 6, 'seguridad': 6,
              'seguranca': 6, 'crimen': 6, 'narcotrafico': 10, 'cronica': 4, 'nacional': 2, 'nacionales': 2, 'crime': 6, 'cotidiano': 3}
_SEC_CYBER = {'investigaciones': 10, 'investigations': 10, 'lavado': 10, 'corrupcion': 8, 'crimen-organizado': 10, 'ambiental': 5, 'seguridad': 4, 'analisis': 4}
_SEC_GOV = {'noticias': 8, 'prensa': 6, 'comunicados': 8, 'comunicado': 6, 'news': 8, 'press': 6, 'noticias-': 4, 'alertas': 7, 'seguridad': 3, 'imprensa': 5, 'noticia': 5}
_PATHS_V1 = ['policiales', 'policial', 'sucesos', 'judicial', 'seguridad', 'justicia', 'policia', 'nacional', 'crimen', 'narcotrafico', 'cronica', 'violencia']
_PATHS_CYBER = ['investigaciones', 'investigations', 'seguridad', 'lavado', 'corrupcion']
_PATHS_GOV = ['noticias', 'prensa', 'comunicados', 'news', 'press-releases', 'alertas']


def _reg(host):
    return '.'.join((host or '').split(':')[0].split('.')[-2:])


def _fecha_desde_url(u):
    m = re.search(r'/(20\d\d)[/-](0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])(?:/|-|$)', u or '')
    return f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else None


class URLAutoDiscoverer:
    def __init__(self):
        self.cache_file = ARCHIVO_CACHE
        self.cache = self.load_cache()
        self.common_paths = _PATHS_V1

    def load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def pagina_valida(html):
        """¿Parece un listado de noticias? (estructura) o contiene palabras clave v1 del dominio."""
        if len(re.findall(r'<article|<h[23][ >]', html or '', re.I)) >= 4:
            return True
        low = (html or '').lower()
        return any(k in low for k in ('meurtre', 'violence', 'crime', 'braquage', 'cyberattaque', 'ransomware', 'piratage'))

    def probar_url(self, url, intentos=1):
        r, _ = fetch(url, intentos=intentos, timeout=15)
        return r.text if (r is not None and self.pagina_valida(r.text)) else None

    @staticmethod
    def variantes(url):
        p = urlparse(url)
        hosts = [p.netloc, p.netloc[4:] if p.netloc.startswith('www.') else 'www.' + p.netloc]
        path = p.path or '/'
        paths = [path, path.rstrip('/') if path != '/' else path, (path + '/') if not path.endswith('/') else path]
        out = []
        for h in hosts:
            for pa in paths:
                u = f'{p.scheme}://{h}{pa}' + (('?' + p.query) if p.query else '')
                if u != url and u not in out:
                    out.append(u)
        return out

    @staticmethod
    def feeds_de(html, base):
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception:
            return []
        out = []
        for l in soup.find_all('link', href=True):
            t = (l.get('type') or '').lower()
            if 'rss' in t or 'atom' in t:
                out.append(urljoin(base, l['href']))
        return list(dict.fromkeys(out))[:4]

    def candidatos_home(self, base_url, html, ctx):
        words = _SEC_CYBER if ctx == 'cyber' else _SEC_GOV if ctx == 'gov' else _SEC_CRIME
        host = _reg(urlparse(base_url).netloc)
        found = {}
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception:
            return []
        for a in soup.find_all('a', href=True)[:900]:
            href = urljoin(base_url, a['href']).split('#')[0]
            pu = urlparse(href)
            if pu.scheme not in ('http', 'https') or _reg(pu.netloc) != host:
                continue
            path = norm(pu.path)
            segs = [s for s in pu.path.split('/') if s]
            txt = norm(a.get_text(' '))[:60]
            sc = sum(w for k, w in words.items() if k in path) + sum(w * 0.6 for k, w in words.items() if k in txt)
            if len(segs) > 3:
                sc -= 4
            if re.search(r'\d{5,}|[-_]\d{3,}\.html?$', pu.path):
                sc -= 6
            if pu.query:
                sc -= 2
            if sc >= 5:
                found[href] = max(found.get(href, 0), sc)
        return sorted(((s, u) for u, s in found.items()), reverse=True)[:6]

    def _guardar(self, nombre, url, how):
        self.cache[nombre] = {'url': url, 'found_date': datetime.now().isoformat(timespec='seconds'), 'how': how}
        self.save_cache()
        return url

    def discover_url(self, fuente, razon='', deadline=None):
        """-> (nueva_url | None, como).  Orden: caché → www/apex/slash → enlaces de la portada → rutas v1."""
        nombre, orig = fuente['nombre'], fuente['url']
        ctx = 'gov' if fuente.get('tipo') == 'gov' else fuente.get('ctx', 'crime')
        vencido = lambda: deadline is not None and time.time() > deadline
        cu = self.cache.get(nombre, {}).get('url')
        if cu and cu != orig and self.probar_url(cu):
            return cu, 'cache'
        for v in self.variantes(orig):
            if vencido():
                return None, 'tiempo'
            if self.probar_url(v):
                return self._guardar(nombre, v, 'variante'), 'variante'
        bases = [fuente['base']] + [b for b in self.variantes(fuente['base'] + '/')]
        for b in dict.fromkeys(bases):
            if vencido():
                return None, 'tiempo'
            r, k = fetch(b, 1, 15)
            if r is None:
                continue
            feeds = self.feeds_de(r.text, r.url)
            if feeds and not fuente.get('rss'):
                fuente['rss_auto'] = feeds[0]
            for sc, u in self.candidatos_home(r.url, r.text, ctx):
                if vencido():
                    return None, 'tiempo'
                if self.probar_url(u):
                    return self._guardar(nombre, u, 'nav'), 'nav'
            break
        paths = _PATHS_GOV if ctx == 'gov' else _PATHS_CYBER if ctx == 'cyber' else self.common_paths
        base = fuente['base'].rstrip('/')
        for path in paths[:8]:
            for test in (f'{base}/{path}', f'{base}/{path}/', f'{base}/rubrique/{path}'):
                if vencido():
                    return None, 'tiempo'
                if self.probar_url(test):
                    return self._guardar(nombre, test, 'ruta'), 'ruta'
        return None, 'sin_resultado'


class VerificadorFuentes:
    """Menú 8 / botón 'Verificar': comprueba cada fuente (3 intentos como v1) y repara URLs con auto-discovery."""
    def __init__(self):
        self.discoverer = URLAutoDiscoverer()

    def verificar_fuente(self, fuente, aplicar_discovery=True):
        r, kind = fetch(fuente['url'], MAX_INTENTOS)
        if r is not None:
            fuente['activo'] = True
            return fuente, True, kind
        if aplicar_discovery:
            nueva, how = self.discoverer.discover_url(fuente, kind, time.time() + PRESUPUESTO_FUENTE)
            if nueva:
                fuente['url'] = nueva
                p = urlparse(nueva)
                fuente['base'] = f'{p.scheme}://{p.netloc}'
                fuente['activo'] = True
                return fuente, True, 'disc:' + how
        fuente['activo'] = False
        return fuente, False, kind

    def verificar_todas(self, fuentes, mostrar_progreso=True, progreso=None, stop=None):
        emit('info', f"\n{'═' * 78}\n🔍 {t('m_verify').upper()}\n{'═' * 78}")
        activas, auto, total = 0, 0, len(fuentes)
        res = []
        for i, f in enumerate(fuentes, 1):
            if stop is not None and stop.is_set():
                emit('warn', '■ stop')
                break
            orig = f['url']
            fv, ok, how = self.verificar_fuente(f, True)
            if ok:
                activas += 1
                if fv['url'] != orig:
                    auto += 1
                    emit('disc', f"[{i:2d}/{total}] ↻ {fv['nombre']}  {orig}  →  {fv['url']}")
                else:
                    emit('ok', f"[{i:2d}/{total}] ✔ {fv['nombre']}")
            else:
                emit('err', f"[{i:2d}/{total}] ✖ {fv['nombre']}  ({how})")
            registrar_salud(fv)
            res.append(fv)
            if progreso:
                progreso(i / total, fv['nombre'], i)
        emit('info', f"📊 {activas}/{total} OK · ↻ {auto} auto-discovery")
        return res

# ============================================================================
# EXTRACTOR  (cosecha v1 + RSS + clasificación anti-falsos-positivos)
# ============================================================================

def _xml_texto(s):
    s = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return limpiar(htmllib.unescape(s))


def parse_rss(texto):
    out = []
    for blk in re.findall(r'<item[ >].*?</item>|<entry[ >].*?</entry>', texto, re.S | re.I)[:60]:
        def g(tag):
            m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', blk, re.S | re.I)
            return _xml_texto(m.group(1)) if m else ''
        link = g('link')
        if not link:
            m = re.search(r'<link[^>]+href="([^"]+)"', blk, re.I)
            link = m.group(1) if m else ''
        fecha = None
        raw = g('pubDate') or g('updated') or g('published')
        try:
            fecha = parsedate_to_datetime(raw).strftime('%Y-%m-%d')
        except Exception:
            if _fecha_ok(raw):
                fecha = raw[:10]
        out.append({'titulo': g('title'), 'texto': g('description') or g('summary'), 'url': link, 'fecha': fecha})
    return out


def _url_segura(u):
    return u if u and urlparse(u).scheme in ('http', 'https') else ''


def _nivel_gov(it, fuente):
    u, tt = (it.get('url') or '').lower(), norm(it.get('titulo', ''))
    n = 3
    if '-ale-' in u or '/alerte/' in u or tt.startswith('alerte'):
        n = 8
    elif '-avi-' in u or '/avis/' in u:
        n = 4
    elif '/cti/' in u or '-cti-' in u:
        n = 5
    if re.search(r'critique|urgence attentat|ransomware|rancongiciel|exploit\w* activement|attentat|menace terroriste', tt):
        n += 2
    return min(10, n)


class ExtractorNoticias:
    def __init__(self, fuentes, sens=None):
        self.fuentes = fuentes
        self.sens = sens or SENSIBILIDAD
        self.disc = URLAutoDiscoverer()

    # ---- cosecha: lógica v1 (article + div.class + h1-h4), con protección contra contenedores gigantes
    def cosechar(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        elementos = []
        elementos.extend(soup.find_all('article'))
        elementos.extend(soup.find_all('div', class_=re.compile(r'article|story|post|news|entry', re.I)))
        elementos.extend(soup.find_all(['h1', 'h2', 'h3', 'h4']))
        items, vistos = [], set()
        for elem in elementos:
            if len(items) >= MAX_ELEMENTOS:
                break
            texto = limpiar(elem.get_text(' '))
            if len(texto) < 40:                                   # v1
                continue
            if elem.name in ('div', 'article') and (len(texto) > 1500 or len(elem.find_all(['article', 'h2', 'h3'])) > 3):
                continue                                          # contenedor de página entera, no una noticia
            is_h = elem.name in ('h1', 'h2', 'h3', 'h4')
            head = elem if is_h else elem.find(['h1', 'h2', 'h3', 'h4'])
            titulo = limpiar(head.get_text(' ')) if head is not None else ''
            if len(titulo) < 20:
                titulo = texto[:220]
            key = norm(titulo)[:120]
            if key in vistos:
                continue
            vistos.add(key)
            a = elem if elem.name == 'a' else None
            if a is None and head is not None:
                a = head.find('a', href=True) or head.find_parent('a')
            if a is None:
                a = elem.find('a', href=True) or elem.find_parent('a')
            href = urljoin(url, a['href']) if a is not None and a.get('href') else ''
            tm = elem.find('time')
            if tm is None:
                par = elem.find_parent('article')
                tm = par.find('time') if par is not None else None
            fecha = tm.get('datetime', '')[:10] if tm is not None and tm.get('datetime') else None
            if not _fecha_ok(fecha):
                fecha = _fecha_desde_url(href)
            items.append({'titulo': titulo[:500], 'texto': texto[:900], 'url': href, 'fecha': fecha})
        return items

    def _evento(self, fuente, it, rej):
        titulo = limpiar(it['titulo'])
        if not (20 <= len(titulo) <= 400):
            rej['nav'] += 1
            return None
        _id = hashlib.md5(norm(titulo)[:200].encode()).hexdigest()[:16]
        teaser = it.get('texto', '')[:350]
        geo = geolocalizar(titulo + ' ' + teaser, dep_code_fuente(fuente), _id)
        r = clasificar_detalle(titulo, teaser, self.sens, geo['precision'])
        if 'reject' in r:
            rej[r['reject']] += 1
            return None
        hoy = datetime.now().strftime('%Y-%m-%d')
        fecha = it.get('fecha') if _fecha_ok(it.get('fecha')) else hoy
        fecha = min(fecha[:10], hoy)
        url = _url_segura(it.get('url'))
        return {'id': _id, 'titulo': titulo[:500], 'fecha': fecha, 'tipo': r['tipo'], 'categoria': r['cat'], 'fuente': fuente['nombre'],
                'severidad': r['sev'], 'confianza': r['conf'], 'url': url,
                'fuentes': [{'n': fuente['nombre'], 'u': url, 'f': fecha}],
                'conflicto': es_conflicto(r['tipo'], r['cat'], r['sev'], r['conf']), 'v': SCHEMA, **geo}

    def _alerta(self, fuente, it, rej):
        titulo = limpiar(it['titulo'])
        if len(titulo) < 25 or len(titulo) > 400 or (_NAV.search(norm(titulo)) and len(titulo) <= 45):
            rej['nav'] += 1
            return None
        if fuente.get('filtro') and not re.search(fuente['filtro'], norm(titulo + ' ' + it.get('texto', '')[:300])):
            rej['sin_keyword'] += 1
            return None
        url = _url_segura(it.get('url'))
        hoy = datetime.now().strftime('%Y-%m-%d')
        fecha = it.get('fecha') if _fecha_ok(it.get('fecha')) else hoy
        return {'id': hashlib.md5(('gov' + norm(titulo)[:200]).encode()).hexdigest()[:16], 'titulo': titulo[:300], 'fecha': min(fecha[:10], hoy),
                'url': url, 'fuente': fuente['nombre'], 'ctx': fuente.get('ctx', 'crime'), 'nivel': _nivel_gov(it, fuente)}

    def extraer_de_fuente(self, fuente, paginas=PAGINAS_BUSQUEDA, stop=None):
        """-> (eventos, alertas, info). Dos intentos y se sigue; si cambia de dominio/sección se auto-descubre la URL nueva."""
        t0 = time.time()
        deadline = t0 + PRESUPUESTO_FUENTE
        info = {'nombre': fuente['nombre'], 'kind': '', 'n': 0, 'cand': 0, 'rej': Counter(), 'url_nueva': None, 'note': '', 'dur': 0}
        es_gov = fuente.get('tipo') == 'gov'
        eventos, alertas, vistos_ids = [], [], set()

        def procesar(items):
            n0 = len(eventos) + len(alertas)
            for it in items:
                if es_gov:
                    a = self._alerta(fuente, it, info['rej'])
                    if a and a['id'] not in vistos_ids:
                        vistos_ids.add(a['id']); alertas.append(a)
                else:
                    e = self._evento(fuente, it, info['rej'])
                    if e and e['id'] not in vistos_ids:
                        vistos_ids.add(e['id']); eventos.append(e)
            return len(eventos) + len(alertas) - n0

        def rss(url):
            r, _ = fetch(url, 1)
            its = parse_rss(r.text) if r is not None else []
            info['cand'] += len(its)
            return procesar(its)

        def adoptar(url, nota):
            fuente['url'] = url
            p = urlparse(url)
            fuente['base'] = f'{p.scheme}://{p.netloc}'
            info['url_nueva'] = url
            emit('disc', f"      ↻ {fuente['nombre']}: URL actualizada ({nota}) → {url}")

        try:
            if fuente.get('rss') or fuente.get('rss_auto'):
                rss(fuente.get('rss') or fuente.get('rss_auto'))
            r, kind = fetch(fuente['url'], INTENTOS_ESCANEO)
            if r is not None:                                      # ¿redirigida a otro host/sección?
                pf, po = urlparse(r.url), urlparse(fuente['url'])
                if pf.netloc != po.netloc or pf.path.rstrip('/') != po.path.rstrip('/'):
                    if pf.path.strip('/') == '' and po.path.strip('/') != '':
                        r, kind = None, 'gone'                       # nos mandó a la portada: la sección cambió
                    elif _reg(pf.netloc) == _reg(po.netloc):
                        adoptar(r.url, 'redirección')
            if r is None and kind == 'blocked' and not (stop is not None and stop.is_set()):
                info['kind'] = kind                                # bloqueo = problema del host, no de la URL: solo RSS, sin probar variantes
                if not (eventos or alertas):
                    pu = urlparse(fuente['url']); b0 = f'{pu.scheme}://{pu.netloc}'; u0 = fuente['url'].rstrip('/')
                    probados = {fuente.get('rss'), fuente.get('rss_auto')}
                    for fd in (fuente.get('rss_auto'), b0 + '/feed/', b0 + '/rss.xml', b0 + '/rss', u0 + '/rss', u0 + '/feed/', u0 + '.rss'):
                        if not fd or (fd in probados and fd != fuente.get('rss_auto')) or time.time() > deadline or (stop is not None and stop.is_set()):
                            continue
                        probados.add(fd)
                        n_ant = info['cand']
                        rss(fd)
                        if info['cand'] > n_ant:
                            fuente['rss_auto'] = fd
                            break
                        time.sleep(get_random_delay())
            elif r is None and not (stop is not None and stop.is_set()):
                info['kind'] = kind
                nueva, how = self.disc.discover_url(fuente, kind, deadline)
                if nueva:
                    adoptar(nueva, how)
                    r, kind = fetch(nueva, 1)
            info['kind'] = kind
            if r is None:
                info['note'] = {'dns': 'dominio muerto', 'blocked': 'bloqueada', 'gone': 'URL desaparecida', 'timeout': 'timeout'}.get(kind, kind)
            else:
                hashes = set()
                base_url = fuente['url']
                for pagina in range(1, paginas + 1):
                    if stop is not None and stop.is_set() or time.time() > deadline:
                        break
                    if pagina > 1:
                        r = None
                        for pat in (base_url.rstrip('/') + f'/page/{pagina}/', base_url.rstrip('/') + f'?page={pagina}',
                                    base_url.rstrip('/') + f'/pagina/{pagina}', base_url.rstrip('/') + f'?p={pagina}'):
                            r, _ = fetch(pat, 1)
                            if r is not None:
                                break
                        if r is None:
                            break
                    h = hashlib.md5(r.text.encode('utf-8', 'ignore')).hexdigest()
                    if h in hashes:                                  # misma página repetida
                        break
                    hashes.add(h)
                    its = self.cosechar(r.text, r.url)
                    info['cand'] += len(its)
                    ok_pag = procesar(its)
                    if pagina == 1 and len(its) < 3 and not (fuente.get('rss') or fuente.get('rss_auto')):
                        for fd in self.disc.feeds_de(r.text, r.url)[:1]:      # página sin contenido: usa su RSS
                            ok_pag += rss(fd)
                            fuente['rss_auto'] = fd
                            info['note'] = 'vía RSS'
                    if ok_pag == 0 and pagina > 2:                 # v1
                        break
                    time.sleep(get_random_delay())                  # v1
        except Exception as e:
            logger.warning(f"{fuente['nombre']}: {e}")
            info['kind'] = info['kind'] or 'error'
            info['note'] = str(e)[:60]
        info['n'] = len(eventos) + len(alertas)
        if info['n'] > 0 and info['kind'] != 'ok':                   # la web falló pero el RSS entregó
            info['kind'], info['note'] = 'ok', 'vía RSS (web bloqueada)'
        if info['n'] == 0 and info['kind'] == 'ok':
            info['note'] = info['note'] or ('sin contenido (JS/bloqueo)' if info['cand'] == 0 else 'filtrado: ' + ', '.join(f'{k} {v}' for k, v in info['rej'].most_common(3)))
        info['dur'] = round(time.time() - t0, 1)
        return eventos, alertas, info

# ============================================================================
# ALARMA  (conflictos de calle detectados → SSE → sirena en el panel + campana en la terminal)
# ============================================================================

gestor_global = None
fuentes_global = None
JOB = {'running': False, 'progress': 0.0, 'msg': '', 'added': 0, 'merged': 0, 'total': 0, 'done': 0, 'scope': '', 'mode': '',
       'started': None, 'finished': None}
STOP_EVENT = threading.Event()
_JOB_LOCK = threading.Lock()


def detectar_conflictos(nuevos):
    """Conflictos nuevos: rue ≥ umbral, terrorismo, y clusters (≥3 eventos de calle en 24h en un mismo departamento)."""
    out = [c for c in nuevos if c.get('conflicto') and not gestor_global.alarma_ya_vista(c['id'])]
    hoy = datetime.now()
    ayer = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
    rec = [c for c in gestor_global.copia()[-1000:] if c.get('categoria') == 'rue' and c.get('fecha', '') >= ayer and c.get('dep_code')]
    por_dep = Counter(c['dep_code'] for c in rec)
    dep_nuevos = {c.get('dep_code') for c in nuevos if c.get('categoria') == 'rue'}
    for dep, n in por_dep.items():
        cid = f"cluster:{dep}:{hoy:%Y-%m-%d}"
        if n >= 3 and dep in dep_nuevos and not gestor_global.alarma_ya_vista(cid):
            nm, la, lo = DEPS[dep]
            out.append({'id': cid, 'titulo': f'{n} hechos de violencia armada en 24h — {nm}', 'departement': nm, 'tipo': 'masacre',
                        'severidad': 7, 'lat': la, 'lon': lo})
    return out


def lanzar_alarma(items, test=False):
    ser_items = [{'id': c.get('id'), 'titulo': c.get('titulo', ''), 'dep': c.get('departement', ''), 'tipo': c.get('tipo', ''),
                  'sev': c.get('severidad', 0), 'lat': c.get('lat'), 'lon': c.get('lon')} for c in items][:6]
    gestor_global.registrar_alarma(ser_items, test)
    STATE['alarm_seq'] += 1
    STATE['alarm'] = {'seq': STATE['alarm_seq'], 'items': ser_items, 'test': test, 'ts': datetime.now().isoformat(timespec='seconds')}
    top = ser_items[0] if ser_items else {}
    emit('alarm', f"🚨 {'TEST ' if test else ''}ALARMA — {len(items)} hecho(s): {top.get('titulo', '')[:110]} ({top.get('dep', '')})")


def alarma_test():
    lanzar_alarma([{'id': 'test', 'titulo': 'Prueba de alarma — hecho de violencia armada simulado', 'departement': 'México', 'tipo': 'masacre',
                    'severidad': 7, 'lat': 19.4326, 'lon': -99.1332}], test=True)

# ============================================================================
# ESCÁNER  (secuencial como v1; progreso y log compartidos por terminal y panel)
# ============================================================================

def init_globals(archivo=None):
    global gestor_global, fuentes_global
    gestor_global = GestorDatos(archivo)
    fuentes_global = aplicar_estado(_mk_fuentes())
    v = gestor_global.cfg('umbral')
    if v:
        _set_umbral(int(v))


def _set_umbral(v):
    global UMBRAL_ALARMA
    UMBRAL_ALARMA = max(3, min(10, int(v)))


def seleccionar_fuentes(scope):
    act = [f for f in fuentes_global if f.get('activo', True)]
    if scope == 'fd':
        return [f for f in act if f.get('tipo') == 'faits_divers']
    if scope == 'cyber':
        return [f for f in act if f.get('tipo') == 'cyber']
    if scope == 'gov':
        return [f for f in act if f.get('tipo') == 'gov']
    if scope.startswith('dep:'):
        d = scope[4:]
        return [f for f in act if f.get('departement') == d]
    if scope.startswith('src:'):
        return [f for f in fuentes_global if f['nombre'] == scope[4:]]
    return act


def _resumen_rej(rej):
    return ', '.join(f'{k} {v}' for k, v in rej.most_common(3))


def ejecutar_actualizacion(scope='all', paginas=None, sens=None, interactivo=False):
    with _JOB_LOCK:
        if JOB['running']:
            return False
        JOB.update(running=True, progress=0.0, msg='', added=0, merged=0, total=0, done=0, scope=scope, mode='scan',
                   started=datetime.now().isoformat(timespec='seconds'))
        STOP_EVENT.clear()
        STATE['tick'] += 1
    paginas = max(1, min(8, int(paginas or PAGINAS_BUSQUEDA)))
    sens = sens if sens in _UMBRAL_CONF else SENSIBILIDAD
    t0 = time.time()
    infos, tot_add, tot_merge, tot_alert, tot_conf = [], 0, 0, 0, 0
    try:
        fuentes = seleccionar_fuentes(scope)
        total = len(fuentes)
        JOB['total'] = total
        emit('info', f"\n{'═' * 78}\n🔪 DIABOLIC LATAM — escaneo [{scope}] · {total} sources · {paginas} p · sens={sens}\n{'═' * 78}")
        ext = ExtractorNoticias(fuentes, sens)
        for i, f in enumerate(fuentes, 1):
            if STOP_EVENT.is_set():
                emit('warn', '■ Scan interrompu')
                break
            JOB.update(msg=f['nombre'], done=i - 1, progress=(i - 1) / max(1, total))
            STATE['tick'] += 1
            ev, al, info = ext.extraer_de_fuente(f, paginas, STOP_EVENT)
            res = gestor_global.agregar_crimes(ev)
            nuevas_al = gestor_global.agregar_alertas(al)
            conflictos = detectar_conflictos(res['added'])
            registrar_salud(f, info)
            infos.append(info)
            tot_add += len(res['added']); tot_merge += len(res['merged']); tot_alert += len(nuevas_al)
            JOB.update(added=tot_add, merged=tot_merge, done=i, progress=i / max(1, total))
            dec = f"+{len(res['added'])}" if not al else f"+{len(nuevas_al)} alertas"
            extra = f" · 🔗{len(res['merged'])} confirmados" if res['merged'] else ''
            if info['n'] > 0:
                emit('ok', f"[{i:2d}/{total}] ✔ {f['nombre'][:38]:38} {dec:>10}  ({info['n']} ev · {info['cand']} cand){extra}  {info['dur']}s")
            elif info['kind'] == 'ok':
                emit('warn', f"[{i:2d}/{total}] ◌ {f['nombre'][:38]:38} {'0':>10}  ({info['cand']} cand) {info['note']}  {info['dur']}s")
            else:
                emit('err', f"[{i:2d}/{total}] ✖ {f['nombre'][:38]:38} {info['note'] or info['kind']}  {info['dur']}s")
            if res['added'] or res['merged'] or nuevas_al:
                STATE['version'] += 1
            if conflictos:
                tot_conf += len(conflictos)
                lanzar_alarma(conflictos)
        rej = Counter()
        for x in infos:
            rej.update(x['rej'])
        ceros = [x['nombre'] for x in infos if x['n'] == 0]
        emit('info', f"{'─' * 78}\n🔪 {tot_add} {t('new_events')} · 🔗 {tot_merge} confirmados por otras fuentes · 🏛 {tot_alert} alertas · 🚨 {tot_conf} violencia armada\n"
                     f"⛔ filtrados (falsos positivos evitados): {_resumen_rej(rej) or '-'}\n📰 sin resultados: {len(ceros)}/{len(infos)}   ⏱ {round(time.time() - t0)}s")
    except Exception as e:
        logger.exception(e)
        emit('err', f'scan: {e}')
    finally:
        JOB.update(running=False, progress=1.0, finished=datetime.now().isoformat(timespec='seconds'), msg='')
        STATE['version'] += 1
        STATE['tick'] += 1
    return {'added': tot_add, 'merged': tot_merge, 'alerts': tot_alert, 'infos': infos}


def ejecutar_verificacion():
    with _JOB_LOCK:
        if JOB['running']:
            return False
        JOB.update(running=True, progress=0.0, msg='', added=0, merged=0, total=len(fuentes_global), done=0, scope='verify', mode='verify',
                   started=datetime.now().isoformat(timespec='seconds'))
        STOP_EVENT.clear()
        STATE['tick'] += 1

    def cb(p, nombre, i):
        JOB.update(progress=round(p, 3), msg=nombre, done=i)
        STATE['tick'] += 1
    try:
        VerificadorFuentes().verificar_todas(fuentes_global, progreso=cb, stop=STOP_EVENT)
    except Exception as e:
        logger.exception(e)
        emit('err', f'verify: {e}')
    finally:
        JOB.update(running=False, progress=1.0, finished=datetime.now().isoformat(timespec='seconds'), msg='')
        STATE['version'] += 1
        STATE['tick'] += 1
    return True


def iniciar_scheduler(minutos=None):
    minutos = AUTO_REFRESH_MIN if minutos is None else minutos
    if minutos <= 0:
        return

    def loop():
        while True:
            time.sleep(minutos * 60)
            ejecutar_actualizacion('all')
    threading.Thread(target=loop, daemon=True, name='scheduler').start()


# ============================================================================
# FILTROS + API
# ============================================================================

def filtrar(crimes, periodo='all', cat='all', tipo='', q='', conf=0):
    if periodo in ('24h', '7d', '30d', '90d'):
        dias = 1 if periodo == '24h' else int(periodo[:-1])
        lim = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        crimes = [c for c in crimes if c.get('fecha', '') >= lim]
    if cat in CATEGORIAS:
        crimes = [c for c in crimes if c.get('categoria') == cat]
    if tipo:
        crimes = [c for c in crimes if c.get('tipo') == tipo]
    if conf:
        crimes = [c for c in crimes if c.get('confianza', 0) >= conf]
    if q:
        qn = norm(q)
        crimes = [c for c in crimes if qn in norm(f"{c.get('titulo', '')} {c.get('departement', '')} {c.get('tipo', '')} {c.get('fuente', '')}")]
    return crimes


def _int(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def _args_filtro():
    a = request.args
    return filtrar(gestor_global.copia(), a.get('periodo', 'all'), a.get('cat', 'all'), a.get('tipo', ''), a.get('q', '')[:80], _int(a.get('conf')))


app = Flask(__name__)


@app.after_request
def _headers(r):
    r.headers['X-Content-Type-Options'] = 'nosniff'
    r.headers['Referrer-Policy'] = 'no-referrer'
    return r


def _post_ok():
    """Les POST exigent un en-tête perso (X-DF): une page web tierce ne peut pas déclencher scans/alarmes sur localhost."""
    return request.headers.get('X-DF') == '1'


def _json_body():
    return request.get_json(silent=True) or {}


@app.route('/api/stats')
def api_stats():
    cr = _args_filtro()
    hoy = datetime.now()
    st = gestor_global.estadisticas(cr)
    ms = sorted(st['mensual'])[-18:]
    wt = {k: v for k, v in sorted(st['weekday_type'].items(), key=lambda x: -sum(x[1]))[:12] if k != 'other'}
    street = sorted((c for c in cr if c.get('categoria') == 'rue'), key=lambda c: (c.get('fecha', ''), relevancia(c, hoy)), reverse=True)[:5]
    return jsonify({
        'total': st['total'], 'ultimos_7dias': st['ultimos_7dias'], 'prev_7dias': st['prev_7dias'], 'ultimos_30dias': st['ultimos_30dias'],
        'prev_30dias': st['prev_30dias'], 'ultimos_90dias': st['ultimos_90dias'], 'severidad_promedio': round(st['severidad_promedio'], 2),
        'departements': dict(sorted(st['departements'].items(), key=lambda x: -x[1])[:15]), 'n_departements': len(st['departements']),
        'tipos': dict(st['tipos']), 'fuentes': dict(sorted(st['fuentes'].items(), key=lambda x: -x[1])[:10]),
        'n_fuentes': len([f for f in fuentes_global if f.get('activo', True)]), 'categorias': dict(st['categorias']),
        'mensual': {m: st['mensual'][m] for m in ms}, 'semanal': st['semanal'], 'dept_bubble': st['dept_bubble'],
        'sev_hist': st['sev_hist'], 'weekday_type': wt, 'conflictos_24h': st['conflictos_24h'], 'multi_fuente': st['multi_fuente'],
        'street': [ser(c, hoy) for c in street], 'ultima_actualizacion': gestor_global.datos.get('ultima_actualizacion')})


@app.route('/api/analytics')
def api_analytics():
    return jsonify(Analitica.analytics(_args_filtro()))


@app.route('/api/indicators')
def api_indicators():
    return jsonify(Analitica.indicadores(_args_filtro()))


@app.route('/api/geo')
def api_geo():
    hoy = datetime.now()
    cr = [c for c in _args_filtro() if c.get('lat') is not None]
    cr = sorted(cr, key=lambda c: c.get('fecha', ''), reverse=True)[:4000]
    pts = [[c['lat'], c['lon'], c.get('severidad', 1), c['id'], c['tipo'], c['titulo'][:200], c.get('fecha', ''), c.get('departement', ''),
            c.get('url', ''), c.get('precision', ''), c.get('categoria', 'fisico'), relevancia(c, hoy), len(c.get('fuentes') or []) or 1,
            [[f.get('n', ''), f.get('u', '')] for f in (c.get('fuentes') or [])][:6]] for c in cr]
    dep = Counter(c['dep_code'] for c in cr if c.get('dep_code'))
    return jsonify({'points': pts, 'dept_counts': dep, 'dept_pos': {k: list(v) for k, v in DEPS.items()}, 'hotspots': Analitica.hotspots(cr)})


@app.route('/api/network')
def api_network():
    return jsonify(Analitica.red(_args_filtro()))


@app.route('/api/sankey')
def api_sankey():
    return jsonify(Analitica.sankey(_args_filtro()))


@app.route('/api/crimes')
def api_crimes():
    hoy = datetime.now()
    cr = _args_filtro()
    sort = request.args.get('sort', 'date')
    if sort == 'rel':
        cr = sorted(cr, key=lambda c: (relevancia(c, hoy), c.get('fecha', '')), reverse=True)
    elif sort == 'sev':
        cr = sorted(cr, key=lambda c: (c.get('severidad', 0), c.get('fecha', '')), reverse=True)
    else:
        cr = sorted(cr, key=lambda c: (c.get('fecha', ''), relevancia(c, hoy)), reverse=True)
    per = max(1, min(50, _int(request.args.get('per'), 15)))
    page = max(1, _int(request.args.get('page'), 1))
    pages = max(1, math.ceil(len(cr) / per))
    page = min(page, pages)
    return jsonify({'items': [ser(c, hoy) for c in cr[(page - 1) * per: page * per]], 'page': page, 'total_pages': pages, 'total': len(cr)})


@app.route('/api/alerts')
def api_alerts():
    cat = request.args.get('cat', 'all')
    ctx = 'cyber' if cat == 'cyber' else 'crime' if cat in ('fisico', 'rue') else 'all'
    items = gestor_global.alertas(ctx)[:40]
    return jsonify({'items': items, 'ctx': ctx, 'vigipirate': gestor_global.cfg('vigipirate', {'nivel': 0})})


@app.route('/api/sources')
def api_sources():
    out = []
    for f in fuentes_global:
        e = ESTADO['fuentes'].get(f['nombre'], {})
        out.append({'nombre': f['nombre'], 'url': f['url'], 'tipo': f.get('tipo'), 'ctx': f.get('ctx'), 'departement': f.get('departement'),
                    'activo': f.get('activo', True), 'rss': f.get('rss') or f.get('rss_auto') or '', 'last': e.get('last'), 'fails': e.get('fails', 0)})
    return jsonify({'sources': out})


@app.route('/api/status')
def api_status():
    return jsonify({'job': JOB, 'version': STATE['version']})


@app.route('/stream')
def stream():
    def gen():
        last_tick, last_log = -1, max(0, _LOG_SEQ[0] - 40)
        while True:
            if STATE['tick'] != last_tick:
                last_tick = STATE['tick']
                with _LOG_LOCK:
                    nuevos = [e for e in LOG if e['i'] > last_log]
                if nuevos:
                    last_log = nuevos[-1]['i']
                payload = {'version': STATE['version'], 'job': dict(JOB), 'log': nuevos, 'alarm': STATE['alarm']}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            else:
                yield ': ka\n\n'
            time.sleep(1.0)
    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


_SCOPE_RX = re.compile(r'^(?:all|fd|cyber|gov|dep:.{1,60}|src:.{1,100})$')


@app.route('/api/scan', methods=['POST'])
def api_scan():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    b = _json_body()
    scope = str(b.get('scope', 'all'))
    if not _SCOPE_RX.match(scope):
        return jsonify({'started': False, 'error': 'scope'}), 400
    if JOB['running']:
        return jsonify({'started': False, 'running': True})
    threading.Thread(target=ejecutar_actualizacion, args=(scope, _int(b.get('paginas'), PAGINAS_BUSQUEDA), b.get('sens')), daemon=True).start()
    return jsonify({'started': True})


@app.route('/actualizar', methods=['POST'])         # compat v2
def actualizar():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    if JOB['running']:
        return jsonify({'started': False, 'running': True})
    threading.Thread(target=ejecutar_actualizacion, args=('all',), daemon=True).start()
    return jsonify({'started': True})


@app.route('/api/scan/stop', methods=['POST'])
def api_scan_stop():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    STOP_EVENT.set()
    emit('warn', '■ Stop demandé…')
    return jsonify({'ok': True})


@app.route('/api/verify', methods=['POST'])
def api_verify():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    if JOB['running']:
        return jsonify({'started': False, 'running': True})
    threading.Thread(target=ejecutar_verificacion, daemon=True).start()
    return jsonify({'started': True})


@app.route('/api/sources/toggle', methods=['POST'])
def api_src_toggle():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    n = _json_body().get('nombre')
    for f in fuentes_global:
        if f['nombre'] == n:
            f['activo'] = not f.get('activo', True)
            registrar_salud(f)
            return jsonify({'ok': True, 'activo': f['activo']})
    return jsonify({'ok': False}), 404


@app.route('/api/sources/add', methods=['POST'])
def api_src_add():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    b = _json_body()
    nombre, url = limpiar(str(b.get('nombre', '')))[:80], str(b.get('url', '')).strip()[:300]
    p = urlparse(url)
    if len(nombre) < 2 or p.scheme not in ('http', 'https') or not p.netloc:
        return jsonify({'ok': False, 'error': 'nom/URL invalide'}), 400
    if any(f['nombre'] == nombre for f in fuentes_global):
        return jsonify({'ok': False, 'error': 'déjà existante'}), 400
    tipo = {'faits_divers': ('faits_divers', 'crime'), 'cyber': ('cyber', 'cyber'), 'gov_crime': ('gov', 'crime'), 'gov_cyber': ('gov', 'cyber')}.get(b.get('tipo'), ('faits_divers', 'crime'))
    dep = limpiar(str(b.get('departement') or 'Regional'))[:40]
    f = {'nombre': nombre, 'url': url, 'base': f'{p.scheme}://{p.netloc}', 'departement': dep, 'activo': True, 'tipo': tipo[0], 'ctx': tipo[1]}
    fuentes_global.append(f)
    with _ESTADO_LOCK:
        ESTADO.setdefault('custom', []).append(dict(f))
    registrar_salud(f)
    emit('info', f'＋ Source ajoutée: {nombre}')
    return jsonify({'ok': True})


@app.route('/api/vigipirate', methods=['POST'])
def api_vig():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    n = max(0, min(3, _int(_json_body().get('nivel'))))
    gestor_global.set_cfg('vigipirate', {'nivel': n, 'ts': datetime.now().strftime('%Y-%m-%d %H:%M')})
    return jsonify({'ok': True})


@app.route('/api/alarm/test', methods=['POST'])
def api_alarm_test():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    alarma_test()
    return jsonify({'ok': True})


@app.route('/api/alarm/config', methods=['POST'])
def api_alarm_cfg():
    if not _post_ok():
        return jsonify({'error': 'forbidden'}), 403
    _set_umbral(_int(_json_body().get('umbral'), UMBRAL_ALARMA))
    gestor_global.set_cfg('umbral', UMBRAL_ALARMA)
    emit('info', f'🔔 Seuil alarme = {UMBRAL_ALARMA}')
    return jsonify({'ok': True, 'umbral': UMBRAL_ALARMA})


@app.route('/api/alarm/history')
def api_alarm_hist():
    return jsonify({'items': gestor_global.datos.get('alarma_hist', [])[:30]})


@app.route('/graph/<kind>.png')
def graph_png(kind):
    if kind not in ('tipos', 'mensual', 'heatmap', 'hexbin', 'red'):
        return Response('not found', status=404)
    png = render_estatico(kind, _args_filtro(), request.args.get('lang', 'es'))
    if not png:
        return Response('missing dependency', status=501)
    return Response(png, mimetype='image/png', headers={'Cache-Control': 'no-store'})


@app.route('/exportar/<fmt>')
def exportar(fmt):
    g = gestor_global
    m = {'json': (g.exportar_json, 'application/json'), 'csv': (g.exportar_csv, 'text/csv'),
         'html': (g.exportar_html, 'text/html'), 'geojson': (g.exportar_geojson, 'application/geo+json')}
    if fmt not in m:
        return Response('not found', status=404)
    return Response(m[fmt][0](), mimetype=m[fmt][1], headers={'Content-Disposition': f'attachment; filename=diabolic_narco.{fmt}'})


@app.route('/')
def home():
    i18n = json.dumps(TEXTOS, ensure_ascii=False)
    tipos = json.dumps({k: {'i': v['icono'], 'c': v['color'], 'cat': v['cat'], 'n': {l: v[l] for l in LANGS}} for k, v in TIPOS_CRIMEN.items()}, ensure_ascii=False)
    cfg = json.dumps({'umbral': UMBRAL_ALARMA, 'auto': AUTO_REFRESH_MIN, 'sens': SENSIBILIDAD})
    h = HTML_TEMPLATE.replace('__I18N__', i18n).replace('__TYPES__', tipos).replace('__CFG__', cfg) \
        .replace('__LANG__', IDIOMA_ACTUAL or 'es')
    return Response(h, mimetype='text/html')

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DIABOLIC LATAM</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.css">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800;900&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-chart-sankey@0.12.1/dist/chartjs-chart-sankey.min.js"></script>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
@property --a{syntax:'<angle>';initial-value:0deg;inherits:false}
:root{--bg:#03050c;--cy:#00e5ff;--mg:#ff2bd6;--vi:#8b5cff;--gn:#2bffb4;--rd:#ff2d55;--am:#ffb800;--bl:#2f6bff;--tx:#e6f4ff;--mut:#7f93b5;--bd:#16304f;--glass:rgba(8,18,38,.72)}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Rajdhani','Segoe UI',system-ui,sans-serif;font-size:16px;color:var(--tx);min-height:100vh;
 background:radial-gradient(1100px 600px at 8% -10%,rgba(0,229,255,.13),transparent 60%),radial-gradient(900px 600px at 100% 0,rgba(255,43,214,.11),transparent 60%),radial-gradient(700px 500px at 50% 120%,rgba(139,92,255,.16),transparent 60%),var(--bg);overflow-x:hidden}
body:before{content:'';position:fixed;left:-20%;right:-20%;bottom:-8vh;height:52vh;pointer-events:none;z-index:0;
 background:linear-gradient(to bottom,transparent,rgba(0,229,255,.10)),repeating-linear-gradient(90deg,rgba(0,229,255,.16) 0 1px,transparent 1px 64px),repeating-linear-gradient(0deg,rgba(0,229,255,.16) 0 1px,transparent 1px 64px);
 transform:perspective(520px) rotateX(62deg);transform-origin:50% 100%;-webkit-mask:linear-gradient(to top,#000 10%,transparent 85%);mask:linear-gradient(to top,#000 10%,transparent 85%)}
body:after{content:'';position:fixed;inset:0;pointer-events:none;z-index:300;background:repeating-linear-gradient(0deg,rgba(255,255,255,.028) 0 1px,transparent 1px 3px);mix-blend-mode:overlay}
.wrap{position:relative;z-index:1;max-width:1560px;margin:0 auto;padding:14px 16px 40px}
/* ===== HOLO FRAME ===== */
.holo{position:relative;background:linear-gradient(160deg,rgba(10,24,48,.80),rgba(5,11,24,.74));border-radius:14px;backdrop-filter:blur(9px);-webkit-backdrop-filter:blur(9px);box-shadow:0 0 24px rgba(0,229,255,.06),inset 0 0 30px rgba(0,229,255,.03)}
.holo:before{content:'';position:absolute;inset:0;border-radius:inherit;padding:1px;pointer-events:none;
 background:conic-gradient(from var(--a),var(--cy),var(--vi),var(--mg),var(--vi),var(--cy));
 -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box exclude,linear-gradient(#000 0 0);animation:spin 9s linear infinite;opacity:.75}
.holo:after{content:'';position:absolute;inset:-1px;border-radius:inherit;pointer-events:none;
 background:linear-gradient(var(--cy),var(--cy)) top left/16px 2px no-repeat,linear-gradient(var(--cy),var(--cy)) top left/2px 16px no-repeat,
 linear-gradient(var(--mg),var(--mg)) top right/16px 2px no-repeat,linear-gradient(var(--mg),var(--mg)) top right/2px 16px no-repeat,
 linear-gradient(var(--mg),var(--mg)) bottom left/16px 2px no-repeat,linear-gradient(var(--mg),var(--mg)) bottom left/2px 16px no-repeat,
 linear-gradient(var(--cy),var(--cy)) bottom right/16px 2px no-repeat,linear-gradient(var(--cy),var(--cy)) bottom right/2px 16px no-repeat;filter:drop-shadow(0 0 5px var(--cy))}
@keyframes spin{to{--a:360deg}}
@keyframes sheen{to{background-position:300% 0}}
@keyframes flick{0%,100%{opacity:1}91%{opacity:1}92%{opacity:.7}93%{opacity:1}95%{opacity:.85}96%{opacity:1}}
@keyframes pulse{0%{transform:scale(.6);opacity:.9}100%{transform:scale(2.6);opacity:0}}
@keyframes blink{50%{opacity:.25}}
@keyframes tape{to{transform:translateX(-50%)}}
@keyframes hue{to{filter:hue-rotate(360deg)}}
.hl{background:linear-gradient(90deg,var(--cy),#fff,var(--mg),var(--cy));background-size:300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:sheen 7s linear infinite}
/* ===== HEADER ===== */
.hud{z-index:500;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;padding:14px 20px;margin-bottom:10px}
.brand{display:flex;align-items:center;gap:14px}
.logo{font-family:Orbitron,monospace;font-weight:900;font-size:1.9em;letter-spacing:6px;animation:flick 5s infinite;white-space:nowrap}
.logo small{font-size:.35em;letter-spacing:3px;display:block;color:var(--mut);font-weight:500;margin-top:2px;-webkit-text-fill-color:var(--mut)}
.flag{display:flex;height:34px;width:8px;border-radius:3px;overflow:hidden;flex-direction:column;box-shadow:0 0 12px rgba(0,229,255,.6)}
.flag i{flex:1}.flag i:nth-child(1){background:#ffd100}.flag i:nth-child(2){background:#0033a0}.flag i:nth-child(3){background:#ce1126}
.leds{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.led{display:flex;align-items:center;gap:6px;font-size:.78em;letter-spacing:1.4px;text-transform:uppercase;color:var(--mut)}
.led i{width:9px;height:9px;border-radius:50%;background:#394a66;box-shadow:0 0 0 0 transparent}
.led.on i{background:var(--gn);box-shadow:0 0 10px var(--gn)}
.led.warn i{background:var(--am);box-shadow:0 0 10px var(--am)}
.led.bad i{background:var(--rd);box-shadow:0 0 12px var(--rd);animation:blink .7s infinite}
.led.run i{background:var(--cy);box-shadow:0 0 12px var(--cy);animation:blink .9s infinite}
select,input[type=text],input[type=url],input[type=number]{background:rgba(3,10,22,.85);color:var(--tx);border:1px solid var(--bd);border-radius:10px;padding:8px 12px;font:inherit;font-size:.92em}
select:focus,input:focus{outline:none;border-color:var(--cy);box-shadow:0 0 12px rgba(0,229,255,.3)}
.btn{position:relative;background:linear-gradient(180deg,rgba(0,229,255,.16),rgba(0,229,255,.04));color:var(--tx);border:1px solid rgba(0,229,255,.5);border-radius:10px;padding:7px 14px;font:inherit;font-weight:600;font-size:.88em;letter-spacing:.8px;cursor:pointer;transition:.18s;white-space:nowrap;text-decoration:none;display:inline-flex;gap:6px;align-items:center}
.btn:hover{box-shadow:0 0 16px rgba(0,229,255,.5);transform:translateY(-1px);background:rgba(0,229,255,.22)}
.btn:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}
.btn.red{border-color:rgba(255,45,85,.6);background:linear-gradient(180deg,rgba(255,45,85,.25),rgba(255,45,85,.05))}.btn.red:hover{box-shadow:0 0 16px rgba(255,45,85,.6)}
.btn.mg{border-color:rgba(255,43,214,.55);background:linear-gradient(180deg,rgba(255,43,214,.2),rgba(255,43,214,.04))}.btn.mg:hover{box-shadow:0 0 16px rgba(255,43,214,.55)}
.btn.sm{padding:4px 9px;font-size:.78em}
.job{width:100%;display:none;gap:12px;align-items:center;font-size:.82em;color:var(--mut)}.job.on{display:flex}
.bar{flex:1;height:5px;background:#0b1a30;border-radius:5px;overflow:hidden}.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--cy),var(--mg));box-shadow:0 0 12px var(--cy);transition:width .4s}
/* ===== TICKER TAPE ===== */
.tapebox{overflow:hidden;white-space:nowrap;padding:7px 0;margin-bottom:10px;border-radius:10px}
.tape-in{display:inline-flex;gap:30px;animation:tape 70s linear infinite;padding-left:20px}
.tapebox:hover .tape-in{animation-play-state:paused}
.tk{display:inline-flex;align-items:center;gap:7px;font-size:.92em}
.tk b{color:var(--cy);letter-spacing:1.2px;font-weight:700}.tk i{font-style:normal;font-family:Orbitron,monospace;font-size:.85em}
.tk em{font-style:normal;font-weight:700}.tk em.up{color:var(--rd)}.tk em.dn{color:var(--gn)}.tk em.fl{color:var(--mut)}
.arw{display:inline-block;width:11px;height:12px;background:linear-gradient(120deg,var(--cy),#fff,var(--mg),var(--cy));background-size:300% 300%;animation:sheen 3s linear infinite;filter:drop-shadow(0 0 4px currentColor)}
.arw.up{clip-path:polygon(50% 0,100% 100%,50% 72%,0 100%);filter:drop-shadow(0 0 5px var(--rd)) hue-rotate(-40deg)}
.arw.dn{clip-path:polygon(50% 100%,100% 0,50% 28%,0 0);filter:drop-shadow(0 0 5px var(--gn)) hue-rotate(60deg)}
.arw.fl{clip-path:polygon(0 40%,70% 40%,70% 15%,100% 50%,70% 85%,70% 60%,0 60%);opacity:.7}
.spk{vertical-align:middle}
/* ===== GOV BAR ===== */
.gov{display:flex;gap:14px;align-items:center;padding:8px 14px;margin-bottom:10px;font-size:.9em;overflow:hidden}
.gov .tag{font-family:Orbitron,monospace;font-size:.7em;letter-spacing:2px;padding:3px 10px;border-radius:6px;background:linear-gradient(90deg,var(--bl),var(--rd));color:#fff;white-space:nowrap}
.gov .items{flex:1;display:flex;gap:22px;overflow-x:auto;scrollbar-width:none;white-space:nowrap}
.gov .items::-webkit-scrollbar{display:none}
.gov a{color:var(--tx);text-decoration:none}.gov a:hover{color:var(--cy)}
.gov .it{display:inline-flex;gap:7px;align-items:center}
.gov .it u{text-decoration:none;font-size:.7em;letter-spacing:1px;padding:1px 7px;border-radius:5px;border:1px solid}
.gov .it u.cyber{color:var(--cy);border-color:var(--cy)}.gov .it u.crime{color:var(--am);border-color:var(--am)}
.gov .it.hi a{color:#ff8da1}
.vig{padding:3px 10px;border-radius:7px;border:1px solid;font-size:.78em;letter-spacing:1px;white-space:nowrap;cursor:pointer;background:transparent;color:inherit;font-family:inherit}
.vig.l1{color:var(--gn)}.vig.l2{color:var(--am)}.vig.l3{color:var(--rd);animation:blink 1.4s infinite}.vig.l0{color:var(--mut)}
/* ===== TOOLBAR / TABS / FILTERS ===== */
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;align-items:center}
.tools .sep{width:1px;height:22px;background:var(--bd);margin:0 4px}
.tabs{position:sticky;top:0;z-index:60;display:flex;gap:4px;overflow-x:auto;padding:6px;margin-bottom:10px;border-radius:12px;background:rgba(3,8,18,.86);backdrop-filter:blur(10px);border:1px solid var(--bd)}
.tab-btn{background:transparent;border:0;color:var(--mut);padding:9px 18px;border-radius:9px;font:inherit;font-weight:700;letter-spacing:1px;font-size:.92em;cursor:pointer;white-space:nowrap;text-transform:uppercase}
.tab-btn.on{color:#fff;background:rgba(0,229,255,.12);box-shadow:inset 0 -2px 0 var(--cy),0 0 18px rgba(0,229,255,.2)}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
.grp{display:flex;gap:5px;padding-right:12px;margin-right:4px;border-right:1px solid var(--bd)}
.chip{background:rgba(5,14,30,.8);color:var(--mut);border:1px solid var(--bd);border-radius:18px;padding:4px 13px;font-size:.82em;cursor:pointer;font-weight:600;letter-spacing:.6px;transition:.15s}
.chip:hover{color:var(--tx);border-color:var(--cy)}
.chip.on{background:rgba(0,229,255,.18);border-color:var(--cy);color:#fff;box-shadow:0 0 12px rgba(0,229,255,.35)}
.chip[data-v=fisico].on{background:rgba(255,45,85,.2);border-color:var(--rd);box-shadow:0 0 12px rgba(255,45,85,.4)}
.chip[data-v=rue].on{background:rgba(255,184,0,.2);border-color:var(--am);box-shadow:0 0 12px rgba(255,184,0,.4)}
.tab{display:none}.tab.on{display:block}
/* ===== GRID / CARDS ===== */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:12px;margin-bottom:14px}
.kpi{padding:12px 15px}.kpi small{color:var(--mut);font-size:.72em;text-transform:uppercase;letter-spacing:1.2px;display:block}
.kpi b{font-family:Orbitron,monospace;font-size:1.65em;display:inline-block;margin-top:3px}
.kpi .d{font-size:.78em;margin-left:6px;font-weight:700}.d.up{color:var(--rd)}.d.dn{color:var(--gn)}.d.fl{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:14px;margin-bottom:14px}
.card{padding:16px 16px 14px}.card h3{font-family:Orbitron,monospace;font-size:.7em;letter-spacing:2px;color:var(--cy);text-transform:uppercase;margin-bottom:10px;font-weight:500}
.card .cv{position:relative;height:250px}.card.wide{grid-column:1/-1}
.row2{display:grid;grid-template-columns:minmax(300px,1fr) 2fr;gap:14px;margin-bottom:14px}
@media(max-width:900px){.row2{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.logo{font-size:1.3em;letter-spacing:3px}}
.gauge{display:flex;flex-direction:column;align-items:center}
.gauge svg{width:100%;max-width:310px}.gauge .gl{font-family:Orbitron,monospace;letter-spacing:3px;font-size:.95em;margin-top:-8px}
.ind{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px;width:100%}
.ind div{background:rgba(0,229,255,.05);border:1px solid var(--bd);border-radius:10px;padding:7px 9px;text-align:center}
.ind small{display:block;color:var(--mut);font-size:.68em;letter-spacing:1.2px;text-transform:uppercase}.ind b{font-family:Orbitron,monospace;font-size:1.05em}
.sig{padding:2px 12px;border-radius:8px;font-family:Orbitron,monospace;font-size:.8em;letter-spacing:1.5px;border:1px solid}
.sig.up{color:var(--rd);border-color:var(--rd);box-shadow:0 0 12px rgba(255,45,85,.4)}.sig.dn{color:var(--gn);border-color:var(--gn);box-shadow:0 0 12px rgba(43,255,180,.35)}.sig.fl{color:var(--mut);border-color:var(--bd)}
/* ===== LISTS ===== */
.item{position:relative;background:rgba(2,8,20,.7);border:1px solid var(--bd);border-left:3px solid var(--rd);border-radius:11px;padding:10px 14px;margin-bottom:8px;transition:.18s;display:flex;gap:12px;align-items:center}
.item:hover{transform:translateX(4px);background:rgba(0,229,255,.06);box-shadow:0 0 18px rgba(0,229,255,.12)}
.item .tt{flex:1;min-width:0}.item a.t{color:var(--tx);text-decoration:none;font-weight:700;font-size:1.02em;line-height:1.25}.item a.t:hover{color:var(--cy)}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;font-size:.76em;color:var(--mut);align-items:center}
.badge{border:1px solid var(--bd);border-radius:14px;padding:1px 9px;background:rgba(3,10,22,.8)}
.srcs a{color:var(--cy);text-decoration:none;border:1px solid rgba(0,229,255,.35);border-radius:12px;padding:1px 8px;font-size:.95em}.srcs a:hover{background:rgba(0,229,255,.15)}
.ring{width:46px;height:46px;flex:none}
.ring text{font-family:Orbitron,monospace;font-size:13px;fill:var(--tx)}
.alert{display:flex;justify-content:space-between;gap:10px;padding:7px 10px;border-radius:9px;background:rgba(255,45,85,.08);border:1px solid rgba(255,45,85,.35);margin-bottom:6px;font-size:.88em}
.alert.ok{background:rgba(43,255,180,.07);border-color:rgba(43,255,180,.3);color:var(--gn)}
.hli{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--bd);font-size:.9em}
.cloud{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;min-height:190px;align-content:flex-start}.cloud span{font-weight:700;cursor:default}
.hm{border-collapse:collapse;width:100%;font-size:.78em}.hm td,.hm th{padding:4px 6px;text-align:center}.hm th{color:var(--mut);font-weight:600}.hm td.l{text-align:left;white-space:nowrap}
.pager{display:flex;justify-content:center;align-items:center;gap:14px;margin:14px 0;color:var(--mut);font-size:.9em}
.empty{color:var(--mut);text-align:center;padding:26px}
/* ===== MAP ===== */
#map{isolation:isolate;height:70vh;border-radius:12px;border:1px solid var(--bd);background:#050a14}
.maptools{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;align-items:center}.note{color:var(--mut);font-size:.78em;margin-left:auto}
.leaflet-container{font-family:inherit}.leaflet-control-layers,.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:rgba(6,14,30,.94)!important;color:var(--tx)!important;border:1px solid var(--cy);box-shadow:0 0 18px rgba(0,229,255,.3)!important}
.leaflet-popup-content{margin:10px 12px;font-size:.95em;line-height:1.35}.leaflet-popup-content a{color:var(--cy)}
.leaflet-marker-icon.pulse{position:absolute}.pulse i{position:absolute;inset:0;border-radius:50%;background:var(--am);box-shadow:0 0 14px var(--am)}.pulse:before{content:'';position:absolute;inset:0;border-radius:50%;border:2px solid var(--am);animation:pulse 1.6s infinite}
.pulse.hi i{background:var(--rd);box-shadow:0 0 16px var(--rd)}.pulse.hi:before{border-color:var(--rd)}
.relbar{height:4px;background:#0b1a30;border-radius:4px;overflow:hidden;margin:5px 0}.relbar i{display:block;height:100%;background:linear-gradient(90deg,var(--cy),var(--mg))}
#tlLbl{color:var(--cy);font-family:Orbitron,monospace;font-size:.85em}
#net{height:66vh;border:1px solid var(--bd);border-radius:12px;background:rgba(2,6,14,.8)}
.statics{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:14px}.statics img{width:100%;border-radius:8px;display:block;background:#0b0f1a;min-height:150px}
/* ===== SCAN CENTER ===== */
.scan-grid{display:grid;grid-template-columns:minmax(330px,1fr) 1.6fr;gap:14px}@media(max-width:1000px){.scan-grid{grid-template-columns:1fr}}
.ctl{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;align-items:center}.ctl label{color:var(--mut);font-size:.8em;letter-spacing:1px;text-transform:uppercase}
#console{height:300px;overflow:auto;background:rgba(0,4,10,.9);border:1px solid var(--bd);border-radius:10px;padding:10px;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace}
#console div{white-space:pre-wrap;word-break:break-word}.l-ok{color:var(--gn)}.l-warn{color:var(--am)}.l-err{color:var(--rd)}.l-info{color:var(--cy)}.l-dim{color:#566a8a}.l-alarm{color:#fff;background:var(--rd);padding:0 6px}.l-disc{color:var(--mg)}
.srctbl{width:100%;border-collapse:collapse;font-size:.86em}.srctbl th{color:var(--mut);text-align:left;font-weight:600;font-size:.78em;letter-spacing:1px;text-transform:uppercase;padding:5px 6px;position:sticky;top:0;background:#071022}
.srctbl td{padding:5px 6px;border-top:1px solid var(--bd);vertical-align:middle}.srctbl a{color:var(--cy);text-decoration:none}
.srcwrap{max-height:540px;overflow:auto;border-radius:10px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#394a66;margin-right:6px}.dot.ok{background:var(--gn);box-shadow:0 0 8px var(--gn)}.dot.warn{background:var(--am);box-shadow:0 0 8px var(--am)}.dot.bad{background:var(--rd);box-shadow:0 0 8px var(--rd)}
.addsrc{display:grid;grid-template-columns:1fr 1.4fr;gap:6px;margin-top:10px}.addsrc input,.addsrc select{width:100%}
/* ===== ALARM ===== */
.alarmbtn{position:relative}.alarmbtn .led{margin-left:2px}
#alarmPanel{position:absolute;right:0;top:44px;z-index:600;width:310px;padding:14px;display:none;background:#070d1c;box-shadow:0 12px 50px rgba(0,0,0,.85),0 0 28px rgba(0,229,255,.25)}#alarmPanel.on{display:block}
#alarmPanel .r{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:9px;font-size:.9em}
#alarmPanel input[type=range]{width:130px;accent-color:var(--cy)}
.ahist{max-height:130px;overflow:auto;font-size:.78em;color:var(--mut);margin-top:6px}.ahist div{border-top:1px solid var(--bd);padding:3px 0}
#alarmOv{position:fixed;left:0;right:0;bottom:0;z-index:400;display:none;padding:14px 22px;background:linear-gradient(90deg,rgba(255,45,85,.96),rgba(255,43,214,.9));color:#fff;align-items:center;gap:16px;box-shadow:0 -6px 60px rgba(255,45,85,.9);animation:blink 1s infinite}
#alarmOv.on{display:flex}#alarmOv b{font-family:Orbitron,monospace;letter-spacing:3px}#alarmOv span{flex:1}
body.alarming .hud:before{animation-duration:1.2s}
footer{text-align:center;color:#4d6285;font-size:.78em;padding:26px;letter-spacing:1px}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}

/* ampliar gráficos */
.card h3.zm{cursor:zoom-in}.card h3.zm:after{content:'⤢';float:right;font-size:1.5em;line-height:.8;opacity:.8;margin-left:8px}.card h3.zm:hover:after{color:var(--mg);opacity:1}
.card .cv canvas,.card .statics img,.card img{cursor:zoom-in}
.card .cv{min-height:250px}
#zoomOv{position:fixed;inset:0;z-index:2000;background:rgba(2,6,14,.9);display:flex;padding:2.5vh 2.5vw}
#zoomOv .zbox{flex:1;display:flex;flex-direction:column;padding:14px 18px;background:#070d1c;min-width:0;min-height:0}
#zoomOv .zh{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;font-family:Orbitron,monospace;letter-spacing:2px;color:var(--cy)}
#zoomOv .zb{flex:1;min-height:0;overflow:auto}#zoomOv .zb .cv{height:100%!important}#zoomOv .zb #net{height:100%!important}
#zoomOv .zb img{display:block;width:auto;max-width:100%;max-height:100%;margin:0 auto;cursor:default}
body.zooming{overflow:hidden}
.leaflet-tooltip.ptip{background:rgba(5,11,24,.96);color:#d7e6ff;border:1px solid var(--cy);border-radius:8px;box-shadow:0 0 18px rgba(0,229,255,.35);max-width:300px;white-space:normal;padding:7px 10px;font:13px Rajdhani,sans-serif;line-height:1.35}
.leaflet-tooltip.ptip small{color:#8aa0c4}.leaflet-tooltip-top.ptip:before{border-top-color:var(--cy)}
</style>
</head>
<body>
<div id="alarmOv"><b>⚠ <span style="display:inline" data-i18n="alarm_conflict"></span></b><span id="alarmTxt"></span><button class="btn sm" id="alarmGo" data-i18n="m_fit"></button><button class="btn sm" id="alarmAck" data-i18n="alarm_ack"></button></div>
<div class="wrap">

<header class="holo hud">
  <div class="brand"><div class="flag"><i></i><i></i><i></i></div>
    <div class="logo"><span class="hl">DIABOLIC LATAM</span><small data-i18n="app_sub"></small></div></div>
  <div class="leds">
    <span class="led" id="ledLive"><i></i><span data-i18n="led_live"></span></span>
    <span class="led" id="ledScan"><i></i><span data-i18n="led_scan"></span></span>
    <span class="led" id="ledGov"><i></i><span data-i18n="led_gov"></span></span>
    <span style="position:relative"><button class="btn alarmbtn" id="alarmBtn"><span class="led" id="ledAlarm"><i></i></span><span data-i18n="alarm"></span></button>
      <div id="alarmPanel" class="holo">
        <div class="r"><b class="hl" data-i18n="alarm"></b><span id="alarmState" class="badge"></span></div>
        <div class="r"><button class="btn sm" id="aArm"></button><button class="btn sm red" id="aTest" data-i18n="alarm_test"></button></div>
        <div class="r"><button class="btn sm" id="aMute" data-i18n="alarm_mute5"></button><button class="btn sm mg" id="aStop" data-i18n="alarm_ack"></button></div>
        <div class="r"><span data-i18n="alarm_vol"></span><input type="range" id="aVol" min="0" max="100" value="60"></div>
        <div class="r"><span data-i18n="alarm_thr"></span><select id="aThr"><option>5</option><option>6</option><option>7</option><option>8</option><option>9</option></select></div>
        <div class="r"><span data-i18n="alarm_sound"></span><select id="aSnd"><option value="siren">Sirène</option><option value="pulse">Pulse</option><option value="klaxon">Klaxon</option></select></div>
        <div class="r"><span data-i18n="alarm_notif"></span><input type="checkbox" id="aNot"></div>
        <small style="color:var(--mut)" id="aHint"></small>
        <b style="font-size:.78em;color:var(--cy);letter-spacing:1px" data-i18n="alarm_hist"></b><div class="ahist" id="aHist"></div>
      </div></span>
    <select id="lang"><option value="es">🇪🇸 Español</option><option value="en">🇬🇧 English</option></select>
  </div>
  <div class="job" id="job"><span id="jobTxt"></span><div class="bar"><i id="jobBar"></i></div><span id="jobPct"></span></div>
</header>

<div class="holo tapebox" id="tape"></div>

<div class="holo gov" id="gov"><span class="tag" data-i18n="gov_alerts"></span><div class="items" id="govItems"></div><button class="vig l0" id="vig"></button></div>

<div class="tools">
  <button class="btn red" data-scan="all">▶ <span data-i18n="btn_scan_all"></span></button>
  <button class="btn" data-scan="fd">🔪 <span data-i18n="btn_scan_fd"></span></button>
  <button class="btn" data-scan="cyber">🛡 <span data-i18n="btn_scan_cyber"></span></button>
  <button class="btn" data-scan="gov">🏛 <span data-i18n="btn_scan_gov"></span></button>
  <button class="btn mg" id="btnStop">■ <span data-i18n="btn_stop"></span></button>
  <button class="btn" id="btnVerify">🔍 <span data-i18n="btn_verify"></span></button>
  <span class="sep"></span>
  <button class="btn" id="btnMute">🔔 <span data-i18n="btn_mute"></span></button>
  <button class="btn" id="btnFull">⛶ <span data-i18n="btn_full"></span></button>
  <button class="btn" id="btnCopy">🔗 <span data-i18n="btn_copy"></span></button>
  <button class="btn" id="btnReset">↺ <span data-i18n="btn_reset"></span></button>
  <a class="btn" href="/exportar/geojson">GeoJSON</a><a class="btn" href="/exportar/csv">CSV</a><a class="btn" href="/exportar/json">JSON</a><a class="btn" href="/exportar/html">HTML</a>
</div>

<nav class="tabs" id="tabs">
  <button class="tab-btn on" data-tab="dash" data-i18n="tab_dash"></button>
  <button class="tab-btn" data-tab="map" data-i18n="tab_map"></button>
  <button class="tab-btn" data-tab="graphs" data-i18n="tab_graphs"></button>
  <button class="tab-btn" data-tab="network" data-i18n="tab_network"></button>
  <button class="tab-btn" data-tab="static" data-i18n="tab_static"></button>
  <button class="tab-btn" data-tab="feed" data-i18n="tab_feed"></button>
  <button class="tab-btn" data-tab="scan" data-i18n="tab_scan"></button>
</nav>
<div class="filters">
  <div class="grp" id="fPer"><span class="chip on" data-v="all" data-i18n="f_all"></span><span class="chip" data-v="24h">24h</span><span class="chip" data-v="7d">7d</span><span class="chip" data-v="30d">30d</span><span class="chip" data-v="90d">90d</span></div>
  <div class="grp" id="fCat"><span class="chip on" data-v="all" data-i18n="cat_all"></span><span class="chip" data-v="fisico" data-i18n="cat_phys"></span><span class="chip" data-v="rue" data-i18n="cat_rue"></span><span class="chip" data-v="cyber" data-i18n="cat_cyber"></span></div>
  <select id="fTipo"></select>
  <input type="text" id="fQ" data-i18n-ph="search_ph">
  <select id="fConf"><option value="0" data-i18n="conf_any"></option><option value="45" data-i18n="conf_med"></option><option value="60" data-i18n="conf_high"></option></select>
</div>

<section class="tab on" id="tab-dash">
  <div class="kpis" id="kpis"></div>
  <div class="row2">
    <div class="holo card gauge"><h3 data-i18n="threat_idx"></h3><div id="gauge" style="width:100%"></div><div class="ind" id="ind"></div></div>
    <div class="holo card"><h3 data-i18n="c_boll"></h3><div class="cv" style="height:330px"><canvas id="chBoll"></canvas></div></div>
  </div>
  <div class="grid">
    <div class="holo card"><h3 data-i18n="c_street"></h3><div id="streetList"></div></div>
    <div class="holo card"><h3 data-i18n="c_toprel"></h3><div id="topRel"></div></div>
    <div class="holo card"><h3 data-i18n="c_dept"></h3><div class="cv"><canvas id="chDept"></canvas></div></div>
    <div class="holo card"><h3 data-i18n="c_types"></h3><div class="cv"><canvas id="chTypes"></canvas></div></div>
    <div class="holo card wide"><h3 data-i18n="c_monthly"></h3><div class="cv"><canvas id="chMonthly"></canvas></div></div>
    <div class="holo card"><h3 data-i18n="c_radar"></h3><div class="cv"><canvas id="chRadar"></canvas></div></div>
    <div class="holo card"><h3 data-i18n="c_sev"></h3><div class="cv"><canvas id="chSev"></canvas></div></div>
    <div class="holo card"><h3 data-i18n="c_forecast"></h3><div class="cv"><canvas id="chFore"></canvas></div></div>
    <div class="holo card"><h3 data-i18n="c_anom"></h3><div class="cv"><canvas id="chAnom"></canvas></div></div>
    <div class="holo card wide"><h3 data-i18n="c_weekday"></h3><div id="hm"></div></div>
    <div class="holo card"><h3 data-i18n="c_trend"></h3><div class="cloud" id="cloud"></div></div>
    <div class="holo card"><h3>⚠ <span data-i18n="alerts"></span></h3><div id="alerts"></div><h3 style="margin-top:14px" data-i18n="hotspots_t"></h3><div id="hotl"></div></div>
  </div>
</section>

<section class="tab" id="tab-map">
  <div class="maptools">
    <button class="btn sm" data-fly="-8,-68,3">🌎</button><button class="btn sm" data-fly="23.6,-102.5,5">MX</button><button class="btn sm" data-fly="4.6,-74.1,6">CO</button>
    <button class="btn sm" data-fly="-1.8,-78.2,7">EC</button><button class="btn sm" data-fly="-9.2,-75.0,5">PE</button><button class="btn sm" data-fly="-14.2,-51.9,4">BR</button>
    <button class="btn sm" data-fly="7.1,-66.2,6">VE</button><button class="btn sm" data-fly="15.5,-88.5,6">CA</button><button class="btn sm" data-fly="-34.0,-64.0,4">AR/CL</button>
    <button class="btn sm mg" id="tlBtn">▶ <span data-i18n="m_timelapse"></span></button><span id="tlLbl"></span>
    <button class="btn sm" id="fitBtn">◎ <span data-i18n="m_fit"></span></button>
    <span class="note" id="mapNote"></span>
  </div>
  <div class="holo" style="padding:8px"><div id="map"></div></div>
</section>

<section class="tab" id="tab-graphs"><div class="grid">
  <div class="holo card wide"><h3 data-i18n="c_sankey"></h3><div class="cv" style="height:520px"><canvas id="chSankey"></canvas></div></div>
  <div class="holo card"><h3 data-i18n="c_weekly"></h3><div class="cv"><canvas id="chWeekly"></canvas></div></div>
  <div class="holo card"><h3 data-i18n="c_bubble"></h3><div class="cv"><canvas id="chBubble"></canvas></div></div>
</div></section>
<section class="tab" id="tab-network"><div class="holo card wide"><h3 data-i18n="c_net"></h3><div id="net"></div></div></section>
<section class="tab" id="tab-static"><div class="statics" id="statics"></div></section>
<section class="tab" id="tab-feed"><div class="holo card"><div class="ctl"><label data-i18n="sort_by"></label><select id="fSort"><option value="date" data-i18n="sort_date"></option><option value="rel" data-i18n="sort_rel"></option><option value="sev" data-i18n="sort_sev"></option></select></div><div id="feed"></div><div class="pager" id="pager"></div></div></section>

<section class="tab" id="tab-scan"><div class="scan-grid">
  <div>
    <div class="holo card" style="margin-bottom:14px"><h3 data-i18n="scan_ctl"></h3>
      <div class="ctl"><label data-i18n="scan_pages"></label><select id="sPages"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option></select>
        <label data-i18n="scan_sens"></label><select id="sSens"><option value="amplio" data-i18n="sens_wide"></option><option value="equilibrado" data-i18n="sens_bal" selected></option><option value="estricto" data-i18n="sens_strict"></option></select></div>
      <div class="ctl"><button class="btn red" data-scan="all">▶ <span data-i18n="btn_scan_all"></span></button><button class="btn" data-scan="fd">🔪 <span data-i18n="btn_scan_fd"></span></button><button class="btn" data-scan="cyber">🛡 <span data-i18n="btn_scan_cyber"></span></button><button class="btn" data-scan="gov">🏛 <span data-i18n="btn_scan_gov"></span></button></div>
      <div class="ctl"><label data-i18n="scan_dep"></label><select id="sDep"></select><button class="btn sm" id="sDepGo">▶</button></div>
      <div class="ctl"><label data-i18n="scan_src"></label><select id="sSrc"></select><button class="btn sm" id="sSrcGo">▶</button></div>
      <div class="ctl"><button class="btn mg" id="btnStop2">■ <span data-i18n="btn_stop"></span></button><button class="btn" id="btnVerify2">🔍 <span data-i18n="btn_verify"></span></button></div>
      <small style="color:var(--mut)" data-i18n="scan_note"></small>
    </div>
    <div class="holo card"><h3 data-i18n="scan_console"></h3><div id="console"></div></div>
  </div>
  <div class="holo card"><h3><span data-i18n="scan_sources"></span> · <span id="srcCount"></span></h3>
    <div class="srcwrap"><table class="srctbl"><thead><tr><th></th><th data-i18n="src_name"></th><th data-i18n="src_type"></th><th>#</th><th data-i18n="src_note"></th><th></th></tr></thead><tbody id="srcBody"></tbody></table></div>
    <div class="addsrc"><input type="text" id="nName" data-i18n-ph="src_name"><input type="url" id="nUrl" placeholder="https://..."><input type="text" id="nDep" data-i18n-ph="src_dep">
      <select id="nTipo"><option value="faits_divers">prensa · narco/violencia</option><option value="cyber">análisis · finanzas</option><option value="gov_crime">gov · crime</option><option value="gov_cyber">gov · cyber</option></select></div>
    <div class="ctl" style="margin-top:8px"><button class="btn" id="btnAdd">＋ <span data-i18n="add_source"></span></button></div>
    <h3 style="margin-top:14px" data-i18n="official_links"></h3><div class="ctl" id="offLinks"></div>
  </div>
</div></section>

<footer>🛡 <span data-i18n="motto"></span> · By Condor2026 · •SpectrumSecurity• · <span id="upd"></span></footer>
</div>

<script>
const I18N=__I18N__, TYPES=__TYPES__, CFG=__CFG__, LOC={es:'es-MX',en:'en-GB'};
let LANG=new URLSearchParams(location.search).get('lang')||(()=>{try{return localStorage.getItem('df_lang')}catch(e){return null}})()||'__LANG__';
if(!I18N[LANG])LANG='es';
const S={periodo:'all',cat:'all',tipo:'',q:'',conf:0,sort:'date',page:1,tab:'dash'}, STALE={};
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const lsGet=(k,d)=>{try{const v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}, lsSet=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const T=k=>(I18N[LANG]&&I18N[LANG][k])||I18N.fr[k]||k;
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=u=>/^https?:\/\//i.test(u||'')?u:'';
const tname=t=>TYPES[t]?(TYPES[t].n[LANG]||TYPES[t].n.fr):t, ticon=t=>TYPES[t]?TYPES[t].i:'❓', tcol=t=>TYPES[t]?TYPES[t].c:'#6b7280';
const CATC={fisico:'#ff2d55',rue:'#ffb800',cyber:'#00e5ff'}, catName=c=>T(c==='fisico'?'cat_phys':c==='rue'?'cat_rue':'cat_cyber');
const nf=n=>new Intl.NumberFormat(LOC[LANG]).format(n);
const qs=()=>new URLSearchParams({periodo:S.periodo,cat:S.cat,tipo:S.tipo,q:S.q,conf:S.conf,lang:LANG}).toString();
async function api(p,extra=''){const r=await fetch(p+'?'+qs()+extra);if(!r.ok)throw new Error(p+' '+r.status);return r.json();}
async function post(p,body){const r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json','X-DF':'1'},body:JSON.stringify(body||{})});return r.json().catch(()=>({}));}
const CH={};
function mk(id,cfg){const el=document.getElementById(id);if(!el)return;if(CH[id])CH[id].destroy();CH[id]=new Chart(el,cfg);}
Chart.defaults.color='#8aa0c4';Chart.defaults.borderColor='rgba(40,80,130,.35)';Chart.defaults.font.family="Rajdhani,'Segoe UI',sans-serif";Chart.defaults.maintainAspectRatio=false;Chart.defaults.font.size=13;
const CY='#00e5ff',MG='#ff2bd6',RD='#ff2d55',AM='#ffb800',GN='#2bffb4';
const arrow=d=>`<span class="arw ${d>1?'up':d<-1?'dn':'fl'}"></span>`, dcls=d=>d>1?'up':d<-1?'dn':'fl', sgn=d=>(d>0?'+':'')+d.toFixed(1)+'%';
function spark(a,w=48,h=15,col='#00e5ff'){if(!a||a.length<2)return'';const mx=Math.max(...a,1),mn=Math.min(...a),r=(mx-mn)||1;
  const pts=a.map((v,i)=>(i/(a.length-1)*w).toFixed(1)+','+(h-1-(v-mn)/r*(h-2)).toFixed(1)).join(' ');
  return `<svg class="spk" width="${w}" height="${h}"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.4" style="filter:drop-shadow(0 0 3px ${col})"/></svg>`;}
function ring(v,col){v=Math.max(0,Math.min(100,Math.round(v)));const c=2*Math.PI*18,o=c*(1-v/100);
  return `<svg class="ring" viewBox="0 0 46 46"><circle cx="23" cy="23" r="18" fill="none" stroke="#0e2240" stroke-width="4"/><circle cx="23" cy="23" r="18" fill="none" stroke="${col}" stroke-width="4" stroke-linecap="round" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${o.toFixed(1)}" transform="rotate(-90 23 23)" style="filter:drop-shadow(0 0 4px ${col})"/><text x="23" y="27" text-anchor="middle">${v}</text></svg>`;}
function srcChips(f){return (f||[]).slice(0,6).map(s=>{const u=safeUrl(s[1]);return u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(s[0])}</a>`:`<span class="badge">${esc(s[0])}</span>`}).join(' ');}
function evItem(c){const u=safeUrl(c.url);const col=CATC[c.categoria]||'#888';
  return `<div class="item" style="border-left-color:${col}">${ring(c.relevancia,col)}<div class="tt"><a class="t" ${u?`href="${esc(u)}" target="_blank" rel="noopener noreferrer"`:''}>${esc(c.titulo)}</a>
  <div class="meta"><span class="badge" style="border-color:${tcol(c.tipo)};color:${tcol(c.tipo)}">${ticon(c.tipo)} ${esc(tname(c.tipo))}</span><span class="badge" style="color:${col}">${esc(catName(c.categoria))}</span>
  <span class="badge">📍 ${esc(c.departement||'?')}</span><span class="badge">📅 ${esc(c.fecha)}</span><span class="badge">💀 ${c.severidad}/10</span><span class="badge">✔ ${c.confianza}%</span>
  <span class="srcs">${esc(T('sources_lbl'))}: ${srcChips(c.fuentes)}</span></div></div></div>`;}

function applyI18n(){
  $$('[data-i18n]').forEach(e=>e.textContent=T(e.dataset.i18n));
  $$('[data-i18n-ph]').forEach(e=>e.placeholder=T(e.dataset.i18nPh));
  document.documentElement.lang=LANG;$('#lang').value=LANG;
  const sel=$('#fTipo'),cur=S.tipo;sel.innerHTML='<option value="">'+esc(T('all_types'))+'</option>';
  Object.keys(TYPES).filter(k=>k!=='other').forEach(k=>{const o=document.createElement('option');o.value=k;o.textContent=ticon(k)+' '+tname(k);sel.appendChild(o);});sel.value=cur;
  updAlarmUI();updVig();
}

/* ===================== TICKER (crypto style) ===================== */
async function renderTicker(){
  const d=await api('/api/indicators');
  const lab=k=>k.kind==='cat'?catName(k.key):k.kind==='tipo'?ticon(k.key)+' '+tname(k.key):T(k.label||k.key);
  const col=k=>k.kind==='cat'?CATC[k.key]:k.kind==='tipo'?tcol(k.key):CY;
  const one=d.tickers.map(k=>`<span class="tk"><b style="color:${col(k)}">${esc(lab(k))}</b><i>${k.kind==='rsi'||k.kind==='idx'?k.value.toFixed(0):nf(k.value)}</i>${arrow(k.delta)}<em class="${dcls(k.delta)}">${sgn(k.delta)}</em>${spark(k.series,48,15,col(k))}</span>`).join('');
  $('#tape').innerHTML=`<div class="tape-in">${one}${one}</div>`;
}
/* ===================== GOV ALERTS ===================== */
let VIG=null;
async function renderGov(){
  const d=await api('/api/alerts');VIG=d.vigipirate;
  $('#govItems').innerHTML=d.items.length?d.items.slice(0,24).map(a=>{const u=safeUrl(a.url);return `<span class="it ${a.nivel>=7?'hi':''}"><u class="${a.ctx}">${a.ctx==='cyber'?'FINANZAS':'SEGURIDAD'}</u>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(a.titulo)}</a>`:esc(a.titulo)}<small style="color:var(--mut)">${esc(a.fecha)} · ${esc(a.fuente)}</small></span>`}).join(''):`<span style="color:var(--mut)">${esc(T('gov_none'))}</span>`;
  $('#ledGov').className='led '+(d.items.length?'on':'warn');updVig();
}
function updVig(){const b=$('#vig');if(!b)return;const n=VIG&&VIG.nivel?VIG.nivel:0;b.className='vig l'+n;b.textContent='ALERTA · '+(n?T('vig_'+n):T('vig_set'));}
$('#vig').onclick=async()=>{const n=prompt(T('vig_prompt'),(VIG&&VIG.nivel)||'');if(n===null)return;const v=parseInt(n);await post('/api/vigipirate',{nivel:(v>=1&&v<=3)?v:0});renderGov();};

/* ===================== DASHBOARD ===================== */
const GAUGE_LBL=['th_calm','th_watch','th_tense','th_crit'];
function gaugeSVG(v){const a=Math.PI*(1-v/100),cx=150,cy=140,r=110,x=cx+r*Math.cos(a)*0.9,y=cy-r*Math.sin(a)*0.9;
  return `<svg viewBox="0 0 300 175"><defs><linearGradient id="gg" x1="0" x2="1"><stop offset="0" stop-color="#2bffb4"/><stop offset=".45" stop-color="#ffb800"/><stop offset=".75" stop-color="#ff2bd6"/><stop offset="1" stop-color="#ff2d55"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <path d="M40 140 A110 110 0 0 1 260 140" fill="none" stroke="#0e2240" stroke-width="16" stroke-linecap="round"/>
  <path d="M40 140 A110 110 0 0 1 260 140" fill="none" stroke="url(#gg)" stroke-width="16" stroke-linecap="round" pathLength="100" stroke-dasharray="${v} 100" filter="url(#glow)"/>
  <line x1="150" y1="140" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#fff" stroke-width="3" stroke-linecap="round" filter="url(#glow)"/><circle cx="150" cy="140" r="7" fill="#fff"/>
  <text x="150" y="112" text-anchor="middle" font-family="Orbitron" font-size="34" fill="#fff" filter="url(#glow)">${Math.round(v)}</text></svg>`;}
async function renderDash(){
  const [st,an,ind,geoRel]=await Promise.all([api('/api/stats'),api('/api/analytics'),api('/api/indicators'),api('/api/crimes','&sort=rel&per=6')]);
  const dl=(a,b)=>b>0?(a-b)/b*100:(a>0?100:0), cy=st.total?Math.round((st.categorias.cyber||0)/st.total*100):0;
  const K=[['📊',nf(st.total),'k_total',null],['⚡',nf(st.ultimos_7dias),'k_7d',dl(st.ultimos_7dias,st.prev_7dias)],['🔥',nf(st.ultimos_30dias),'k_30d',dl(st.ultimos_30dias,st.prev_30dias)],
   ['🚨',nf(st.categorias.rue||0),'cat_rue',null],['🛡',nf(st.categorias.cyber||0)+' · '+cy+'%','k_cyber',null],['⚔',nf(st.conflictos_24h),'k_conf24',null],['🔗',nf(st.multi_fuente),'k_multi',null],
   ['📰',st.n_fuentes,'k_sources',null],['📍',st.n_departements,'k_depts',null],['💀',st.severidad_promedio.toFixed(1)+'/10','k_sev',null]];
  $('#kpis').innerHTML=K.map(k=>`<div class="holo kpi"><small>${k[0]} ${esc(T(k[2]))}</small><b>${esc(k[1])}</b>${k[3]!==null?`<span class="d ${dcls(k[3])}">${arrow(k[3])} ${sgn(k[3])}</span>`:''}</div>`).join('');
  $('#upd').textContent=st.ultima_actualizacion||'';
  const th=ind.threat;$('#gauge').innerHTML=gaugeSVG(th.idx)+`<div class="gl hl" style="text-align:center">${esc(T(GAUGE_LBL[th.level]))}</div>`;
  const sg=ind.signal==='up'?['sig_up','up']:ind.signal==='dn'?['sig_dn','dn']:['sig_neu','fl'];
  $('#ind').innerHTML=`<div><small>RSI·14</small><b style="color:${ind.rsi>70?RD:ind.rsi<30?GN:CY}">${ind.rsi.toFixed(0)}</b></div><div><small>SMA7/30</small><b>${arrow(ind.momentum)}${sgn(ind.momentum)}</b></div><div><small>${esc(T('vol'))}</small><b>${ind.volatility.toFixed(2)}</b></div>
   <div style="grid-column:1/-1"><small>${esc(T('signal'))}</small><span class="sig ${sg[1]}">${esc(T(sg[0]))}</span></div>`;
  const s=ind.series;
  mk('chBoll',{type:'line',data:{labels:s.dates.map(d=>d.slice(5)),datasets:[
    {label:'BB+',data:s.up,borderColor:'rgba(139,92,255,.6)',borderWidth:1,pointRadius:0,fill:false,tension:.3},
    {label:'BB−',data:s.dn,borderColor:'rgba(139,92,255,.6)',borderWidth:1,pointRadius:0,fill:'-1',backgroundColor:'rgba(139,92,255,.12)',tension:.3},
    {label:'SMA30',data:s.sma30,borderColor:AM,borderWidth:1.6,pointRadius:0,tension:.3},{label:'SMA7',data:s.sma7,borderColor:MG,borderWidth:1.8,pointRadius:0,tension:.3},
    {label:T('k_total'),type:'bar',data:s.counts,backgroundColor:s.counts.map((_,i)=>s.rsi[i]>70?'rgba(255,45,85,.7)':'rgba(0,229,255,.35)'),borderRadius:2}]},
    options:{interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{boxWidth:10,font:{size:10}}}},scales:{x:{ticks:{maxTicksLimit:12}}}}});
  $('#streetList').innerHTML=st.street.length?st.street.map(evItem).join(''):`<div class="empty">${esc(T('no_data'))}</div>`;
  $('#topRel').innerHTML=geoRel.items.length?geoRel.items.map(evItem).join(''):`<div class="empty">${esc(T('no_data'))}</div>`;
  const dep=Object.entries(st.departements).slice(0,10);
  mk('chDept',{type:'bar',data:{labels:dep.map(d=>d[0]),datasets:[{data:dep.map(d=>d[1]),borderRadius:5,backgroundColor:dep.map((_,i)=>i%2?'rgba(0,229,255,.75)':'rgba(255,43,214,.75)')}]},options:{indexAxis:'y',plugins:{legend:{display:false}}}});
  const tp=Object.entries(st.tipos).sort((a,b)=>b[1]-a[1]);
  mk('chTypes',{type:'doughnut',data:{labels:tp.map(x=>ticon(x[0])+' '+tname(x[0])),datasets:[{data:tp.map(x=>x[1]),backgroundColor:tp.map(x=>tcol(x[0])),borderColor:'#050a14',borderWidth:3}]},options:{cutout:'58%',plugins:{legend:{position:'right',labels:{boxWidth:10,font:{size:10}}}}}});
  const ms=Object.keys(st.mensual),ln=(k,c)=>({label:catName(k),data:ms.map(m=>st.mensual[m][k]),borderColor:c,backgroundColor:c+'30',fill:true,tension:.35,pointRadius:2});
  mk('chMonthly',{type:'line',data:{labels:ms,datasets:[ln('fisico',RD),ln('rue',AM),ln('cyber',CY)]},options:{interaction:{mode:'index',intersect:false}}});
  const top8=tp.slice(0,8),mx=Math.max(1,...top8.map(x=>x[1]));
  mk('chRadar',{type:'radar',data:{labels:top8.map(x=>tname(x[0])),datasets:[{data:top8.map(x=>Math.round(x[1]/mx*100)),borderColor:CY,backgroundColor:'rgba(0,229,255,.2)',pointBackgroundColor:MG}]},options:{plugins:{legend:{display:false}},scales:{r:{ticks:{display:false},grid:{color:'rgba(40,80,130,.4)'},angleLines:{color:'rgba(40,80,130,.4)'},pointLabels:{font:{size:10}}}}}});
  mk('chSev',{type:'polarArea',data:{labels:[1,2,3,4,5,6,7,8,9,10],datasets:[{data:st.sev_hist,backgroundColor:st.sev_hist.map((_,i)=>`hsla(${190+i*18},90%,58%,.7)`)}]},options:{plugins:{legend:{display:false}},scales:{r:{ticks:{display:false},grid:{color:'rgba(40,80,130,.4)'}}}}});
  const f=an.forecast,L=f.hist_labels.concat(f.pred_labels),pad=f.hist.map(()=>null);
  mk('chFore',{type:'line',data:{labels:L,datasets:[{label:T('history_lbl'),data:f.hist.concat(f.pred.map(()=>null)),borderColor:CY,tension:.3,pointRadius:2},
    {label:T('forecast_lbl'),data:f.pred.length?pad.slice(0,-1).concat([f.hist[f.hist.length-1]]).concat(f.pred):[],borderColor:MG,borderDash:[6,5],tension:.3,pointRadius:3}]}});
  mk('chAnom',{type:'bar',data:{labels:an.daily.map(d=>d.date.slice(5)),datasets:[{data:an.daily.map(d=>d.count),backgroundColor:an.daily.map(d=>d.z>=2?RD:'rgba(0,229,255,.45)'),borderRadius:3}]},options:{plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:10}}}}});
  renderHeat(st.weekday_type);
  const tr=an.trending,mxs=Math.max(1,...tr.map(x=>x.score));
  $('#cloud').innerHTML=tr.length?tr.map(x=>`<span title="x${x.score} · ${x.count}" style="font-size:${(.85+x.score/mxs*1.5).toFixed(2)}em;color:hsl(${(300-x.score/mxs*120)|0},90%,66%)">${esc(x.word)}</span>`).join(''):`<div class="empty">${esc(T('no_data'))}</div>`;
  $('#alerts').innerHTML=an.anomalies.length?an.anomalies.slice(-6).reverse().map(a=>`<div class="alert"><span>⚡ ${esc(T('alert_spike'))} · ${esc(a.date)}</span><b>${a.count} (z=${a.z})</b></div>`).join(''):`<div class="alert ok">✔ ${esc(T('alert_ok'))}</div>`;
  $('#hotl').innerHTML=an.hotspots.slice(0,5).map((h,i)=>`<div class="hli"><span>${i+1}. ${esc(h.label)}</span><b>${h.count} · ${h.sev}/10</b></div>`).join('')||`<div class="empty">${esc(T('no_data'))}</div>`;
}
function renderHeat(wt){const ks=Object.keys(wt);if(!ks.length){$('#hm').innerHTML=`<div class="empty">${esc(T('no_data'))}</div>`;return;}
  const mx=Math.max(1,...ks.flatMap(k=>wt[k])),d0=new Date(2024,0,1);
  const days=[...Array(7)].map((_,i)=>new Date(d0.getTime()+i*864e5).toLocaleDateString(LOC[LANG],{weekday:'short'}));
  $('#hm').innerHTML='<table class="hm"><tr><th></th>'+days.map(d=>`<th>${esc(d)}</th>`).join('')+'</tr>'+ks.map(k=>`<tr><td class="l">${ticon(k)} ${esc(tname(k))}</td>`+wt[k].map(v=>`<td style="background:rgba(255,43,214,${(v/mx*.8+.04).toFixed(2)});color:${v/mx>.5?'#fff':'#a9bad6'}">${v}</td>`).join('')+'</tr>').join('')+'</table>';}

/* ===================== MAP ===================== */
let MAP,LAYERS={},LCTRL,GEOJ=null,PTS=[],HEAT=null,TL=null,BASES=null;
function popup(p){const u=safeUrl(p[8]),col=CATC[p[10]]||'#888';
  return `<b>${ticon(p[4])} ${esc(tname(p[4]))}</b> <span style="color:${col}">· ${esc(catName(p[10]))}</span><br>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(p[5])}</a>`:esc(p[5])}<br>
  <small>${esc(p[7])} · ${esc(p[6])} · ${esc(T('severity'))} ${p[2]}/10</small><div class="relbar" title="${esc(T('relevance'))}"><i style="width:${p[11]}%"></i></div>
  <small>${esc(T('relevance'))} ${p[11]}% · ${esc(T('confirmed_by'))} ${p[12]}</small><div class="srcs" style="margin-top:4px">${srcChips(p[13])}</div>`;}
const cut=(t,n)=>{t=String(t||'');return t.length>n?t.slice(0,n-1)+'…':t;};
function tip(p){const col=CATC[p[10]]||'#888';
  return `<b>${ticon(p[4])} ${esc(tname(p[4]))}</b> <span style="color:${col}">· ${esc(catName(p[10]))}</span><br>${esc(cut(p[5],120))}<br>
  <small>📍 ${esc(p[7])} · ${esc(p[6])}<br>${esc(T('severity'))} ${p[2]}/10 · ${esc(T('relevance'))} ${p[11]}% · ${esc(T('confirmed_by'))} ${p[12]}</small>`;}
function clusterTip(l){const ms=l.getAllChildMarkers(),c={};let mx=0;
  ms.forEach(m=>{const p=m._p;if(!p)return;c[p[4]]=(c[p[4]]||0)+1;mx=Math.max(mx,p[2]);});
  const top=Object.entries(c).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([t,n])=>`${ticon(t)} ${esc(tname(t))} <b>×${n}</b>`).join('<br>');
  return `<b>Σ ${ms.length}</b> · ${esc(T('severity'))} max ${mx}/10<br>${top}`;}
function initMap(){
  MAP=L.map('map',{preferCanvas:true}).setView([6,-72],4);
  const mkT=(u,o)=>L.tileLayer(u,Object.assign({maxZoom:19,attribution:'© OpenStreetMap contributors'},o||{}));
  BASES={'map_dark':mkT('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',attribution:'© OpenStreetMap · © CARTO'}),
   'map_street':mkT('https://tile.openstreetmap.org/{z}/{x}/{y}.png'),
   'map_osmfr':mkT('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',{subdomains:'abc',attribution:'© OpenStreetMap HOT'}),
   'map_voyager':mkT('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{subdomains:'abcd',attribution:'© OpenStreetMap · © CARTO'}),
   'map_light':mkT('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',attribution:'© OpenStreetMap · © CARTO'}),
   'map_sat':mkT('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{attribution:'Tiles © Esri'})};
  const sel=lsGet('df_base','map_dark');(BASES[sel]||BASES.map_dark).addTo(MAP);
  MAP.on('baselayerchange',e=>{for(const k in BASES)if(BASES[k]===e.layer)lsSet('df_base',k);});
  $$('[data-fly]').forEach(b=>b.onclick=()=>{const [a,o,z]=b.dataset.fly.split(',').map(Number);MAP.flyTo([a,o],z);});
}
async function renderMap(){
  if(!MAP)initMap();
  const g=await api('/api/geo');PTS=g.points;
  Object.values(LAYERS).forEach(l=>MAP.removeLayer(l));if(LCTRL)MAP.removeControl(LCTRL);LAYERS={};
  HEAT=L.heatLayer(PTS.map(p=>[p[0],p[1],Math.max(.15,p[2]/10)]),{radius:22,blur:20,minOpacity:.3,gradient:{.2:'#2f6bff',.45:'#00e5ff',.65:'#ffb800',.85:'#ff2d55',1:'#fff'}});
  LAYERS[T('m_heat')]=HEAT;
  const cl=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:45,chunkedLoading:true});
  PTS.forEach(p=>{const mk=L.circleMarker([p[0],p[1]],{radius:5+p[2]*.45,color:'#03050c',weight:1,fillColor:tcol(p[4]),fillOpacity:.9}).bindPopup(popup(p)).bindTooltip(tip(p),{sticky:true,direction:'top',className:'ptip',opacity:1});mk._p=p;cl.addLayer(mk);});
  cl.on('clustermouseover',a=>{const l=a.layer;l.unbindTooltip();l.bindTooltip(clusterTip(l),{direction:'top',className:'ptip',opacity:1}).openTooltip();});
  LAYERS[T('m_clusters')]=cl;
  const rue=PTS.filter(p=>p[10]==='rue').slice(0,160);
  LAYERS[T('m_pulse')]=L.layerGroup(rue.map(p=>L.marker([p[0],p[1]],{icon:L.divIcon({className:'pulse'+(p[2]>=(CFG.umbral||6)?' hi':''),html:'<i></i>',iconSize:[18,18]})}).bindPopup(popup(p)).bindTooltip(tip(p),{direction:'top',offset:[0,-10],className:'ptip',opacity:1})));
  LAYERS[T('m_hot')]=L.layerGroup(g.hotspots.map(h=>L.circle([h.lat,h.lon],{radius:15000+h.count*3500,color:RD,weight:1.5,fillColor:RD,fillOpacity:.12,dashArray:'4 4'}).bindTooltip(`🔥 ${esc(h.label)} · ${h.count} · ${h.sev}/10`)));
  {const mx=Math.max(1,...Object.values(g.dept_counts||{}));const P2=g.dept_pos||{};
    LAYERS[T('m_choro')]=L.layerGroup(Object.keys(g.dept_counts||{}).filter(k=>P2[k]).map(k=>{const v=g.dept_counts[k]/mx;return L.circle([P2[k][1],P2[k][2]],{radius:60000+v*260000,color:'#16304f',weight:1,fillColor:`hsl(${(260+v*100)|0},90%,${40+v*15|0}%)`,fillOpacity:.35+v*.25}).bindTooltip(`${esc(P2[k][0])}: ${g.dept_counts[k]}`,{sticky:true});}));}
  const bl={};for(const k in BASES)bl[T(k)]=BASES[k];
  LCTRL=L.control.layers(bl,LAYERS,{collapsed:false}).addTo(MAP);
  [T('m_heat'),T('m_clusters'),T('m_pulse'),T('m_hot')].forEach(k=>LAYERS[k]&&LAYERS[k].addTo(MAP));
  $('#mapNote').textContent=T('geo_note')+' · '+nf(PTS.length)+' '+T('events');
  setTimeout(()=>MAP.invalidateSize(),60);
}
function fitMap(){if(!MAP||!PTS.length)return;MAP.fitBounds(L.latLngBounds(PTS.map(p=>[p[0],p[1]])).pad(.1));}
function flyTo(lat,lon,z){if(MAP)MAP.flyTo([lat,lon],z||11);}
$('#fitBtn').onclick=fitMap;
$('#tlBtn').onclick=()=>{if(TL){clearInterval(TL);TL=null;$('#tlLbl').textContent='';if(HEAT)HEAT.setLatLngs(PTS.map(p=>[p[0],p[1],Math.max(.15,p[2]/10)]));return;}
  if(!HEAT||!PTS.length)return;const days=[...new Set(PTS.map(p=>p[6]))].sort().slice(-30);let i=0;
  TL=setInterval(()=>{const d=days[i];HEAT.setLatLngs(PTS.filter(p=>p[6]<=d).map(p=>[p[0],p[1],Math.max(.15,p[2]/10)]));$('#tlLbl').textContent=d;if(++i>=days.length){clearInterval(TL);TL=null;}},450);};

/* ===================== GRAPHS / NETWORK / STATIC / FEED ===================== */
const nodeLabel=k=>{const[p,v]=k.split(/:(.*)/);return p==='cat'?'◆ '+catName(v):p==='tipo'?ticon(v)+' '+tname(v):'📍 '+v;};
const nodeColor=k=>{const[p,v]=k.split(/:(.*)/);return p==='cat'?CATC[v]:p==='tipo'?tcol(v):'#64748b';};
async function renderGraphs(){
  const [d,st]=await Promise.all([api('/api/sankey'),api('/api/stats')]),labels={};
  d.flows.forEach(f=>{labels[f[0]]=nodeLabel(f[0]);labels[f[1]]=nodeLabel(f[1]);});
  mk('chSankey',{type:'sankey',data:{datasets:[{data:d.flows.map(f=>({from:f[0],to:f[1],flow:f[2]})),labels,colorFrom:c=>nodeColor(c.dataset.data[c.dataIndex].from),colorTo:c=>nodeColor(c.dataset.data[c.dataIndex].to),colorMode:'gradient',size:'max',color:'#e6f4ff',font:{size:11}}]},options:{plugins:{legend:{display:false}}}});
  const w=st.semanal;
  mk('chWeekly',{type:'bar',data:{labels:w.labels,datasets:['fisico','rue','cyber'].map(k=>({label:catName(k),data:w[k],backgroundColor:CATC[k]+'cc',borderRadius:3}))},options:{scales:{x:{stacked:true},y:{stacked:true}}}});
  mk('chBubble',{type:'bubble',data:{datasets:[{label:T('c_dept'),data:st.dept_bubble.map(b=>({x:b.n,y:b.sev,r:5+Math.min(18,b.n/2),d:b.d})),backgroundColor:'rgba(255,43,214,.45)',borderColor:MG}]},
    options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw.d}: ${c.raw.x} · ${c.raw.y}/10`}}},scales:{x:{title:{display:true,text:'#'}},y:{title:{display:true,text:T('severity')},min:0,max:10}}}});
}
let NET;
async function renderNet(){const d=await api('/api/network');
  const nodes=d.nodes.map(n=>({id:n.id,value:n.value,label:n.group==='tipo'?ticon(n.key)+' '+tname(n.key):n.label,shape:n.group==='tipo'?'dot':'box',color:n.group==='tipo'?{background:tcol(n.key),border:'#03050c'}:{background:'#0b1a30',border:'#00e5ff'},font:{color:'#e6f4ff',size:13}}));
  NET=new vis.Network($('#net'),{nodes:new vis.DataSet(nodes),edges:new vis.DataSet(d.edges.map(e=>({...e,color:{color:'#2f6bff',opacity:.5}})))},{physics:{solver:'forceAtlas2Based',stabilization:{iterations:160}},interaction:{hover:true},edges:{smooth:{type:'continuous'}}});}
function imgFail(el){const d=document.createElement('div');d.className='empty';d.textContent='⚠ '+T('st_missing');el.replaceWith(d);}
function renderStatic(){const k=[['tipos','st_tipos'],['mensual','st_mensual'],['heatmap','st_heatmap'],['hexbin','st_hexbin'],['red','st_red']],ts=Date.now();
  $('#statics').innerHTML=k.map(x=>`<div class="holo card"><h3>${esc(T(x[1]))}</h3><img alt="" loading="lazy" src="/graph/${x[0]}.png?${qs()}&t=${ts}" onerror="imgFail(this)"></div>`).join('');}
async function renderFeed(){const d=await api('/api/crimes','&page='+S.page+'&sort='+S.sort);
  $('#feed').innerHTML=d.items.length?d.items.map(evItem).join(''):`<div class="empty">${esc(T('no_data'))}</div>`;
  $('#pager').innerHTML=`<button class="btn sm" ${d.page<=1?'disabled':''} id="pp">${esc(T('prev'))}</button><span>${esc(T('page'))} ${d.page} / ${d.total_pages} · ${nf(d.total)} ${esc(T('events'))}</span><button class="btn sm" ${d.page>=d.total_pages?'disabled':''} id="pn">${esc(T('next'))}</button>`;
  $('#pp').onclick=()=>{S.page--;renderFeed();};$('#pn').onclick=()=>{S.page++;renderFeed();};}

/* ===================== SCAN CENTER ===================== */
const OFF=[['DEA','https://www.dea.gov/'],['OFAC','https://ofac.treasury.gov/recent-actions'],['UNODC','https://www.unodc.org/'],['Insight Crime','https://insightcrime.org/'],['InterAmerican/OEA CICAD','https://www.oas.org/es/sms/cicad/'],['Alertas de viaje EE.UU.','https://travel.state.gov/'],['Emergencias 911 · 112 · 190','tel:911']];
let SRC=[];
function lastDot(l){if(!l||!l.kind)return['','status_idle'];if(l.kind==='ok'&&l.n>0)return['ok','status_ok'];if(l.kind==='ok')return['warn','status_empty'];if(l.kind==='dns')return['bad','status_dns'];if(l.kind==='blocked')return['warn','status_blocked'];if(l.kind==='gone')return['warn','status_gone'];return['bad','status_err'];}
async function renderScan(){
  const r=await (await fetch('/api/sources')).json();SRC=r.sources;
  $('#srcCount').textContent=SRC.filter(s=>s.activo).length+'/'+SRC.length;
  $('#srcBody').innerHTML=SRC.map((s,i)=>{const l=s.last||{},[dc,tk]=lastDot(l),u=safeUrl(s.url);
    return `<tr><td><span class="dot ${dc}"></span></td><td>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(s.nombre)}</a>`:esc(s.nombre)}<br><small style="color:var(--mut)">${esc(s.departement)}</small></td><td>${esc(s.tipo)}</td><td>${l.n!=null?l.n:'–'}<br><small style="color:var(--mut)">${l.dur!=null?l.dur+'s':''}</small></td>
    <td><small>${esc(T(tk))}${l.note?' · '+esc(l.note):''}${s.fails>1?' · ✖'+s.fails:''}</small></td><td style="white-space:nowrap"><button class="btn sm" data-sc="${i}">▶</button> <button class="btn sm ${s.activo?'':'red'}" data-tg="${i}">${s.activo?'ON':'OFF'}</button></td></tr>`}).join('');
  $$('[data-sc]').forEach(b=>b.onclick=()=>startScan('src:'+SRC[b.dataset.sc].nombre));
  $$('[data-tg]').forEach(b=>b.onclick=async()=>{await post('/api/sources/toggle',{nombre:SRC[b.dataset.tg].nombre});renderScan();});
  const dp=[...new Set(SRC.map(s=>s.departement))].sort();
  const keep=$('#sDep').value;$('#sDep').innerHTML=dp.map(d=>`<option>${esc(d)}</option>`).join('');if(keep)$('#sDep').value=keep;
  const ks=$('#sSrc').value;$('#sSrc').innerHTML=SRC.map(s=>`<option>${esc(s.nombre)}</option>`).join('');if(ks)$('#sSrc').value=ks;
  $('#offLinks').innerHTML=OFF.map(o=>`<a class="btn sm" href="${o[1]}" target="_blank" rel="noopener noreferrer">${esc(o[0])}</a>`).join('');
}
async function startScan(scope){const r=await post('/api/scan',{scope,paginas:+$('#sPages').value,sens:$('#sSens').value});if(r.started===false)logLine({l:'warn',t:'',m:T('scan_busy')});}
$$('[data-scan]').forEach(b=>b.onclick=()=>startScan(b.dataset.scan));
$('#sDepGo').onclick=()=>startScan('dep:'+$('#sDep').value);$('#sSrcGo').onclick=()=>startScan('src:'+$('#sSrc').value);
['#btnStop','#btnStop2'].forEach(s=>$(s).onclick=()=>post('/api/scan/stop'));
['#btnVerify','#btnVerify2'].forEach(s=>$(s).onclick=()=>post('/api/verify'));
$('#btnAdd').onclick=async()=>{const r=await post('/api/sources/add',{nombre:$('#nName').value,url:$('#nUrl').value,departement:$('#nDep').value||'National',tipo:$('#nTipo').value});if(r.ok){$('#nName').value='';$('#nUrl').value='';renderScan();}else alert(r.error||'error');};
function logLine(e){const c=$('#console');if(!c)return;const d=document.createElement('div');d.className='l-'+(e.l||'info');d.textContent=(e.t?e.t+'  ':'')+e.m;c.appendChild(d);while(c.childNodes.length>400)c.removeChild(c.firstChild);c.scrollTop=c.scrollHeight;}

/* ===================== ALARM ===================== */
const AL={armed:lsGet('df_armed','0')==='1',vol:+lsGet('df_vol','60'),snd:lsGet('df_snd','siren'),muteUntil:0,ctx:null,node:null,playing:false,last:null,seq:null,notif:lsGet('df_notif','0')==='1'};
function ensureCtx(){if(!AL.ctx){try{AL.ctx=new (window.AudioContext||window.webkitAudioContext)();}catch(e){}}if(AL.ctx&&AL.ctx.state==='suspended')AL.ctx.resume();return AL.ctx;}
function stopSiren(){if(AL.node){try{AL.node.stop();}catch(e){}AL.node=null;}AL.playing=false;$('#alarmOv').classList.remove('on');document.body.classList.remove('alarming');updAlarmUI();}
function playSiren(){const c=ensureCtx();if(!c||AL.playing)return;AL.playing=true;
  const o=c.createOscillator(),g=c.createGain(),lfo=c.createOscillator(),lg=c.createGain();
  const m={siren:['sawtooth',900,.55,350],pulse:['square',880,5,0],klaxon:['square',420,2.2,0]}[AL.snd]||['sawtooth',900,.55,350];
  o.type=m[0];o.frequency.value=m[1];lfo.frequency.value=m[2];lg.gain.value=m[3];
  if(AL.snd==='siren'){lfo.connect(lg);lg.connect(o.frequency);}
  else{lfo.type='square';const lg2=c.createGain();lg2.gain.value=.5;lfo.connect(lg2);lg2.connect(g.gain);}
  g.gain.value=Math.max(0,AL.vol/100)*.25;o.connect(g);g.connect(c.destination);o.start();lfo.start();
  const stop=o.stop.bind(o);o.stop=()=>{try{stop();lfo.stop();}catch(e){}};AL.node=o;setTimeout(()=>{if(AL.node===o)stopSiren();},9000);if(navigator.vibrate)navigator.vibrate([300,150,300,150,300]);}
function trigger(al){AL.last=al;const it=(al.items||[])[0]||{};
  const txt=(al.test?'[TEST] ':'')+(it.titulo||T('alarm_conflict'))+(it.dep?' · '+it.dep:'')+(al.items&&al.items.length>1?' (+'+(al.items.length-1)+')':'');
  $('#alarmTxt').textContent=txt;$('#alarmOv').classList.add('on');document.body.classList.add('alarming');
  const ah=$('#aHist');const dv=document.createElement('div');dv.textContent=new Date().toLocaleTimeString(LOC[LANG])+' · '+txt;ah.prepend(dv);
  if(AL.notif&&window.Notification&&Notification.permission==='granted'){try{new Notification('DIABOLIC LATAM',{body:txt});}catch(e){}}
  if((AL.armed||al.test)&&Date.now()>AL.muteUntil)playSiren();updAlarmUI();}
function updAlarmUI(){const led=$('#ledAlarm'),st=$('#alarmState'),muted=Date.now()<AL.muteUntil;
  led.className='led '+(AL.playing?'bad':!AL.armed?'':muted?'warn':'on');
  if(st)st.textContent=T(AL.playing?'alarm_ringing':!AL.armed?'alarm_off':muted?'alarm_muted':'alarm_armed');
  const a=$('#aArm');if(a)a.textContent=AL.armed?T('alarm_disarm'):T('alarm_arm');
  const h=$('#aHint');if(h)h.textContent=(AL.ctx&&AL.ctx.state==='running')?'':T('alarm_click');
  const bm=$('#btnMute');if(bm)bm.style.opacity=muted?.5:1;}
$('#alarmBtn').onclick=e=>{e.stopPropagation();$('#alarmPanel').classList.toggle('on');};
document.addEventListener('click',e=>{if(!e.target.closest('#alarmPanel')&&!e.target.closest('#alarmBtn'))$('#alarmPanel').classList.remove('on');});
$('#aArm').onclick=()=>{AL.armed=!AL.armed;lsSet('df_armed',AL.armed?'1':'0');ensureCtx();updAlarmUI();};
$('#aTest').onclick=async()=>{ensureCtx();AL.muteUntil=0;await post('/api/alarm/test');};
$('#aMute').onclick=()=>{AL.muteUntil=Date.now()+5*60000;stopSiren();setTimeout(updAlarmUI,5*60000+100);};
$('#btnMute').onclick=()=>{AL.muteUntil=Date.now()<AL.muteUntil?0:Date.now()+30*60000;stopSiren();};
$('#aStop').onclick=stopSiren;$('#alarmAck').onclick=stopSiren;
$('#alarmGo').onclick=()=>{const it=(AL.last&&AL.last.items||[])[0];stopSiren();show('map');if(it&&it.lat!=null)setTimeout(()=>flyTo(it.lat,it.lon,11),400);};
$('#aVol').value=AL.vol;$('#aVol').oninput=e=>{AL.vol=+e.target.value;lsSet('df_vol',AL.vol);};
$('#aSnd').value=AL.snd;$('#aSnd').onchange=e=>{AL.snd=e.target.value;lsSet('df_snd',AL.snd);};
$('#aThr').value=String(CFG.umbral||6);$('#aThr').onchange=e=>post('/api/alarm/config',{umbral:+e.target.value});
$('#aNot').checked=AL.notif;$('#aNot').onchange=e=>{AL.notif=e.target.checked;lsSet('df_notif',AL.notif?'1':'0');if(AL.notif&&window.Notification&&Notification.permission==='default')Notification.requestPermission();};

/* ===================== ORQUESTACIÓN ===================== */
const R={dash:renderDash,map:renderMap,graphs:renderGraphs,network:renderNet,static:renderStatic,feed:renderFeed,scan:renderScan};
async function show(tab){S.tab=tab;$$('.tab-btn').forEach(b=>b.classList.toggle('on',b.dataset.tab===tab));$$('.tab').forEach(s=>s.classList.toggle('on',s.id==='tab-'+tab));
  if(STALE[tab]!==false){STALE[tab]=false;try{await R[tab]();}catch(e){console.error(e);}}
  if(tab==='map'&&MAP)MAP.invalidateSize();if(tab==='network'&&NET)NET.fit();}
function invalidate(){Object.keys(R).forEach(k=>STALE[k]=true);show(S.tab);renderTicker().catch(console.error);renderGov().catch(console.error);}
$$('.tab-btn').forEach(b=>b.onclick=()=>show(b.dataset.tab));
const chipGroup=(sel,key)=>$$(sel+' .chip').forEach(c=>c.onclick=()=>{S[key]=c.dataset.v;S.page=1;$$(sel+' .chip').forEach(x=>x.classList.toggle('on',x===c));invalidate();});
chipGroup('#fPer','periodo');chipGroup('#fCat','cat');
$('#fTipo').onchange=e=>{S.tipo=e.target.value;S.page=1;invalidate();};
$('#fConf').onchange=e=>{S.conf=+e.target.value;S.page=1;invalidate();};
$('#fSort').onchange=e=>{S.sort=e.target.value;S.page=1;STALE.feed=true;if(S.tab==='feed')show('feed');};
let qt;$('#fQ').oninput=e=>{clearTimeout(qt);qt=setTimeout(()=>{S.q=e.target.value;S.page=1;invalidate();},350);};
$('#lang').onchange=e=>{LANG=e.target.value;lsSet('df_lang',LANG);applyI18n();invalidate();};
$('#btnReset').onclick=()=>{Object.assign(S,{periodo:'all',cat:'all',tipo:'',q:'',conf:0,page:1});$('#fQ').value='';$('#fConf').value='0';$$('#fPer .chip,#fCat .chip').forEach(c=>c.classList.toggle('on',c.dataset.v==='all'));applyI18n();invalidate();};
$('#btnFull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();};
$('#btnCopy').onclick=async()=>{try{await navigator.clipboard.writeText(location.origin+'/?lang='+LANG);const b=$('#btnCopy span');const o=b.textContent;b.textContent=T('copied');setTimeout(()=>b.textContent=o,1200);}catch(e){}};
let lastV=null,jobWas=false;
function jobUI(j){const on=j&&j.running;$('#job').classList.toggle('on',!!on);$('#ledScan').className='led '+(on?'run':'');
  $$('[data-scan],#sDepGo,#sSrcGo').forEach(b=>b.disabled=!!on);
  if(on){const p=Math.round((j.progress||0)*100);$('#jobBar').style.width=p+'%';$('#jobPct').textContent=p+'%';$('#jobTxt').textContent=T('updating')+' · '+(j.msg||'')+' · '+(j.done||0)+'/'+(j.total||0);}
  if(jobWas&&!on){STALE.scan=true;if(S.tab==='scan')show('scan');}jobWas=!!on;}
function connect(){let es;try{es=new EventSource('/stream');}catch(e){return;}
  es.onopen=()=>$('#ledLive').className='led on';
  es.onerror=()=>{$('#ledLive').className='led bad';};
  es.onmessage=ev=>{const d=JSON.parse(ev.data);$('#ledLive').className='led on';jobUI(d.job);(d.log||[]).forEach(logLine);
    if(d.alarm&&AL.seq!==null&&d.alarm.seq!==AL.seq)trigger(d.alarm);if(d.alarm)AL.seq=d.alarm.seq;
    if(lastV!==null&&d.version!==lastV)invalidate();lastV=d.version;};}

/* ── ampliar gráficos: botón ⤢ en el título, doble clic en el gráfico, Esc para cerrar ── */
let ZM=null;
function zoomClose(){if(!ZM)return;const{ov,body,ph}=ZM;ph.parentNode.insertBefore(body,ph);ph.remove();ov.remove();document.body.classList.remove('zooming');ZM=null;zoomResize();}
function zoomResize(){setTimeout(()=>{try{window.dispatchEvent(new Event('resize'));if(window.Chart)document.querySelectorAll('canvas').forEach(c=>{const ch=Chart.getChart(c);if(ch)ch.resize();});if(typeof NET!=='undefined'&&NET&&NET.fit)NET.fit();}catch(e){}},80);}
function zoomOpen(card){
  if(ZM)return;const body=card.querySelector('.cv,#net,img');if(!body)return;
  const ph=document.createComment('zm');body.parentNode.insertBefore(ph,body);
  const ov=document.createElement('div');ov.id='zoomOv';
  ov.innerHTML='<div class="holo zbox"><div class="zh"><span></span><button class="btn sm mg">✕</button></div><div class="zb"></div></div>';
  const h=card.querySelector('h3');ov.querySelector('.zh span').textContent=h?h.textContent:'';
  ov.querySelector('.zb').appendChild(body);document.body.appendChild(ov);document.body.classList.add('zooming');
  ov.querySelector('button').onclick=zoomClose;ov.addEventListener('mousedown',e=>{if(e.target===ov)zoomClose();});
  ZM={ov,body,ph};zoomResize();
}
document.addEventListener('keydown',e=>{if(e.key==='Escape')zoomClose();});
const zoomable=c=>c&&c.querySelector&&c.querySelector('.cv,#net,img');
document.addEventListener('click',e=>{if(ZM)return;const h=e.target.closest('.card > h3');if(h&&zoomable(h.parentElement))zoomOpen(h.parentElement);});
document.addEventListener('dblclick',e=>{if(ZM)return;const c=e.target.closest('.card');if(c&&zoomable(c)&&!e.target.closest('input,select,button,textarea'))zoomOpen(c);});
new MutationObserver(()=>document.querySelectorAll('.card > h3:not(.zm)').forEach(h=>{if(zoomable(h.parentElement))h.classList.add('zm');})).observe(document.body,{childList:true,subtree:true});
document.querySelectorAll('.card > h3').forEach(h=>{if(zoomable(h.parentElement))h.classList.add('zm');});
applyI18n();show('dash');renderTicker().catch(console.error);renderGov().catch(console.error);connect();
fetch('/api/alarm/history').then(r=>r.json()).then(h=>{const ah=$('#aHist');(h.items||[]).slice(0,12).forEach(x=>{const d=document.createElement('div');d.textContent=x.ts+' · '+x.titulo;ah.appendChild(d);});}).catch(()=>{});
</script></body></html>
"""



# ============================================================================
# CLI  (terminal alimentada por el mismo bus que el panel web)
# ============================================================================

def mostrar_banner_inicial():
    print(f"""{Color.CYAN}
╔═══════════════════════════════════════════════════════════════════════════════╗
║    ██████╗ ██╗ █████╗ ██████╗  ██████╗ ██╗     ██╗ ██████╗                    ║
║    ██╔══██╗██║██╔══██╗██╔══██╗██╔═══██╗██║     ██║██╔════╝                    ║
║    ██║  ██║██║███████║██████╔╝██║   ██║██║     ██║██║                         ║
║    ██║  ██║██║██╔══██║██╔══██╗██║   ██║██║     ██║██║                         ║
║    ██████╔╝██║██║  ██║██████╔╝╚██████╔╝███████╗██║╚██████╗                    ║
║    ╚═════╝ ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚═╝ ╚═════╝                    ║
║{Color.MAGENTA}   🔪 DIABOLIC LATAM v{VERSION} · NARCO · SICARIATO · LAVADO · ALARMA · OFICIAL  {Color.CYAN}║
║{Color.RESET}{Color.BLUE}   ██████{Color.WHITE}██████{Color.RED}██████{Color.CYAN}   "Plata o plomo"                  - By Condor2026          ║
║                                                      •SpectrumSecurity•       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Color.RESET}""")


def _pausa():
    input(f"\n{Color.GRAY}{t('press_enter')}{Color.RESET}")


def _barra(v, mx, n=30):
    return '█' * min(int(v / mx * n), n) if mx else ''


def tipo_nombre(k):
    return TIPOS_CRIMEN.get(k, TIPOS_CRIMEN['other']).get(IDIOMA_ACTUAL, k)


def _titulo(txt):
    cprint(f"\n{'═' * 70}", 'cyan', bold=True)
    cprint(f"  {txt}", 'magenta', bold=True)
    cprint(f"{'═' * 70}", 'cyan', bold=True)


def mostrar_stats_rapidas():
    r = gestor_global.estadisticas_rapidas()
    st = gestor_global.estadisticas()
    if not r:
        cprint(f"\n⚠️ {t('no_data')}", 'yellow')
        return
    _titulo(f"⚡ {t('m_quick')}")
    print(f"  🔪 {t('top_type')}: {tipo_nombre(r['tipo_mas_comun'])} ({r['tipo_mas_comun_count']} - {r['tipo_mas_comun_porcentaje']:.1f}%)")
    print(f"  📅 {t('top_day')}: {r['dia_mas_activo']} ({r['dia_mas_activo_count']})")
    print(f"  📰 {t('top_source')}: {r['fuente_mas_activa']} ({r['fuente_mas_activa_count']})")
    print(f"  🏴 {t('top_dept')}: {r['departamento_critico']} ({r['departamento_critico_count']})")
    ic = '▲' if r['tendencia'] > 0 else '▼' if r['tendencia'] < 0 else '■'
    print(f"  📈 {t('trend')}: {ic} {abs(r['tendencia']):.1f}%")
    c = st['categorias']
    print(f"  💀 {t('severity')}: {st['severidad_promedio']:.1f}/10 · 🔪 {c.get('fisico', 0)} · 🚨 {c.get('rue', 0)} · 🛡️ {c.get('cyber', 0)} · 🔗 {st['multi_fuente']}")


_MENU = [('m_search', '🔍'), ('m_analysis', '📊'), ('m_patterns', '🔗'), ('m_evolution', '📈'), ('m_web', '🌐'), ('m_last', '📰'),
         ('m_export', '📥'), ('m_verify', '🛠️'), ('m_types', '📊'), ('m_adv', '📈'), ('m_clean', '🧹'), ('m_quick', '⚡'),
         ('m_analytics', '🧠'), ('m_png', '🖼️'), ('m_scan_sub', '🎯'), ('m_gov', '🏛️'), ('m_indic', '📉'), ('m_alarm_test', '🚨'),
         ('m_health', '🩺'), ('m_sens', '🎚️')]


def mostrar_menu_principal():
    st = gestor_global.estadisticas()
    act = len([f for f in fuentes_global if f.get('activo', True)])
    c = st['categorias']
    print(f"\n{Color.CYAN}{'═' * 66}{Color.RESET}\n{Color.BOLD}  🔪 DIABOLIC LATAM v{VERSION}{Color.RESET}   {Color.GRAY}sens={SENSIBILIDAD} · umbral alarma={UMBRAL_ALARMA}{Color.RESET}\n{Color.CYAN}{'═' * 66}{Color.RESET}")
    print(f"  📊 {t('k_total')}: {st['total']}   🔪 {c.get('fisico', 0)}  🚨 {c.get('rue', 0)}  🛡️ {c.get('cyber', 0)}   🏛️ {len(gestor_global.alertas())}")
    print(f"  📰 {t('k_sources')}: {act}/{len(fuentes_global)}   🏴 {t('k_depts')}: {len(st['departements'])}")
    print(f"{Color.YELLOW}{'─' * 66}{Color.RESET}\n{Color.CYAN}  📋 {t('menu_title')}{Color.RESET}")
    half = (len(_MENU) + 1) // 2
    for i in range(half):
        l = f"{Color.GREEN} {i + 1:2d}. {_MENU[i][1]} {t(_MENU[i][0])[:30]:30}{Color.RESET}"
        j = i + half
        r = f"{Color.GREEN}{j + 1:2d}. {_MENU[j][1]} {t(_MENU[j][0])[:30]}{Color.RESET}" if j < len(_MENU) else ''
        print(l + '  ' + r)
    print(f"{Color.RED}  0. 🗑️ {t('m_exit')}{Color.RESET}\n{Color.YELLOW}{'═' * 66}{Color.RESET}")


def servir_web(host='127.0.0.1'):
    iniciar_scheduler()
    if not gestor_global.copia() and not gestor_global.alertas():
        threading.Thread(target=ejecutar_actualizacion, args=('all',), daemon=True).start()
    emit('ok', f"\n🌐 http://localhost:{PUERTO}   (Ctrl+C)   — les scans lancés depuis le panneau s'affichent ici aussi")
    app.run(host=host, port=PUERTO, debug=False, threaded=True)


def _menu_scan():
    _titulo(f"🎯 {t('m_scan_sub')}")
    opts = [('fd', t('btn_scan_fd')), ('cyber', t('btn_scan_cyber')), ('gov', t('btn_scan_gov')), ('dep', t('scan_dep')), ('src', t('scan_src'))]
    for i, (_, n) in enumerate(opts, 1):
        print(f"  {Color.GREEN}{i}. {n}{Color.RESET}")
    o = input(f"{Color.CYAN}➤ {Color.RESET}").strip()
    if o in ('1', '2', '3'):
        ejecutar_actualizacion(opts[int(o) - 1][0])
    elif o == '4':
        deps = sorted({f['departement'] for f in fuentes_global})
        for i, d in enumerate(deps, 1):
            print(f"  {i:2d}. {d}")
        k = input('➤ ').strip()
        if k.isdigit() and 1 <= int(k) <= len(deps):
            ejecutar_actualizacion('dep:' + deps[int(k) - 1])
    elif o == '5':
        for i, f in enumerate(fuentes_global, 1):
            print(f"  {i:2d}. {f['nombre']}")
        k = input('➤ ').strip()
        if k.isdigit() and 1 <= int(k) <= len(fuentes_global):
            ejecutar_actualizacion('src:' + fuentes_global[int(k) - 1]['nombre'])


def _mostrar_alertas():
    _titulo(f"🏛️ {t('gov_alerts')}")
    vg = gestor_global.cfg('vigipirate', {'nivel': 0})
    print(f"  ALERTA REGIONAL: {t('vig_' + str(vg['nivel'])) if vg.get('nivel') else t('vig_set')}")
    for a in gestor_global.alertas()[:25]:
        col = 'red' if a['nivel'] >= 7 else 'yellow' if a['nivel'] >= 5 else 'cyan'
        cprint(f"  [{a['ctx'].upper():5}] {a['fecha']}  {a['titulo'][:90]}", col)
        cprint(f"          {a['fuente']}  {a['url']}", 'gray')
    if not gestor_global.alertas():
        cprint(f"  {t('gov_none')}", 'gray')


def _mostrar_indicadores():
    ind = Analitica.indicadores(gestor_global.copia())
    _titulo(f"📉 {t('m_indic')}")
    th = ind['threat']
    bar = '█' * int(th['idx'] / 5) + '░' * (20 - int(th['idx'] / 5))
    col = ['green', 'yellow', 'magenta', 'red'][th['level']]
    cprint(f"  {t('threat_idx')}: [{bar}] {th['idx']:.0f}/100  {t(['th_calm', 'th_watch', 'th_tense', 'th_crit'][th['level']])}", col, bold=True)
    print(f"  RSI(14)={ind['rsi']:.0f}   SMA7/30={ind['momentum']:+.1f}%   {t('vol')}={ind['volatility']:.2f}   {t('signal')}: {t({'up': 'sig_up', 'dn': 'sig_dn', 'fl': 'sig_neu'}[ind['signal']])}")
    print()
    for k in ind['tickers']:
        nm = t('cat_' + {'fisico': 'phys', 'rue': 'rue', 'cyber': 'cyber'}[k['key']]) if k['kind'] == 'cat' else tipo_nombre(k['key']) if k['kind'] == 'tipo' else k['key'].upper()
        arrow = '▲' if k['delta'] > 1 else '▼' if k['delta'] < -1 else '■'
        cprint(f"  {nm:30} {k['value']:>7}  {arrow} {k['delta']:+6.1f}%  {''.join('▁▂▃▄▅▆▇█'[min(7, int(v / max(1, max(k['series'])) * 7))] for v in k['series'])}",
               'red' if k['delta'] > 1 else 'green' if k['delta'] < -1 else 'gray')


def _mostrar_salud():
    _titulo(f"🩺 {t('m_health')}")
    for f in fuentes_global:
        e = ESTADO['fuentes'].get(f['nombre'], {})
        l = e.get('last') or {}
        k = l.get('kind', '-')
        col = 'green' if k == 'ok' and l.get('n') else 'yellow' if k in ('ok', 'blocked', 'gone', '') else 'red'
        cprint(f"  {'●' if f.get('activo', True) else '○'} {f['nombre'][:38]:38} {k:8} n={l.get('n', '-'):>3} cand={l.get('cand', '-'):>3} {l.get('note', '')[:40]}", col)


def debug_fuente(nombre):
    """Diagnóstico: muestra, para UNA fuente, cada candidato cosechado y por qué se acepta o se rechaza."""
    f = next((x for x in fuentes_global if nombre.lower() in x['nombre'].lower()), None)
    if not f:
        cprint('source inconnue', 'red')
        return
    ext = ExtractorNoticias([f])
    r, kind = fetch(f['url'], INTENTOS_ESCANEO)
    cprint(f"{f['nombre']} → {f['url']}  [{kind}]  {'HTTP ok, ' + str(len(r.text)) + ' o' if r else ''}", 'cyan', bold=True)
    if not r:
        nueva, how = ext.disc.discover_url(f, kind)
        cprint(f"auto-discovery: {nueva} ({how})", 'magenta')
        return
    its = ext.cosechar(r.text, r.url)
    cprint(f"{len(its)} candidats cosechados", 'white')
    for it in its[:40]:
        rej = Counter()
        geo = geolocalizar(it['titulo'] + ' ' + it['texto'][:250], dep_code_fuente(f), 'dbg')
        d = clasificar_detalle(it['titulo'], it['texto'][:350], SENSIBILIDAD, geo['precision'])
        if 'reject' in d:
            cprint(f"  ✖ {d['reject']:11} {it['titulo'][:95]}", 'gray')
        else:
            cprint(f"  ✔ {d['tipo']:11} conf={d['conf']:3} sev={d['sev']} {it['titulo'][:80]}", 'green')


def menu():
    global SENSIBILIDAD
    while True:
        mostrar_menu_principal()
        opc = input(f"{Color.CYAN}➤ {Color.YELLOW}Option: {Color.RESET}").strip()
        if opc == '1':
            ejecutar_actualizacion('all')
            _pausa()
        elif opc == '2':
            st = gestor_global.estadisticas()
            _titulo(f"📊 {t('m_analysis').upper()}")
            print(f"  {t('k_total')}: {st['total']} | 7d: {st['ultimos_7dias']} | 30d: {st['ultimos_30dias']} | 90d: {st['ultimos_90dias']}")
            print(f"  💀 {st['severidad_promedio']:.1f}/10   🔪 {st['categorias'].get('fisico', 0)}  🚨 {st['categorias'].get('rue', 0)}  🛡️ {st['categorias'].get('cyber', 0)}")
            top = sorted(st['departements'].items(), key=lambda x: -x[1])[:10]
            for d, n in top:
                cprint(f"   {d:26}{n:5} {_barra(n, top[0][1])}", 'cyan')
            _pausa()
        elif opc == '3':
            st = gestor_global.estadisticas()
            _titulo(f"🔗 {t('m_patterns').upper()}")
            top = sorted(st['fuentes'].items(), key=lambda x: -x[1])[:10]
            for f, n in top:
                cprint(f"   {f:32}{n:5} {_barra(n, top[0][1])}", 'cyan')
            _pausa()
        elif opc == '4':
            ev = gestor_global.evolucion_mensual()
            _titulo(f"📈 {t('m_evolution').upper()}")
            if ev:
                mx = max(ev.values())
                for m, n in list(ev.items())[-12:]:
                    cprint(f"   {m}  {n:4} {_barra(n, mx)}", 'cyan')
            else:
                cprint(f"   {t('no_data')}", 'gray')
            _pausa()
        elif opc == '5':
            servir_web()
        elif opc == '6':
            _titulo(f"📰 {t('m_last').upper()}")
            hoy = datetime.now()
            for i, c in enumerate(sorted(gestor_global.copia(), key=lambda x: x.get('fecha', ''), reverse=True)[:20], 1):
                d = TIPOS_CRIMEN.get(c.get('tipo'), TIPOS_CRIMEN['other'])
                cprint(f"\n{i:2d}. {d['icono']} {c['titulo'][:100]}", 'white')
                fs = ', '.join(f.get('n', '') for f in (c.get('fuentes') or [])[:4])
                cprint(f"      📅 {c['fecha']} | 📍 {c.get('departement', '?')} | 💀 {c.get('severidad', 0)}/10 | ✔ {c.get('confianza', 0)}% | ⭐ {relevancia(c, hoy)} | 📰 {fs}", 'gray')
            _pausa()
        elif opc == '7':
            fmt = input(f"{Color.YELLOW}1=JSON 2=CSV 3=HTML 4=GeoJSON ➤ {Color.RESET}").strip()
            m = {'1': ('json', gestor_global.exportar_json), '2': ('csv', gestor_global.exportar_csv),
                 '3': ('html', gestor_global.exportar_html), '4': ('geojson', gestor_global.exportar_geojson)}
            if fmt in m:
                fn = f'diabolic_export.{m[fmt][0]}'
                with open(fn, 'w', encoding='utf-8') as f:
                    f.write(m[fmt][1]())
                cprint(f"✅ {fn}", 'green')
            else:
                cprint(f"❌ {t('invalid')}", 'red')
            _pausa()
        elif opc == '8':
            VerificadorFuentes().verificar_todas(fuentes_global)
            _pausa()
        elif opc == '9':
            st = gestor_global.estadisticas()
            _titulo(f"📊 {t('m_types').upper()}")
            top = sorted(st['tipos'].items(), key=lambda x: -x[1])
            for k, n in top:
                cprint(f"   {TIPOS_CRIMEN.get(k, TIPOS_CRIMEN['other'])['icono']} {tipo_nombre(k):34}{n:5} {_barra(n, top[0][1])}", 'cyan')
            _pausa()
        elif opc == '10':
            st = gestor_global.estadisticas()
            _titulo(f"📈 {t('m_adv').upper()}")
            print(f"  {t('k_total')}: {st['total']} · 7d {st['ultimos_7dias']} · 30d {st['ultimos_30dias']} · 90d {st['ultimos_90dias']}")
            print(f"  🔪 {len(st['tipos'])} tipos · 📍 {len(st['departements'])} países · 📰 {len(st['fuentes'])} fuentes · 💀 {st['severidad_promedio']:.1f}/10 · 🔗 {st['multi_fuente']} confirmés")
            _pausa()
        elif opc == '11':
            cprint(f"✅ {gestor_global.limpiar_duplicados()} doublons fusionnés", 'green')
            _pausa()
        elif opc == '12':
            mostrar_stats_rapidas()
            _pausa()
        elif opc == '13':
            an = Analitica.analytics(gestor_global.copia())
            _titulo(f"🧠 {t('m_analytics').upper()}")
            cprint(f"\n⚠️ {t('alerts')}:", 'yellow')
            for a in an['anomalies'][-8:]:
                cprint(f"   ⚡ {a['date']}  n={a['count']}  z={a['z']}", 'red')
            if not an['anomalies']:
                cprint(f"   ✔ {t('alert_ok')}", 'green')
            cprint(f"\n🔥 {t('c_trend')}:", 'yellow')
            cprint('   ' + (', '.join(f"{x['word']}(x{x['score']})" for x in an['trending'][:15]) or '-'), 'cyan')
            cprint(f"\n🗺️ {t('hotspots_t')}:", 'yellow')
            for h in an['hotspots'][:8]:
                cprint(f"   {h['label']:24} n={h['count']:4} sev={h['sev']}", 'cyan')
            f = an['forecast']
            cprint(f"\n🔮 {t('c_forecast')}: " + (' → '.join(f"{d[5:]}:{v}" for d, v in zip(f['pred_labels'], f['pred'])) or '-'), 'magenta')
            _pausa()
        elif opc == '14':
            if not HAS_MPL:
                cprint('⚠️ pip install matplotlib networkx', 'yellow')
                _pausa()
                continue
            os.makedirs(DIR_ESTATICOS, exist_ok=True)
            cr = gestor_global.copia()
            for k in ('tipos', 'mensual', 'heatmap', 'hexbin', 'red'):
                png = render_estatico(k, cr, IDIOMA_ACTUAL)
                if png:
                    p = os.path.join(DIR_ESTATICOS, f'{k}.png')
                    with open(p, 'wb') as fh:
                        fh.write(png)
                    cprint(f"✅ {p}", 'green')
                else:
                    cprint(f"⚠️ {k}: {t('st_missing')}", 'yellow')
            _pausa()
        elif opc == '15':
            _menu_scan()
            _pausa()
        elif opc == '16':
            _mostrar_alertas()
            _pausa()
        elif opc == '17':
            _mostrar_indicadores()
            _pausa()
        elif opc == '18':
            alarma_test()
            _pausa()
        elif opc == '19':
            _mostrar_salud()
            _pausa()
        elif opc == '20':
            o = input(f"{Color.YELLOW}1=amplio (≈v1) 2=equilibrado 3=estricto ➤ {Color.RESET}").strip()
            if o in ('1', '2', '3'):
                SENSIBILIDAD = ('amplio', 'equilibrado', 'estricto')[int(o) - 1]
                cprint(f"✅ sens={SENSIBILIDAD}", 'green')
            _pausa()
        elif opc in ('0', 'q', 'Q'):
            cprint(f"\n👋 {t('bye')}", 'red', bold=True)
            break
        else:
            cprint(f"\n❌ {t('invalid')}", 'red')
            time.sleep(1)


def seleccionar_idioma():
    global IDIOMA_ACTUAL
    print(f"\n{Color.YELLOW}🌍 LANGUE / IDIOMA / LANGUAGE / LINGUA / SPRACHE{Color.RESET}")
    for i, l in enumerate(LANGS, 1):
        print(f"  {Color.GREEN}[{i}] {LANG_FLAGS[l]} {LANG_NAMES[l]}{Color.RESET}")
    while True:
        o = input(f"\n{Color.CYAN}➤ {Color.RESET}").strip()
        if o.isdigit() and 1 <= int(o) <= len(LANGS):
            IDIOMA_ACTUAL = LANGS[int(o) - 1]
            break


def main():
    global IDIOMA_ACTUAL, PUERTO, AUTO_REFRESH_MIN, RESPETAR_ROBOTS, SENSIBILIDAD
    ap = argparse.ArgumentParser(description='DIABOLIC LATAM v8')
    ap.add_argument('--web', action='store_true', help='panneau web direct')
    ap.add_argument('--lang', choices=LANGS)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int)
    ap.add_argument('--auto', type=int, default=0, help='scan automatique toutes les N minutes (web)')
    ap.add_argument('--robots', action='store_true', help='respecter robots.txt (désactivé par défaut, comme la v1)')
    ap.add_argument('--sens', choices=('amplio', 'equilibrado', 'estricto'), default='equilibrado')
    ap.add_argument('--scan', choices=('all', 'fd', 'cyber', 'gov'), help='lance un scan puis quitte')
    ap.add_argument('--pages', type=int, default=PAGINAS_BUSQUEDA)
    ap.add_argument('--debug-fuente', metavar='NOM', help='diagnostic détaillé d\'une source (pourquoi 0 résultat)')
    a = ap.parse_args()
    if a.port:
        PUERTO = a.port
    AUTO_REFRESH_MIN, RESPETAR_ROBOTS, SENSIBILIDAD = a.auto, a.robots, a.sens
    if a.lang:
        IDIOMA_ACTUAL = a.lang
    elif not (a.web or a.scan or a.debug_fuente):
        seleccionar_idioma()
    init_globals()
    if a.debug_fuente:
        debug_fuente(a.debug_fuente)
        return
    if a.scan:
        ejecutar_actualizacion(a.scan, a.pages)
        return
    if a.web:
        servir_web(a.host)
        return
    mostrar_banner_inicial()
    st = gestor_global.estadisticas()
    cprint(f"📊 {st['total']} · ⏳ {gestor_global.datos.get('ultima_actualizacion') or '-'} · 📰 {len(fuentes_global)} · 🧬 UA: {len(USER_AGENTS)}", 'green')
    menu()


if __name__ == '__main__':
    main()
