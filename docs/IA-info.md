# 🧠 Documentation Technique - UltraYouTube Downloader

Ce document est destiné à fournir une vue d'ensemble technique du projet pour une IA ou un développeur souhaitant comprendre, maintenir ou améliorer le logiciel.

## 📌 Informations Générales
- **Nom du projet** : UltraYouTube Downloader
- **Version actuelle** : Voir `version.py`
- **Langage** : Python 3.10+
- **Interface** : CustomTkinter (Moderne, Dark Mode)
- **Moteur de téléchargement** : Hybride (yt-dlp + pytubefix)

---

## 🏗️ Architecture du Projet

### 1. Point d'entrée : `main.py`
Le fichier `main.py` orchestre le démarrage :
- **Auto-Update Logiciel** : Vérifie la version locale par rapport à la version distante sur GitHub (via `git fetch`). Propose une mise à jour automatique si une version supérieure est détectée.
- **Auto-Repair & Upgrade** : Installe et met à jour automatiquement les dépendances Python (`pip install --upgrade`). Cela garantit que `yt-dlp` est toujours à la dernière version pour contourner les blocages YouTube.
- **Lancement** : Initialise l'interface graphique (`src/gui.py`).

### 2. Interface Utilisateur : `src/gui.py`
Gère toute la partie visuelle et l'interaction utilisateur :
- Basé sur **CustomTkinter** pour un rendu moderne.
- **Multi-threading** : Les téléchargements sont lancés dans des threads séparés pour éviter que l'interface ne "freeze" (ne se bloque).
- **Système de Logs** : Redirige les messages du moteur vers un `CTkTextbox` en temps réel.

### 3. Gestionnaire de Téléchargement : `src/downloader.py`
C'est le cœur logique de l'application. Il utilise une **architecture à double moteur** avec des correctifs de fiabilité :
- **yt-dlp (Primaire)** : Optimisé pour la vitesse (15 segments) et la fiabilité.
- **pytubefix (Fallback/Secours)** : Utilisé automatiquement si `yt-dlp` échoue.

---

## 🛠️ Dernières Améliorations et Correctifs

### Fiabilité et Contournement des Blocages (Avril 2026)
- **Correction HTTP 403 Forbidden** : Ajout d'arguments d'extraction avancés dans `yt-dlp` (`player_client`, `extractor_args`) et d'un `User-Agent` moderne pour simuler un navigateur réel.
- **Auto-Upgrade des Dépendances** : Modification du processus de démarrage pour forcer la mise à jour des bibliothèques (`pip install --upgrade`). Crucial pour `yt-dlp` qui publie des correctifs quasi-quotidiens face aux changements de YouTube.
- **Correction Conversion Audio** : Résolution d'un crash dans le moteur de secours où `subprocess.STNULL` (inexistant) empêchait la conversion en MP3. Remplacé par `subprocess.DEVNULL`.

### Restructuration du Code (Refactoring)
- **Modularité** : Déplacement de la logique métier vers le dossier `src/` pour séparer le code source des fichiers de configuration et de documentation.
- **Package Python** : Transformation de `src/` en package (`__init__.py`) et passage aux **imports relatifs** pour une meilleure portabilité et éviter les conflits de noms.
- **Documentation dédiée** : Centralisation des infos techniques dans `docs/`.

---

## 📂 Structure des Fichiers

- `main.py` : Lanceur, mise à jour et installation.
- `version.py` : Contient uniquement la variable `VERSION` (gardé à la racine pour l'auto-update).
- `src/` : Dossier contenant le code source.
  - `gui.py` : Code de l'interface graphique.
  - `downloader.py` : Logique de téléchargement et mapping des formats.
  - `ffmpeg_manager.py` : Téléchargement et gestion de FFmpeg.
  - `utils.py` : Fonctions utilitaires (logging).
- `docs/` : Documentation du projet.
  - `IA-info.md` : Documentation technique détaillée (ce fichier).
- `run.bat` : Script Windows de lancement.
- `Downloads_YT/` : Dossier de sortie par défaut.
- `bin/` : Contient l'exécutable FFmpeg portable.

---

## 🚀 Flux de Travail (Workflow)
1. L'utilisateur lance `run.bat`.
2. `main.py` vérifie les mises à jour et les bibliothèques.
3. `gui.py` s'affiche.
4. Au clic sur "DOWNLOAD" :
   - Le moteur vérifie la présence de FFmpeg via `src/ffmpeg_manager.py`.
   - `src/downloader.py` tente un téléchargement via `yt-dlp`.
   - Les callbacks de progression mettent à jour la barre de progression.
   - Si succès, le fichier est placé dans `Downloads_YT`.
