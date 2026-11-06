#!/usr/bin/env bash
# DIABOLIC LATAM v8.0 — instalador para Termux / Linux
set -e

echo "🔪 DIABOLIC LATAM v8.0 — instalación"

# Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 no encontrado. Instálalo antes de continuar."
  exit 1
fi

# pip
python3 -m pip install --upgrade pip

# Dependencias obligatorias
python3 -m pip install flask requests beautifulsoup4

# Opcionales
read -r -p "¿Instalar matplotlib y networkx para gráficos estáticos? [s/N] " opt
case "$opt" in
  s|S|y|Y) python3 -m pip install matplotlib networkx ;;
  *) echo "⏭  Omitidos (puedes instalarlos luego: pip install matplotlib networkx)" ;;
esac

chmod +x Diabolic_Latam.py 2>/dev/null || true

echo ""
echo "✅ Instalación completa."
echo "▶  python3 Diabolic_Latam.py                  (menú interactivo)"
echo "▶  python3 Diabolic_Latam.py --web --lang es  (panel en http://localhost:5013)"
echo "▶  python3 Diabolic_Latam.py --scan all       (scan por CLI)"
