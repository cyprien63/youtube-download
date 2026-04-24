# 📺 UltraYouTube Downloader

**UltraYouTube Downloader** est une application de bureau professionnelle conçue pour télécharger des vidéos et musiques YouTube avec une fiabilité maximale.

Contrairement aux autres téléchargeurs qui cessent de fonctionner dès que YouTube change son code, ce logiciel utilise une **architecture à double moteur** (Hybrid Engine) et gère lui-même ses dépendances (comme FFmpeg).

---

## 🚀 Démarrage Rapide (Utilisateurs Windows)

Vous n'avez besoin d'aucune connaissance technique.

1. Téléchargez le dossier du projet.
2. Double-cliquez sur le fichier :
   👉 **`run.bat`**

**C'est tout.** Le script va automatiquement :

- Vérifier si Python est installé (et l'installer sinon).
- Créer une zone isolée pour le logiciel.
- Installer les bibliothèques nécessaires.
- **Télécharger et configurer FFmpeg** automatiquement pour la conversion audio/vidéo.
- Lancer l'interface.

---

## ✨ Fonctionnalités Clés

- **⚡ Haute Vitesse** : Téléchargement multi-segmenté.
- **🛡️ Robustesse** : Moteur hybride `yt-dlp` (principal) + `pytubefix` (secours).
- **📺 Qualité Maximale** : Support natif 4K/8K, 1440p, 1080p (fusion audio/vidéo automatique).
- **🎵 Audio Avancé** : Conversion automatique en **MP3, M4A, WAV, OPUS, WMA**.
- **👁️ Interface Claire** : Indicateur visuel "Conversion/Fusion..." pour ne jamais penser que l'app est plantée.
- **🔧 Auto-Configuration** : Plus besoin d'installer FFmpeg manuellement, le logiciel s'en occupe.

---

## 🧠 Architecture Technique

### 1. Lanceur Intelligent (`run.bat`)

Script d'amorçage qui garantit un environnement sain (Python 3.10+, venv propre) avant de lancer l'application.

### 2. Gestionnaire de Dépendances (`ffmpeg_manager.py`)

Nouveauté majeure : au premier lancement, ce module détecte l'absence de FFmpeg et télécharge une version statique portable dans un dossier `bin/` local. Cela garantit que la conversion format (ex: mp4 -> mp3) fonctionne sur 100% des machines sans configuration.

### 3. Moteur Logiciel (`downloader.py`)

- Utilise `yt-dlp` avec des paramètres optimisés.
- Détecte les étapes de conversion et renvoie des feedbacks précis à l'interface ("Conversion en cours...").
- Mode fallback sur `pytubefix` si l'API principale est bloquée.

### 4. Interface (`gui.py`)

Interface sombre et réactive basée sur `customtkinter`. Elle reste fluide (multi-thread) même pendant les gros téléchargements.

---

## ❓ FAQ

**Q: Le téléchargement semble bloqué à 100% ?**
R: Regardez la barre de texte. Si elle indique "Conversion/Fusion...", c'est normal ! Le logiciel est en train de transformer le fichier brut (ex: webm) en fichier fini (ex: mp3). Cela peut prendre 10 à 60 secondes selon la puissance de votre PC.

**Q: J'ai un message "FFmpeg not found. Downloading..." ?**
R: C'est normal lors de la toute première utilisation. Le logiciel récupère les outils nécessaires. Cela ne se produira qu'une fois.

**Q: Où sont mes fichiers ?**
R: Par défaut dans le dossier `Downloads_YT` à côté du logiciel.
