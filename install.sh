#!/bin/bash

# ============================================
# INSTALADOR DE DIABOLIC LATAM v6.0
# Soporta: Termux (Android) y Linux
# ============================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   🔥 DIABOLIC LATAM v6.0 - INSTALADOR AUTOMÁTICO   ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"

# Detectar sistema
if command -v pkg &> /dev/null; then
    OS="termux"
    echo -e "${GREEN}✅ Sistema detectado: Termux (Android)${NC}"
elif command -v apt &> /dev/null; then
    OS="linux"
    echo -e "${GREEN}✅ Sistema detectado: Linux${NC}"
else
    echo -e "${RED}❌ No se detectó Termux ni Linux con apt. Abortando.${NC}"
    exit 1
fi

# Verificar/instalar Python y git
echo -e "${YELLOW}📦 Verificando dependencias...${NC}"

if [ "$OS" == "termux" ]; then
    pkg update -y
    pkg install python git -y
else
    sudo apt update
    sudo apt install python3 python3-pip git -y
fi

# Verificar Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ No se pudo instalar Python. Abortando.${NC}"
    exit 1
fi

# Clonar repositorio si no existe
if [ ! -d "Diabolic_Latam" ]; then
    echo -e "${YELLOW}📥 Clonando repositorio...${NC}"
    git clone https://github.com/Condor2026/Diabolic_Latam
fi

cd Diabolic_Latam || { echo -e "${RED}❌ No se pudo entrar en el directorio Diabolic_Latam${NC}"; exit 1; }

# Instalar dependencias Python
echo -e "${YELLOW}📦 Instalando dependencias Python (requests, beautifulsoup4, flask)...${NC}"
if command -v pip &> /dev/null; then
    pip install requests beautifulsoup4 flask
elif command -v pip3 &> /dev/null; then
    pip3 install requests beautifulsoup4 flask
else
    echo -e "${RED}❌ No se encontró pip. Instálalo manualmente.${NC}"
    exit 1
fi

# Crear archivo requirements.txt para futuras referencias
echo -e "requests>=2.25.0\nbeautifulsoup4>=4.9.3\nflask>=2.0.0" > requirements.txt

# Dar permisos de ejecución al script principal si existe
if [ -f "Diabolic_Latam.py" ]; then
    chmod +x Diabolic_Latam.py
fi

echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA CON ÉXITO${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Para ejecutar DIABOLIC LATAM:${NC}"
echo -e "   cd Diabolic_Latam"
echo -e "   python Diabolic_Latam.py   (o python3 Diabolic_Latam.py)"
echo -e ""
echo -e "${BLUE}🕷️  \"Un gran poder conlleva una gran responsabilidad\"${NC}"
