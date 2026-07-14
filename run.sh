#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

echo "[Launcher] ========================================"
echo "[Launcher]   YouTube Downloader - Launcher Linux"
echo "[Launcher] ========================================"
echo ""

# 1. VERIFICATION DE PYTHON
echo "[Launcher] Verification de Python..."

PYTHON_CMD=""

if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    # Verifier que "python" n'est pas Python 2
    PY_VER=$($PYTHON_CMD --version 2>&1)
    if echo "$PY_VER" | grep -q "Python 3"; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERREUR] Python 3 n'est pas detecte."
    echo "[ACTION] Installez Python 3 :"
    echo "         sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "[Launcher] Python detecte: $PYTHON_VERSION"

# 2. VERIFICATION DU MODULE VENV
echo "[Launcher] Verification du module venv..."
$PYTHON_CMD -c "import venv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERREUR] Le module 'venv' n'est pas disponible."
    echo "[ACTION] Installez-le :"
    echo "         sudo apt install python3-venv"
    exit 1
fi
echo "[Launcher] Module venv OK."

# 3. GESTION DU VENV
if [ -d ".venv" ] && [ -f ".venv/bin/python" ]; then
    echo "[Launcher] Environnement virtuel existant detecte."
else
    # Supprimer un .venv corrompu s'il existe
    if [ -d ".venv" ]; then
        echo "[Launcher] .venv corrompu, suppression..."
        rm -rf .venv
    fi

    echo "[Launcher] Creation de l'environnement virtuel (.venv)..."
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Echec de la creation du venv."
        echo "[ACTION] Verifiez que python3-venv est installe :"
        echo "         sudo apt install python3-venv"
        exit 1
    fi

    # Verifier que le venv a bien ete cree
    if [ ! -f ".venv/bin/python" ]; then
        echo "[ERREUR] Le venv a ete cree mais .venv/bin/python est absent."
        exit 1
    fi

    echo "[Launcher] Installation de pip..."
    .venv/bin/python -m pip install --upgrade pip --quiet

    echo "[Launcher] Installation des dependances..."
    .venv/bin/python -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Echec de l'installation des dependances."
        exit 1
    fi

    echo "[Launcher] Installation terminee."
fi

# 4. LANCEMENT
echo ""
echo "[Launcher] Lancement de l'application..."
echo "[Launcher] ========================================"
.venv/bin/python main.py
EXIT_CODE=$?
echo "[Launcher] ========================================"
if [ $EXIT_CODE -ne 0 ]; then
    echo "[Launcher] L'application s'est terminee avec l'erreur code $EXIT_CODE."
fi
