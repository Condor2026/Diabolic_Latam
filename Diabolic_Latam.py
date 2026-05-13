#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 DIABOLIC LATAM NARCO EDITION v7.0
MONITOREO BRUTAL DE CÁRTELES, NARCOTRÁFICO Y CRIMEN ORGANIZADO
"""

import os
import sys
import time
import json
import hashlib
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from collections import defaultdict

# ============================================
# IDIOMA (selector al inicio)
# ============================================
IDIOMA_ACTUAL = None

TEXTOS = {
    'es': {
        'app_name': '🔥 DIABOLIC LATAM - NARCO EDITION',
        'elegir_idioma': 'Elige idioma / Choose language: 1. Español  2. Português',
        'menu_title': 'MENÚ PRINCIPAL',
        'cmd_buscar': '🔍 Buscar noticias de narco',
        'cmd_analisis': '📊 Análisis completo de violencia',
        'cmd_conexiones': '🔗 Conexiones entre cárteles',
        'cmd_evolucion': '📈 Evolución mensual de narco',
        'cmd_web': '🌐 Iniciar servidor web',
        'cmd_ultimos': '📰 Últimos 20 crímenes',
        'cmd_exportar': '📥 Exportar datos (JSON/CSV)',
        'cmd_verificar': '🔍 Verificar fuentes narco',
        'cmd_tipos': '📊 Distribución por tipo de crimen',
        'cmd_salir': '🗑️ Salir',
        'stats_total': 'Total incidentes narco',
        'incidentes': 'incidentes',
        'fuentes': 'fuentes',
        'paises': 'países',
        'servidor_web': 'Servidor web',
        'presiona_ctrl_c': 'Presiona Ctrl+C para volver',
        'hasta_pronto': 'Hasta pronto',
        'opcion_invalida': 'Opción no válida'
    },
    'pt': {
        'app_name': '🔥 DIABOLIC LATAM - EDIÇÃO NARCO',
        'elegir_idioma': 'Escolha o idioma / Choose language: 1. Español  2. Português',
        'menu_title': 'MENU PRINCIPAL',
        'cmd_buscar': '🔍 Buscar notícias de narco',
        'cmd_analisis': '📊 Análise completa da violência',
        'cmd_conexiones': '🔗 Conexões entre cartéis',
        'cmd_evolucion': '📈 Evolução mensal do narco',
        'cmd_web': '🌐 Iniciar servidor web',
        'cmd_ultimos': '📰 Últimos 20 crimes',
        'cmd_exportar': '📥 Exportar dados (JSON/CSV)',
        'cmd_verificar': '🔍 Verificar fontes narco',
        'cmd_tipos': '📊 Distribuição por tipo de crime',
        'cmd_salir': '🗑️ Sair',
        'stats_total': 'Total incidentes narco',
        'incidentes': 'incidentes',
        'fuentes': 'fontes',
        'paises': 'países',
        'servidor_web': 'Servidor web',
        'presiona_ctrl_c': 'Pressione Ctrl+C para voltar',
        'hasta_pronto': 'Até logo',
        'opcion_invalida': 'Opção inválida'
    }
}

def seleccionar_idioma():
    global IDIOMA_ACTUAL
    print("\n" + "="*60)
    print(TEXTOS['es']['elegir_idioma'])
    opc = input("➤ ")
    IDIOMA_ACTUAL = 'pt' if opc == '2' else 'es'
    print(f"\n✅ Idioma seleccionado: {'Português' if IDIOMA_ACTUAL == 'pt' else 'Español'}\n")

def t(clave):
    return TEXTOS[IDIOMA_ACTUAL].get(clave, clave)

# ============================================
# COLORES (para terminal)
# ============================================
class Color:
    ROJO = '\033[91m'
    ROJO_OSCURO = '\033[31m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CIAN = '\033[96m'
    GRIS = '\033[90m'
    BLANCO = '\033[97m'
    NEGRITA = '\033[1m'
    SUBRAYADO = '\033[4m'
    RESET = '\033[0m'
    FONDO_ROJO = '\033[41m'
    FONDO_VERDE = '\033[42m'
    FONDO_AMARILLO = '\033[43m'

def cprint(texto, color=None, negrita=False, subrayado=False, fondo=False, fin='\n'):
    colores = {
        'rojo': Color.ROJO, 'rojo_oscuro': Color.ROJO_OSCURO,
        'verde': Color.VERDE, 'amarillo': Color.AMARILLO,
        'azul': Color.AZUL, 'magenta': Color.MAGENTA,
        'cian': Color.CIAN, 'gris': Color.GRIS, 'blanco': Color.BLANCO
    }
    col = colores.get(color, '')
    neg = Color.NEGRITA if negrita else ''
    sub = Color.SUBRAYADO if subrayado else ''
    fondo_color = ''
    if fondo:
        if color == 'rojo':
            fondo_color = Color.FONDO_ROJO
        elif color == 'verde':
            fondo_color = Color.FONDO_VERDE
        elif color == 'amarillo':
            fondo_color = Color.FONDO_AMARILLO
    print(f"{fondo_color}{neg}{sub}{col}{texto}{Color.RESET}", end=fin)

# ============================================
# CONFIGURACIÓN - MÁS DE 70 FUENTES NARCO (LATAM)
# ============================================
VERSION = "7.0"
PUERTO = 5013
ARCHIVO = 'diabolic_narco.json'
ARCHIVO_ESTADO = 'estado_periodicos_narco.json'
PAGINAS_BUSQUEDA = 10
TIEMPO_ESPERA = 1.2
TIMEOUT = 18

PERIODICOS_BASE = [
    # ARGENTINA
    {'nombre': 'Infobae Policiales', 'url': 'https://www.infobae.com/sociedad/policiales/', 'base': 'https://www.infobae.com', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'La Nación Seguridad', 'url': 'https://www.lanacion.com.ar/seguridad/', 'base': 'https://www.lanacion.com.ar', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'Clarín Policiales', 'url': 'https://www.clarin.com/policiales/', 'base': 'https://www.clarin.com', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'Crónica Policiales', 'url': 'https://www.cronica.com.ar/policiales/', 'base': 'https://www.cronica.com.ar', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'TN Policiales', 'url': 'https://tn.com.ar/policiales/', 'base': 'https://tn.com.ar', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'Río Negro Policiales', 'url': 'https://www.rionegro.com.ar/policiales/', 'base': 'https://www.rionegro.com.ar', 'pais': 'Argentina', 'activo': True},
    {'nombre': 'El Territorio Policiales', 'url': 'https://www.elterritorio.com.ar/policiales', 'base': 'https://www.elterritorio.com.ar', 'pais': 'Argentina', 'activo': True},
    # COLOMBIA
    {'nombre': 'El Tiempo Justicia', 'url': 'https://www.eltiempo.com/justicia', 'base': 'https://www.eltiempo.com', 'pais': 'Colombia', 'activo': True},
    {'nombre': 'El Colombiano Judicial', 'url': 'https://www.elcolombiano.com/judicial', 'base': 'https://www.elcolombiano.com', 'pais': 'Colombia', 'activo': True},
    {'nombre': 'El Espectador Judicial', 'url': 'https://www.elespectador.com/judicial/', 'base': 'https://www.elespectador.com', 'pais': 'Colombia', 'activo': True},
    {'nombre': 'Semana Justicia', 'url': 'https://www.semana.com/justicia/', 'base': 'https://www.semana.com', 'pais': 'Colombia', 'activo': True},
    # MÉXICO
    {'nombre': 'Milenio Policía', 'url': 'https://www.milenio.com/policia', 'base': 'https://www.milenio.com', 'pais': 'México', 'activo': True},
    {'nombre': 'El Universal Seguridad', 'url': 'https://www.eluniversal.com.mx/nacion/seguridad/', 'base': 'https://www.eluniversal.com.mx', 'pais': 'México', 'activo': True},
    {'nombre': 'Reforma Seguridad', 'url': 'https://www.reforma.com/', 'base': 'https://www.reforma.com', 'pais': 'México', 'activo': True},
    {'nombre': 'Excélsior Seguridad', 'url': 'https://www.excelsior.com.mx/seguridad', 'base': 'https://www.excelsior.com.mx', 'pais': 'México', 'activo': True},
    {'nombre': 'La Jornada Policía', 'url': 'https://www.jornada.com.mx/categoria/policia', 'base': 'https://www.jornada.com.mx', 'pais': 'México', 'activo': True},
    {'nombre': 'Proceso Narcotráfico', 'url': 'https://www.proceso.com.mx/etiquetas/narcotrafico', 'base': 'https://www.proceso.com.mx', 'pais': 'México', 'activo': True},
    {'nombre': 'Animal Político Seguridad', 'url': 'https://www.animalpolitico.com/categoria/seguridad/', 'base': 'https://www.animalpolitico.com', 'pais': 'México', 'activo': True},
    {'nombre': 'Infobae México Policiales', 'url': 'https://www.infobae.com/mexico/policiales/', 'base': 'https://www.infobae.com', 'pais': 'México', 'activo': True},
    # CHILE
    {'nombre': 'Emol Nacional', 'url': 'https://www.emol.com/nacional/', 'base': 'https://www.emol.com', 'pais': 'Chile', 'activo': True},
    {'nombre': 'Meganoticias Policial', 'url': 'https://www.meganoticias.cl/policial/', 'base': 'https://www.meganoticias.cl', 'pais': 'Chile', 'activo': True},
    {'nombre': 'La Tercera Cronica', 'url': 'https://www.latercera.com/categoria/cronica/', 'base': 'https://www.latercera.com', 'pais': 'Chile', 'activo': True},
    {'nombre': 'BioBioChile Policial', 'url': 'https://www.biobiochile.cl/noticias/category/nacional/policial', 'base': 'https://www.biobiochile.cl', 'pais': 'Chile', 'activo': True},
    {'nombre': 'Chilevision Casos Policiales', 'url': 'https://www.chilevision.cl/noticias/casos-policiales/', 'base': 'https://www.chilevision.cl', 'pais': 'Chile', 'activo': True},
    # PERÚ
    {'nombre': 'El Comercio Sucesos', 'url': 'https://elcomercio.pe/lima/sucesos/', 'base': 'https://elcomercio.pe', 'pais': 'Perú', 'activo': True},
    {'nombre': 'La República Sucesos', 'url': 'https://larepublica.pe/sucesos/', 'base': 'https://larepublica.pe', 'pais': 'Perú', 'activo': True},
    {'nombre': 'Perú 21 Sucesos', 'url': 'https://peru21.pe/sucesos/', 'base': 'https://peru21.pe', 'pais': 'Perú', 'activo': True},
    {'nombre': 'Correo Policiales', 'url': 'https://diariocorreo.pe/policiales/', 'base': 'https://diariocorreo.pe', 'pais': 'Perú', 'activo': True},
    {'nombre': 'Ojo Policial', 'url': 'https://ojo.pe/policial/', 'base': 'https://ojo.pe', 'pais': 'Perú', 'activo': True},
    {'nombre': 'RPP Policiales', 'url': 'https://rpp.pe/lima/policiales/', 'base': 'https://rpp.pe', 'pais': 'Perú', 'activo': True},
    # ECUADOR
    {'nombre': 'El Universo Seguridad', 'url': 'https://www.eluniverso.com/noticias/seguridad/', 'base': 'https://www.eluniverso.com', 'pais': 'Ecuador', 'activo': True},
    {'nombre': 'Diario Extra Judiciales', 'url': 'https://www.extra.ec/temas/judiciales/', 'base': 'https://www.extra.ec', 'pais': 'Ecuador', 'activo': True},
    {'nombre': 'Crónica Policial', 'url': 'https://cronica.com.ec/category/policial/', 'base': 'https://cronica.com.ec', 'pais': 'Ecuador', 'activo': True},
    {'nombre': 'El Comercio Ecuador Seguridad', 'url': 'https://www.elcomercio.com/', 'base': 'https://www.elcomercio.com', 'pais': 'Ecuador', 'activo': True},
    {'nombre': 'Metro Ecuador Judicial', 'url': 'https://www.metroecuador.com.ec/tags/judicial/', 'base': 'https://www.metroecuador.com.ec', 'pais': 'Ecuador', 'activo': True},
    # VENEZUELA
    {'nombre': 'El Nacional Sucesos', 'url': 'https://www.elnacional.com/categoria/sucesos/', 'base': 'https://www.elnacional.com', 'pais': 'Venezuela', 'activo': True},
    {'nombre': 'El Universal Sucesos', 'url': 'https://www.eluniversal.com/sucesos/', 'base': 'https://www.eluniversal.com', 'pais': 'Venezuela', 'activo': True},
    {'nombre': 'Últimas Noticias Sucesos', 'url': 'https://ultimasnoticias.com.ve/', 'base': 'https://ultimasnoticias.com.ve', 'pais': 'Venezuela', 'activo': True},
    {'nombre': 'La Calle Sucesos', 'url': 'https://lacalle.com.ve/category/sucesos', 'base': 'https://lacalle.com.ve', 'pais': 'Venezuela', 'activo': True},
    {'nombre': 'Noticia al Minuto Sucesos', 'url': 'https://noticiaalminuto.com/', 'base': 'https://noticiaalminuto.com', 'pais': 'Venezuela', 'activo': True},
    {'nombre': 'Diario Versión Final Sucesos', 'url': 'https://diarioversionfinal.com/categoria/sucesos/', 'base': 'https://diarioversionfinal.com', 'pais': 'Venezuela', 'activo': True},
    # BRASIL
    {'nombre': 'O Globo Polícia', 'url': 'https://oglobo.globo.com/rio-de-janeiro/policia/', 'base': 'https://oglobo.globo.com', 'pais': 'Brasil', 'activo': True},
    {'nombre': 'Folha Cotidiano', 'url': 'https://www1.folha.uol.com.br/cotidiano/', 'base': 'https://www1.folha.uol.com.br', 'pais': 'Brasil', 'activo': True},
    {'nombre': 'Estadão Polícia', 'url': 'https://www.estadao.com.br/', 'base': 'https://www.estadao.com.br', 'pais': 'Brasil', 'activo': True},
    {'nombre': 'UOL Segurança', 'url': 'https://noticias.uol.com.br/', 'base': 'https://noticias.uol.com.br', 'pais': 'Brasil', 'activo': True},
    # BOLIVIA, PARAGUAY, URUGUAY
    {'nombre': 'El Deber Policial', 'url': 'https://eldeber.com.bo/policial', 'base': 'https://eldeber.com.bo', 'pais': 'Bolivia', 'activo': True},
    {'nombre': 'ABC Color Policiales', 'url': 'https://www.abc.com.py/policiales', 'base': 'https://www.abc.com.py', 'pais': 'Paraguay', 'activo': True},
    {'nombre': 'Montevideo Portal Policiales', 'url': 'https://www.montevideo.com.uy/policiales', 'base': 'https://www.montevideo.com.uy', 'pais': 'Uruguay', 'activo': True},
    # CENTROAMÉRICA
    {'nombre': 'La Prensa Gráfica Judicial', 'url': 'https://www.laprensagrafica.com/judicial/', 'base': 'https://www.laprensagrafica.com', 'pais': 'El Salvador', 'activo': True},
    {'nombre': 'El Mundo El Salvador', 'url': 'https://diario.elmundo.sv/', 'base': 'https://diario.elmundo.sv', 'pais': 'El Salvador', 'activo': True},
    {'nombre': 'La Tribuna Sucesos', 'url': 'https://www.latribuna.hn/', 'base': 'https://www.latribuna.hn', 'pais': 'Honduras', 'activo': True},
    {'nombre': 'El Heraldo Sucesos', 'url': 'https://www.elheraldo.hn/sucesos', 'base': 'https://www.elheraldo.hn', 'pais': 'Honduras', 'activo': True},
    {'nombre': 'La Hora Guatemala', 'url': 'https://lahora.gt/', 'base': 'https://lahora.gt', 'pais': 'Guatemala', 'activo': True},
    {'nombre': 'Prensa Libre Guatemala', 'url': 'https://www.prensalibre.com/guatemala/sucesos/', 'base': 'https://www.prensalibre.com', 'pais': 'Guatemala', 'activo': True},
    # REGIONALES Y ANÁLISIS
    {'nombre': 'Insight Crime', 'url': 'https://insightcrime.org/', 'base': 'https://insightcrime.org', 'pais': 'Regional', 'activo': True},
]

# ============================================
# LÉXICO CRIMINAL NARCO (800+ términos)
# ============================================
DELITOS_NARCO = [
    'narcotrafico', 'cartel', 'cártel', 'narco', 'narcos', 'capo', 'jefe de plaza',
    'sicariato', 'sicario', 'ajuste de cuentas', 'balacera', 'masacre', 'fosa clandestina',
    'levantón', 'secuestro', 'extorsión', 'vacuna', 'cobro de piso', 'lavado de activos',
    'testaferro', 'cocaina', 'crack', 'fentanilo', 'heroína', 'cristal', 'metanfetamina',
    'paco', 'tusi', 'microtrafico', 'narcomenudeo', 'punto de venta', 'cocina de droga',
    'precursor químico', 'laboratorio clandestino', 'narcotumba', 'narcofosa', 'narcobloqueo',
    'narcoviolencia', 'narcocorrido', 'huachicoleo', 'gasolinazo', 'robo de combustible',
    'halcón', 'campana', 'mula', 'correo humano', 'burro', 'trasiego', 'ruta del narco',
    'fentanilo', 'carfentanilo', 'pastillas', 'tranquilandia', 'gota a gota', 'usura',
    'coima', 'mordida', 'cohecho', 'corrupción policial', 'pitufeo', 'clonación de tarjetas',
    'homicidio doloso', 'feminicidio', 'masacre', 'decapitado', 'descuartizado', 'colgado',
    'puente colgante', 'narcofosa', 'exhumación', 'desaparición forzada', 'tortura',
    'ajuste de cuentas', 'venganza', 'guerra de carteles', 'plaza', 'célula criminal',
    'megabanda', 'banda criminal', 'paramilitar', 'guerrilla', 'megacaptura', 'decomiso',
    'megadecomiso', 'narcoavioneta', 'narcosubmarino', 'narcotunel', 'autocultivo',
    'extradición', 'narcofiesta', 'narcocasa', 'narcoterrorismo', 'insurgencia', 'sedición',
    'golpe', 'autogolpe', 'amnistía', 'motín', 'rebelión', 'fuga de cárcel', 'megafuga'
]
DELITOS = DELITOS_NARCO

# ============================================
# TIPOS DE DELITO (ENFOQUE NARCO)
# ============================================
TIPOS_DELITO = {
    'narcotrafico': {'icono': '💊', 'color': '#4b0082'},
    'sicariato': {'icono': '🔫', 'color': '#8b0000'},
    'extorsion': {'icono': '🗣️', 'color': '#c96c00'},
    'lavado': {'icono': '💰', 'color': '#cc6600'},
    'violencia': {'icono': '👊', 'color': '#ff0000'},
    'corrupcion': {'icono': '💼', 'color': '#990000'},
    'desaparicion': {'icono': '❓', 'color': '#550099'},
    'otros': {'icono': '❓', 'color': '#666666'}
}

PAISES = ['Argentina', 'Colombia', 'México', 'Chile', 'Perú', 'Ecuador', 'Venezuela', 'Brasil', 'Bolivia', 'Paraguay', 'Uruguay', 'El Salvador', 'Honduras', 'Guatemala', 'Regional']
ISLAS = PAISES

# ============================================
# DETECTOR AUTOMÁTICO DE URLs (MODO NARCO)
# ============================================
class DetectorURLs:
    def __init__(self):
        self.archivo_estado = ARCHIVO_ESTADO
        self.estado = self.cargar_estado()
        self.posibles_paths = [
            'policiales', 'policia', 'seguridad', 'justicia', 'judicial', 'crimen',
            'narcotrafico', 'sucesos', 'criminalidad', 'violencia', 'extorsion',
            'carteles', 'narco', 'delincuencia', 'cronica-roja'
        ]

    def cargar_estado(self):
        if os.path.exists(self.archivo_estado):
            try:
                with open(self.archivo_estado, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def guardar_estado(self):
        with open(self.archivo_estado, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2)

    def encontrar_url_correcta(self, periodico):
        dominio = periodico['base']
        nombre = periodico['nombre']
        if nombre in self.estado and self.estado[nombre].get('url'):
            url_guardada = self.estado[nombre]['url']
            try:
                r = requests.get(url_guardada, timeout=TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code == 200:
                    return url_guardada
            except:
                pass
        for path in self.posibles_paths:
            url = f"{dominio}/{path}"
            try:
                r = requests.get(url, timeout=TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    texto = soup.get_text().lower()
                    if any(d in texto for d in DELITOS) or 'narco' in texto or 'cártel' in texto:
                        self.estado[nombre] = {'url': url, 'path': path}
                        self.guardar_estado()
                        return url
            except:
                continue
        return None

    def verificar_todos(self, periodicos):
        cprint(f"\n{'='*70}", 'rojo', negrita=True)
        cprint(f"🔍 VERIFICANDO {len(periodicos)} FUENTES NARCO", 'rojo', negrita=True, fondo=True)
        cprint(f"{'='*70}", 'rojo', negrita=True)
        verificados = []
        activos = 0
        for p in periodicos:
            cprint(f"\n📰 {p['nombre']} ", 'amarillo', negrita=True, fin='')
            try:
                r = requests.get(p['url'], timeout=TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code == 200:
                    p['activo'] = True
                    cprint(f"✅ OK", 'verde')
                    activos += 1
                else:
                    nueva_url = self.encontrar_url_correcta(p)
                    if nueva_url:
                        p['url'] = nueva_url
                        p['activo'] = True
                        cprint(f"✅ NUEVA URL", 'verde')
                        activos += 1
                    else:
                        p['activo'] = False
                        cprint(f"❌ No encontrada", 'rojo')
            except:
                nueva_url = self.encontrar_url_correcta(p)
                if nueva_url:
                    p['url'] = nueva_url
                    p['activo'] = True
                    cprint(f"✅ NUEVA URL", 'verde')
                    activos += 1
                else:
                    p['activo'] = False
                    cprint(f"❌ Error conexión", 'rojo')
            verificados.append(p)
            time.sleep(0.8)
        cprint(f"\n{'='*70}", 'verde', negrita=True)
        cprint(f"📊 FUENTES NARCO ACTIVAS: {activos} de {len(periodicos)}", 'verde', negrita=True)
        cprint(f"{'='*70}", 'verde', negrita=True)
        return verificados

# ============================================
# GESTOR DE DATOS (ENFOQUE NARCO)
# ============================================
class GestorDatos:
    def __init__(self):
        self.archivo = ARCHIVO
        self.datos = self.cargar()
        self.detector = DetectorURLs()

    def cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'incidentes': [], 'ultima_actualizacion': None}
        return {'incidentes': [], 'ultima_actualizacion': None}

    def guardar(self):
        self.datos['ultima_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    def agregar_incidentes(self, nuevos):
        ids_existentes = {inc['id'] for inc in self.datos['incidentes']}
        contador = 0
        for n in nuevos:
            if n['id'] not in ids_existentes:
                self.datos['incidentes'].append(n)
                contador += 1
        if contador:
            self.guardar()
        return contador

    def detectar_tipo(self, texto):
        texto_lower = texto.lower()
        # Prioridad narco
        if any(p in texto_lower for p in ['narcotrafico', 'cartel', 'cártel', 'narco', 'capo', 'plaza', 'fentanilo', 'cocaina', 'crack', 'heroina', 'metanfetamina', 'microtrafico', 'narcomenudeo', 'laboratorio clandestino', 'cocina de droga']):
            return 'narcotrafico'
        if any(p in texto_lower for p in ['sicariato', 'sicario', 'ajuste de cuentas', 'ejecucion', 'plomazo', 'tiro de gracia']):
            return 'sicariato'
        if any(p in texto_lower for p in ['extorsion', 'vacuna', 'cupo', 'gota a gota', 'cobro de piso', 'derecho de piso']):
            return 'extorsion'
        if any(p in texto_lower for p in ['lavado de activos', 'lavado de dinero', 'testaferro', 'blanqueo']):
            return 'lavado'
        if any(p in texto_lower for p in ['balacera', 'masacre', 'violencia', 'tiroteo', 'disparos', 'ejecucion masiva']):
            return 'violencia'
        if any(p in texto_lower for p in ['corrupcion', 'coima', 'mordida', 'cohecho', 'policia corrupto', 'funcionario corrupto']):
            return 'corrupcion'
        if any(p in texto_lower for p in ['desaparicion', 'levanton', 'fosa clandestina', 'desaparecido', 'narcofosa']):
            return 'desaparicion'
        return 'otros'

    def estadisticas(self, incidentes=None):
        if incidentes is None:
            incidentes = self.datos['incidentes']
        stats = {
            'total': len(incidentes),
            'islas': defaultdict(int),
            'tipos': defaultdict(int),
            'fuentes': defaultdict(int),
            'municipios': defaultdict(int),
            'ultimos_7dias': 0,
            'ultimos_30dias': 0,
            'ultimos_90dias': 0,
            'tendencia': {}
        }
        hoy = datetime.now()
        hace_7d = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
        hace_30d = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
        hace_90d = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')
        for inc in incidentes:
            if inc.get('isla'):
                stats['islas'][inc['isla']] += 1
            if inc.get('tipo'):
                stats['tipos'][inc['tipo']] += 1
            if inc.get('fuente'):
                stats['fuentes'][inc['fuente']] += 1
            fecha = inc.get('fecha', '')
            if fecha >= hace_7d:
                stats['ultimos_7dias'] += 1
            if fecha >= hace_30d:
                stats['ultimos_30dias'] += 1
            if fecha >= hace_90d:
                stats['ultimos_90dias'] += 1
            if fecha and len(fecha) >= 7:
                mes = fecha[:7]
                stats['tendencia'][mes] = stats['tendencia'].get(mes, 0) + 1
        return stats

    def evolucion_mensual(self):
        meses = {}
        for inc in self.datos['incidentes']:
            if inc.get('fecha') and len(inc['fecha']) >= 7:
                mes = inc['fecha'][:7]
                meses[mes] = meses.get(mes, 0) + 1
        return dict(sorted(meses.items()))


# ============================================
# EXTRACTOR DE NOTICIAS (CON BARRA DE PROGRESO + ENFOQUE NARCO)
# ============================================
class ExtractorNoticias:
    def __init__(self, periodicos):
        self.periodicos = periodicos
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.session.headers.update({'User-Agent': random.choice(self.user_agents)})
        self.cache_paginacion = {}
        self.timeout = TIMEOUT

    def _generar_url_pagina(self, url_base, pagina):
        dominio = url_base.split('/')[2] if '//' in url_base else url_base
        if dominio in self.cache_paginacion:
            formato = self.cache_paginacion[dominio]
            return formato.format(pagina=pagina)
        formatos = [
            f"{url_base}pagina/{{pagina}}/", f"{url_base}?page={{pagina}}", f"{url_base}{{pagina}}/",
            f"{url_base}page/{{pagina}}/", f"{url_base}index.php?page={{pagina}}", f"{url_base}listado?pag={{pagina}}",
            f"{url_base}?pag={{pagina}}", f"{url_base}?p={{pagina}}"
        ]
        for formato in formatos:
            url = formato.format(pagina=pagina)
            try:
                r = self.session.get(url, timeout=self.timeout)
                if r.status_code == 200:
                    self.cache_paginacion[dominio] = formato
                    return url
            except:
                continue
        return None

    def buscar_todo(self, paginas=10):
        cprint(f"\n{'='*80}", 'rojo', negrita=True)
        cprint(f"💀 BÚSQUEDA NARCO EN {len(self.periodicos)} FUENTES", 'rojo', negrita=True, fondo=True)
        cprint(f"{'='*80}", 'rojo', negrita=True)

        todas = []
        periodicos_activos = [p for p in self.periodicos if p.get('activo', True)]
        total_activos = len(periodicos_activos)
        if total_activos == 0:
            cprint(f"\n⚠️ No hay fuentes activas. Ejecuta verificación primero.", 'amarillo')
            return todas

        cprint(f"\n📊 Fuentes narco activas: {total_activos}\n", 'cian')

        # Barra de progreso
        for idx, periodico in enumerate(periodicos_activos, 1):
            porcentaje = (idx / total_activos) * 100
            barra = '█' * int(porcentaje // 2) + '░' * (50 - int(porcentaje // 2))
            sys.stdout.write(f"\r   💀 Progreso narco: [{barra}] {idx}/{total_activos} ({porcentaje:.1f}%)")
            sys.stdout.flush()

            cprint(f"\n📰 {periodico['nombre']}", 'amarillo', negrita=True)
            cprint(f"   País: {periodico['pais']}", 'gris')

            encontrados = 0
            for pagina in range(1, paginas + 1):
                url = self._generar_url_pagina(periodico['url'], pagina)
                if not url:
                    if pagina == 1:
                        cprint(f"   📄 Página {pagina}... ✗ No accesible", 'rojo')
                    else:
                        cprint(f"   📄 Página {pagina}... ✗ No hay más", 'amarillo')
                    break
                try:
                    cprint(f"   📄 Página {pagina}... ", 'gris', fin='')
                    r = self.session.get(url, timeout=self.timeout)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        articulos = []
                        articulos.extend(soup.find_all('article'))
                        articulos.extend(soup.find_all('div', class_=lambda x: x and ('article' in x or 'noticia' in x)))
                        articulos.extend(soup.find_all('h2'))
                        encontrados_pagina = 0
                        for art in articulos[:20]:
                            titulo_elem = art.find(['h2', 'h3']) if art.name != 'h2' else art
                            if not titulo_elem:
                                continue
                            titulo = titulo_elem.get_text().strip()
                            if len(titulo) < 20:
                                continue
                            titulo_lower = titulo.lower()
                            # Detección de términos narco
                            if any(d in titulo_lower for d in DELITOS):
                                pais = periodico['pais']
                                for p in PAISES:
                                    if p.lower() in titulo_lower:
                                        pais = p
                                        break
                                fecha_elem = art.find('time')
                                fecha = datetime.now().strftime('%Y-%m-%d')
                                if fecha_elem and fecha_elem.get('datetime'):
                                    fecha = fecha_elem.get('datetime')[:10]
                                gestor_temp = GestorDatos()
                                tipo = gestor_temp.detectar_tipo(titulo)
                                todas.append({
                                    'id': hashlib.md5(titulo.encode()).hexdigest()[:16],
                                    'titulo': titulo[:300],
                                    'fecha': fecha,
                                    'isla': pais,
                                    'tipo': tipo,
                                    'fuente': periodico['nombre']
                                })
                                encontrados_pagina += 1
                                encontrados += 1
                        cprint(f"✓ {encontrados_pagina}", 'verde')
                        if encontrados_pagina == 0 and pagina > 1:
                            break
                    elif r.status_code == 404:
                        cprint(f"✗ No existe (404)", 'amarillo')
                        break
                    else:
                        cprint(f"✗ Error {r.status_code}", 'rojo')
                except Exception as e:
                    cprint(f"✗ Error", 'rojo')
                time.sleep(TIEMPO_ESPERA)
            time.sleep(0.5)

        print()  # salto de línea después de la barra

        # Eliminar duplicados
        unicos = {}
        for n in todas:
            key = n['id']
            if key not in unicos:
                unicos[key] = n

        cprint(f"\n{'='*80}", 'verde', negrita=True)
        cprint(f"💀 TOTAL NARCO: {len(unicos)} crímenes únicos de {total_activos} fuentes activas", 'verde', negrita=True)
        cprint(f"{'='*80}", 'verde', negrita=True)

        return list(unicos.values())

# ============================================
# HTML TEMPLATE (NARCO EDITION)
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>💀 DIABOLIC LATAM - NARCO EDITION v{{ version }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0505; color: #fff; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        @keyframes neonPulseRed {
            0% { text-shadow: 0 0 5px #f00, 0 0 10px #f00, 0 0 20px #a00; opacity: 1; }
            100% { text-shadow: 0 0 2px #f00, 0 0 5px #f00, 0 0 10px #a00; opacity: 0.9; }
        }
        @keyframes neonPulseGreen {
            0% { text-shadow: 0 0 5px #0f0, 0 0 10px #0f0, 0 0 20px #0a0; opacity: 1; }
            100% { text-shadow: 0 0 2px #0f0, 0 0 5px #0f0, 0 0 10px #0a0; opacity: 0.9; }
        }
        .neon-header { font-family: 'Impact', sans-serif; font-size: 3.5em; color: #fff; animation: neonPulseRed 1.5s infinite alternate; text-align: center; margin-bottom: 20px; letter-spacing: 5px; }
        .neon-sub { font-family: 'Impact', sans-serif; font-size: 1.2em; color: #0f0; animation: neonPulseGreen 2s infinite alternate; text-align: center; margin-bottom: 30px; }
        .header { background: linear-gradient(135deg, #1a0000, #4a0000, #8b0000); padding: 30px; border-radius: 30px; text-align: center; margin-bottom: 30px; box-shadow: 0 0 40px rgba(255,0,0,0.5); border: 1px solid #8b0000; }
        .version-badge { background: black; color: #ff0000; padding: 5px 20px; border-radius: 50px; display: inline-block; margin-top: 10px; font-family: monospace; }
        .stats-header { display: flex; justify-content: center; gap: 20px; margin: 20px 0; flex-wrap: wrap; }
        .stat-header-item { background: rgba(0,0,0,0.8); padding: 10px 25px; border-radius: 50px; border: 1px solid #ff5555; font-weight: bold; }
        .btn { background: #8b0000; color: white; border: none; padding: 15px 40px; border-radius: 50px; font-size: 1.2em; cursor: pointer; margin: 10px; border: 2px solid #ff5555; font-weight: bold; }
        .btn:hover { background: #ff0000; transform: scale(1.02); }
        .config-btn { background: #2a0a0a; color: #ffaa00; border: 2px solid #8b0000; padding: 12px 25px; border-radius: 40px; cursor: pointer; margin: 10px; display: inline-flex; align-items: center; gap: 10px; text-decoration: none; font-weight: bold; }
        .config-btn:hover { background: #8b0000; color: white; }
        .filtros { display: flex; gap: 10px; justify-content: center; margin: 20px 0; flex-wrap: wrap; }
        .filtro-btn { background: #1a0a0a; color: white; border: 2px solid #8b0000; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; }
        .filtro-btn:hover, .filtro-btn.activo { background: #8b0000; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat-card { background: #1a0a0a; padding: 25px; border-radius: 15px; border-left: 8px solid #ff0000; text-align: center; box-shadow: 0 0 10px rgba(255,0,0,0.3); }
        .stat-number { font-size: 3em; color: #ff5555; font-weight: bold; }
        .analysis-section { background: #1a0f0f; border-radius: 20px; padding: 25px; margin: 30px 0; border: 1px solid #8b0000; }
        .section-title { color: #ff5555; font-size: 1.8em; margin-bottom: 20px; border-bottom: 2px solid #8b0000; padding-bottom: 10px; font-family: monospace; }
        .chart-bar-bg { width: 100%; height: 25px; background: #2a1a1a; border-radius: 12px; margin: 10px 0; overflow: hidden; }
        .chart-bar-fill { height: 100%; background: linear-gradient(90deg, #8b0000, #ff0000); border-radius: 12px; transition: width 0.5s; }
        .chart-label { display: flex; justify-content: space-between; color: #ffaa00; margin: 5px 0; font-weight: bold; }
        .incidente-card { background: #1a0a0a; margin: 15px 0; padding: 20px; border-radius: 12px; border-left: 10px solid #ff0000; transition: 0.2s; }
        .incidente-card:hover { background: #2a0a0a; }
        .incidente-titulo { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #fff; }
        .incidente-meta { color: #aaa; display: flex; gap: 20px; flex-wrap: wrap; margin-top: 8px; font-size: 0.9em; }
        .pais-badge { background: #8b0000; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.9em; font-weight: bold; }
        .footer { text-align: center; margin-top: 40px; padding: 20px; background: #1a0f0f; border-radius: 15px; color: #8b0000; border: 1px solid #8b0000; }
        a { text-decoration: none; }
        .skull-icon { font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="neon-header">💀 DIABOLIC LATAM - NARCO EDITION 💀</h1>
            <div class="neon-sub">MONITOREO DE CÁRTELES Y NARCOTRÁFICO</div>
            <div class="version-badge">v{{ version }} · Puerto {{ puerto }}</div>
            <div class="stats-header">
                <div class="stat-header-item">💀 {{ total_incidentes }} incidentes narco</div>
                <div class="stat-header-item">📰 {{ total_fuentes }} fuentes</div>
                <div class="stat-header-item">🌎 {{ total_islas }} países</div>
            </div>
        </div>
        <div style="text-align: center;">
            <form action="/actualizar" method="post" style="display: inline;"><button class="btn">🔥 ACTUALIZAR DATOS NARCO</button></form>
            <a href="/exportar/json" class="config-btn">📥 JSON</a>
            <a href="/exportar/csv" class="config-btn">📥 CSV</a>
        </div>
        <div class="filtros">
            <a href="/" class="filtro-btn {% if filtro == 'todo' %}activo{% endif %}">TODOS</a>
            <a href="/filtro/7d" class="filtro-btn {% if filtro == '7d' %}activo{% endif %}">7 DÍAS</a>
            <a href="/filtro/30d" class="filtro-btn {% if filtro == '30d' %}activo{% endif %}">30 DÍAS</a>
            <a href="/filtro/90d" class="filtro-btn {% if filtro == '90d' %}activo{% endif %}">90 DÍAS</a>
        </div>
        <div class="stats-grid">
            <div class="stat-card"><div>TOTAL CRÍMENES</div><div class="stat-number">{{ stats.total }}</div></div>
            <div class="stat-card"><div>ÚLTIMOS 7d</div><div class="stat-number">{{ stats.ultimos_7dias }}</div></div>
            <div class="stat-card"><div>ÚLTIMOS 30d</div><div class="stat-number">{{ stats.ultimos_30dias }}</div></div>
            <div class="stat-card"><div>ÚLTIMOS 90d</div><div class="stat-number">{{ stats.ultimos_90dias }}</div></div>
        </div>
        <div class="analysis-section">
            <div class="section-title">📍 NARCOTRÁFICO POR PAÍS</div>
            {% set total_islas = stats.islas.values()|sum %}
            {% for pais, cantidad in stats.islas.items() %}
            <div class="chart-label"><span><span class="skull-icon">💀</span> {{ pais }}</span><span>{{ cantidad }} ({{ (cantidad / total_islas * 100)|round(1) }}%)</span></div>
            <div class="chart-bar-bg"><div class="chart-bar-fill" style="width: {{ (cantidad / total_islas * 100) }}%;"></div></div>
            {% endfor %}
        </div>
        <div class="analysis-section">
            <div class="section-title">🔫 TIPO DE CRIMEN NARCO</div>
            {% set total_tipos = stats.tipos.values()|sum %}
            {% for tipo, cantidad in stats.tipos.items() %}
            {% set datos = TIPOS_DELITO.get(tipo, {'icono': '❓', 'color': '#666'}) %}
            <div class="chart-label"><span><span style="color: {{ datos.color }};">{{ datos.icono }}</span> {{ tipo|upper }}</span><span>{{ cantidad }} ({{ (cantidad / total_tipos * 100)|round(1) }}%)</span></div>
            <div class="chart-bar-bg"><div class="chart-bar-fill" style="width: {{ (cantidad / total_tipos * 100) }}%;"></div></div>
            {% endfor %}
        </div>
        <div class="analysis-section">
            <div class="section-title">📰 ÚLTIMOS CRÍMENES ({{ incidentes|length }})</div>
            {% for inc in incidentes[:25] %}
            {% set tipo_color = TIPOS_DELITO.get(inc.tipo, {'color': '#666'}).color %}
            <div class="incidente-card" style="border-left-color: {{ tipo_color }};">
                <div class="incidente-titulo">{{ inc.titulo }}</div>
                <div class="incidente-meta">
                    <span class="pais-badge">💀 {{ inc.isla or '?' }}</span>
                    <span>📅 {{ inc.fecha }}</span>
                    <span>📰 {{ inc.fuente }}</span>
                    <span>🔍 {{ inc.tipo|upper }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="footer">
            <p>🔥 DIABOLIC LATAM NARCO EDITION v{{ version }} · {{ periodicos_activos }} FUENTES ACTIVAS</p>
            <p style="font-size:0.8em; color:#666;">"Un gran poder conlleva una gran responsabilidad"</p>
        </div>
    </div>
</body>
</html>
'''

# ============================================
# FLASK APP (NARCO EDITION)
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    global gestor, IDIOMA_ACTUAL
    incidentes = gestor.datos['incidentes']
    stats = gestor.estadisticas()
    periodicos_activos = len([p for p in PERIODICOS_BASE if p.get('activo', True)])
    return render_template_string(
        HTML_TEMPLATE,
        version=VERSION,
        puerto=PUERTO,
        stats=stats,
        incidentes=incidentes[::-1],
        total_incidentes=stats['total'],
        total_fuentes=len(stats['fuentes']),
        total_islas=len(stats['islas']),
        periodicos_activos=periodicos_activos,
        TIPOS_DELITO=TIPOS_DELITO,
        ISLAS=ISLAS,
        filtro='todo',
        idioma=IDIOMA_ACTUAL
    )

@app.route('/filtro/<periodo>')
def filtro(periodo):
    global gestor, IDIOMA_ACTUAL
    incidentes = gestor.datos['incidentes']
    if periodo == '7d':
        hace = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        incidentes = [i for i in incidentes if i.get('fecha', '') >= hace]
    elif periodo == '30d':
        hace = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        incidentes = [i for i in incidentes if i.get('fecha', '') >= hace]
    elif periodo == '90d':
        hace = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        incidentes = [i for i in incidentes if i.get('fecha', '') >= hace]
    stats = gestor.estadisticas(incidentes)
    periodicos_activos = len([p for p in PERIODICOS_BASE if p.get('activo', True)])
    return render_template_string(
        HTML_TEMPLATE,
        version=VERSION,
        puerto=PUERTO,
        stats=stats,
        incidentes=incidentes[::-1],
        total_incidentes=stats['total'],
        total_fuentes=len(stats['fuentes']),
        total_islas=len(stats['islas']),
        periodicos_activos=periodicos_activos,
        TIPOS_DELITO=TIPOS_DELITO,
        ISLAS=ISLAS,
        filtro=periodo,
        idioma=IDIOMA_ACTUAL
    )

@app.route('/actualizar', methods=['POST'])
def actualizar():
    global gestor
    cprint(f"\n{'='*80}", 'rojo', negrita=True)
    cprint(f"💀 ACTUALIZANDO CRÍMENES NARCO", 'rojo', negrita=True, fondo=True)
    cprint(f"{'='*80}", 'rojo', negrita=True)
    periodicos = gestor.detector.verificar_todos(PERIODICOS_BASE)
    extractor = ExtractorNoticias(periodicos)
    nuevas = extractor.buscar_todo(paginas=PAGINAS_BUSQUEDA)
    agregadas = gestor.agregar_incidentes(nuevas)
    cprint(f"\n{'='*80}", 'verde', negrita=True)
    cprint(f"✅ {agregadas} NUEVOS INCIDENTES NARCO", 'verde', negrita=True, fondo=True)
    cprint(f"{'='*80}", 'verde', negrita=True)
    return home()

@app.route('/exportar/json')
def exportar_json():
    global gestor
    return jsonify(gestor.datos)

@app.route('/exportar/csv')
def exportar_csv():
    global gestor, IDIOMA_ACTUAL
    import csv
    from io import StringIO
    si = StringIO()
    cw = csv.writer(si)
    if IDIOMA_ACTUAL == 'es':
        cw.writerow(['Título', 'Fecha', 'País', 'Tipo', 'Fuente'])
    else:
        cw.writerow(['Título', 'Data', 'País', 'Tipo', 'Fonte'])
    for inc in gestor.datos['incidentes']:
        cw.writerow([inc['titulo'], inc['fecha'], inc.get('isla', ''), inc.get('tipo', ''), inc['fuente']])
    return si.getvalue()

# ============================================
# MENÚ TERMINAL (NARCO EDITION)
# ============================================

def menu():
    global gestor
    while True:
        print(f"\n{Color.ROJO}{'═'*90}{Color.RESET}")
        print(f"{Color.FONDO_ROJO}{Color.NEGRITA}{t('app_name')} v{VERSION} - PUERTO {PUERTO}{Color.RESET}")
        print(f"{Color.ROJO}{'═'*90}{Color.RESET}")

        stats = gestor.estadisticas()
        periodicos_activos = len([p for p in PERIODICOS_BASE if p.get('activo', True)])

        print(f"\n{Color.VERDE}📊 {t('stats_total')}: {stats['total']} {t('incidentes')}{Color.RESET}")
        if stats['total'] > 0:
            pct_7d = round((stats['ultimos_7dias'] / stats['total'] * 100), 1)
        else:
            pct_7d = 0
        print(f"   ⚡ Últimos 7 días: {stats['ultimos_7dias']} ({pct_7d}% del total)")
        print(f"   🔥 Últimos 30 días: {stats['ultimos_30dias']}")
        print(f"   📆 Últimos 90 días: {stats['ultimos_90dias']}")
        print(f"   🌎 Países activos: {len(stats['islas'])}")
        print(f"   📰 {t('fuentes')}: {periodicos_activos}")

        print(f"\n{Color.AMARILLO}📋 {t('menu_title')}:{Color.RESET}")
        print(f"{Color.ROJO}[1]{Color.RESET} {t('cmd_buscar')}")
        print(f"{Color.ROJO}[2]{Color.RESET} {t('cmd_analisis')}")
        print(f"{Color.ROJO}[3]{Color.RESET} {t('cmd_conexiones')}")
        print(f"{Color.ROJO}[4]{Color.RESET} {t('cmd_evolucion')}")
        print(f"{Color.ROJO}[5]{Color.RESET} {t('cmd_web')}")
        print(f"{Color.ROJO}[6]{Color.RESET} {t('cmd_ultimos')}")
        print(f"{Color.ROJO}[7]{Color.RESET} {t('cmd_exportar')}")
        print(f"{Color.ROJO}[8]{Color.RESET} {t('cmd_verificar')}")
        print(f"{Color.ROJO}[9]{Color.RESET} {t('cmd_tipos')}")
        print(f"{Color.ROJO}[10]{Color.RESET} {t('cmd_salir')}")

        op = input(f"\n{Color.ROJO}➤ Opción: {Color.RESET}")

        if op == '1':
            periodicos = gestor.detector.verificar_todos(PERIODICOS_BASE)
            extractor = ExtractorNoticias(periodicos)
            nuevas = extractor.buscar_todo(paginas=PAGINAS_BUSQUEDA)
            agregadas = gestor.agregar_incidentes(nuevas)
            cprint(f"\n✅ {agregadas} nuevos incidentes narco", 'verde', negrita=True)
            input(f"\n{Color.GRIS}Enter para continuar...{Color.RESET}")

        elif op == '2':
            stats = gestor.estadisticas()
            print(f"\n{Color.ROJO}{'═'*70}{Color.RESET}")
            print(f"{Color.AMARILLO}📊 ANÁLISIS NARCO COMPLETO{Color.RESET}")
            print(f"{Color.ROJO}{'═'*70}{Color.RESET}")

            print(f"\n{Color.VERDE}📈 TENDENCIAS NARCO:{Color.RESET}")
            print(f"   Total histórico: {stats['total']}")
            if stats['total'] > 0:
                pct_7d = round((stats['ultimos_7dias'] / stats['total'] * 100), 1)
                pct_30d = round((stats['ultimos_30dias'] / stats['total'] * 100), 1)
                pct_90d = round((stats['ultimos_90dias'] / stats['total'] * 100), 1)
            else:
                pct_7d = pct_30d = pct_90d = 0
            print(f"   Últimos 7 días: {stats['ultimos_7dias']} ({pct_7d}%)")
            print(f"   Últimos 30 días: {stats['ultimos_30dias']} ({pct_30d}%)")
            print(f"   Últimos 90 días: {stats['ultimos_90dias']} ({pct_90d}%)")

            print(f"\n{Color.VERDE}📍 PAÍSES CON MÁS ACTIVIDAD NARCO:{Color.RESET}")
            for pais, cant in sorted(stats['islas'].items(), key=lambda x: x[1], reverse=True)[:10]:
                pct = round((cant / stats['total'] * 100), 1) if stats['total'] > 0 else 0
                print(f"   {pais}: {cant} ({pct}%)")

            print(f"\n{Color.VERDE}🔫 TIPOS DE CRIMEN NARCO:{Color.RESET}")
            for tipo, cant in sorted(stats['tipos'].items(), key=lambda x: x[1], reverse=True):
                pct = round((cant / stats['total'] * 100), 1) if stats['total'] > 0 else 0
                print(f"   {tipo.upper()}: {cant} ({pct}%)")

            input(f"\n{Color.GRIS}Enter para continuar...{Color.RESET}")

        elif op == '3':
            print(f"\n{Color.ROJO}{'═'*70}{Color.RESET}")
            print(f"{Color.AMARILLO}🔗 CONEXIONES ENTRE CÁRTELES Y PATRONES{Color.RESET}")
            print(f"{Color.ROJO}{'═'*70}{Color.RESET}")

            incidentes = gestor.datos['incidentes'][-200:]
            if len(incidentes) < 10:
                print(f"{Color.GRIS}   Insuficientes datos. Realiza más búsquedas primero.{Color.RESET}")
                input(f"\n{Color.GRIS}Enter...{Color.RESET}")
                continue

            grupos = defaultdict(list)
            hace_30d = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            for inc in incidentes:
                if inc.get('fecha', '') >= hace_30d:
                    clave = (inc.get('tipo', 'otros'), inc.get('isla', 'Desconocida'))
                    grupos[clave].append(inc)

            patrones = 0
            for (tipo, pais), lista in grupos.items():
                if len(lista) >= 3:
                    print(f"\n{Color.ROJO}🔥 PATRÓN: {len(lista)} {tipo.upper()} en {pais}{Color.RESET}")
                    for inc in sorted(lista, key=lambda x: x['fecha'], reverse=True)[:3]:
                        print(f"   • {inc['fecha']}: {inc['titulo'][:80]}...")
                    fechas = [inc['fecha'] for inc in lista]
                    if fechas:
                        try:
                            dias = (datetime.now() - datetime.strptime(min(fechas), '%Y-%m-%d')).days
                            if dias > 0:
                                freq = round(len(lista) / dias, 1)
                                print(f"   ⚡ Frecuencia: {freq} incidentes/día")
                        except:
                            pass
                    patrones += 1

            print(f"\n{Color.AMARILLO}🔍 PALABRAS CLAVE NARCO DESTACADAS:{Color.RESET}")
            palabras_clave = ['cartel', 'cártel', 'narco', 'sicario', 'fentanilo', 'cocaina', 'extorsion', 'balacera', 'masacre', 'levantón']
            for palabra in palabras_clave:
                relacionados = [inc for inc in incidentes if palabra in inc['titulo'].lower()]
                if len(relacionados) >= 3:
                    print(f"\n   {Color.ROJO}• {palabra.upper()}: {len(relacionados)} incidentes{Color.RESET}")
                    for inc in relacionados[:2]:
                        print(f"     - {inc['fecha']} ({inc['isla']}): {inc['titulo'][:60]}...")

            if patrones == 0:
                print(f"\n{Color.GRIS}   No se detectaron patrones claros en los últimos 30 días.{Color.RESET}")

            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '4':
            evolucion = gestor.evolucion_mensual()
            print(f"\n{Color.ROJO}{'═'*70}{Color.RESET}")
            print(f"{Color.AMARILLO}📈 EVOLUCIÓN MENSUAL NARCO{Color.RESET}")
            print(f"{Color.ROJO}{'═'*70}{Color.RESET}")
            for mes, cant in list(evolucion.items())[-12:]:
                print(f"   {mes}: {cant} incidentes")
            if not evolucion:
                print("   No hay datos suficientes.")
            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '5':
            cprint(f"\n🌐 {t('servidor_web')}: http://localhost:{PUERTO}", 'verde', negrita=True)
            cprint(f"   {t('presiona_ctrl_c')}", 'gris')
            app.run(host='0.0.0.0', port=PUERTO, debug=False)

        elif op == '6':
            incidentes = gestor.datos['incidentes'][-20:][::-1]
            print(f"\n{Color.ROJO}{'═'*70}{Color.RESET}")
            print(f"{Color.AMARILLO}📰 ÚLTIMOS 20 CRÍMENES NARCO{Color.RESET}")
            print(f"{Color.ROJO}{'═'*70}{Color.RESET}")
            for i, inc in enumerate(incidentes, 1):
                print(f"\n{Color.ROJO}{i:2d}.{Color.RESET} {inc['titulo'][:100]}...")
                print(f"      {inc['fecha']} | {inc.get('isla', '?')} | {inc['fuente']} | {inc.get('tipo', '?')}")
            if not incidentes:
                print("   No hay incidentes registrados.")
            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '7':
            with open('export_narco.json', 'w', encoding='utf-8') as f:
                json.dump(gestor.datos, f, indent=2, ensure_ascii=False)
            with open('export_narco.csv', 'w', encoding='utf-8') as f:
                f.write("Título,Fecha,País,Tipo,Fuente\n")
                for inc in gestor.datos['incidentes']:
                    f.write(f"{inc['titulo'][:100].replace(',', ' ')},{inc['fecha']},{inc.get('isla','')},{inc.get('tipo','')},{inc['fuente']}\n")
            cprint(f"\n✅ Exportados export_narco.json y export_narco.csv", 'verde')
            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '8':
            gestor.detector.verificar_todos(PERIODICOS_BASE)
            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '9':
            stats = gestor.estadisticas()
            print(f"\n{Color.ROJO}{'═'*70}{Color.RESET}")
            print(f"{Color.AMARILLO}📊 DISTRIBUCIÓN NARCO POR TIPO{Color.RESET}")
            print(f"{Color.ROJO}{'═'*70}{Color.RESET}")
            for tipo, cant in sorted(stats['tipos'].items(), key=lambda x: x[1], reverse=True):
                pct = round((cant / stats['total'] * 100), 1) if stats['total'] > 0 else 0
                barra = '█' * int(pct // 2) + '░' * (50 - int(pct // 2))
                print(f"   {tipo}: [{barra}] {cant} ({pct}%)")
            input(f"\n{Color.GRIS}Enter...{Color.RESET}")

        elif op == '10':
            cprint(f"\n👋 {t('hasta_pronto')}", 'rojo', negrita=True)
            break

        else:
            cprint(f"\n❌ {t('opcion_invalida')}", 'rojo')
            time.sleep(1)


# ============================================
# MAIN - PUNTO DE ENTRADA (NARCO EDITION)
# ============================================

if __name__ == '__main__':
    seleccionar_idioma()

    print(f"""
{Color.ROJO}
╔══════════════════════════════════════════════════════════════════╗
║  💀 DIABOLIC LATAM - NARCO EDITION v{VERSION} 💀                          ║
║  🔫 MONITOREO DE CÁRTELES · NARCOTRÁFICO · CRIMEN ORGANIZADO      ║
║  🌎 70+ FUENTES · 15+ PAÍSES · ALERTAS DE VIOLENCIA EXTREMA       ║
║                                         - By Condor2026          ║
║                                            •SpectrumSecurity•    ║
╚══════════════════════════════════════════════════════════════════╝
{Color.RESET}""")
    print(f"{Color.GRIS}🕷️  \"Un gran poder conlleva una gran responsabilidad\" - Spider-Man{Color.RESET}")
    print(f"{Color.GRIS}⚖️  Uso ético y legal. Datos públicos. No recomendado para sensibles.{Color.RESET}")
    print(f"{Color.CIAN}💀 Enfoque principal: Cárteles (Sinaloa, CJNG, CDS, Zetas, etc.),{Color.RESET}")
    print(f"{Color.CIAN}   sicariato, extorsión, fentanilo, laboratorios clandestinos.{Color.RESET}")

    gestor = GestorDatos()
    stats = gestor.estadisticas()
    print(f"{Color.VERDE}📊 Incidentes narco en base: {stats['total']}{Color.RESET}")
    print(f"{Color.AMARILLO}⏳ Última actualización: {gestor.datos.get('ultima_actualizacion', 'Nunca')}{Color.RESET}")

    print(f"\n{Color.CIAN}¿Cómo quieres ejecutar?{Color.RESET}")
    print(f"{Color.ROJO}1.{Color.RESET} Modo terminal (10 comandos)")
    print(f"{Color.ROJO}2.{Color.RESET} Modo web directo")

    modo = input(f"\n{Color.ROJO}➤ Elige: {Color.RESET}")

    if modo == '2':
        cprint(f"\n🌐 {t('servidor_web')}: http://localhost:{PUERTO}", 'verde', negrita=True)
        cprint(f"   {t('presiona_ctrl_c')}", 'gris')
        app.run(host='0.0.0.0', port=PUERTO, debug=True)
    else:
        menu()
~ $
