# YouTube Downloader

**YouTube Downloader** est une application de bureau professionnelle concue pour telecharger des videos et musiques YouTube avec une fiabilite maximale.

---

## Demarrage Rapide (Utilisateurs Windows)

Vous n'avez besoin d'aucune connaissance technique.

1. Telechargez le dossier du projet.
2. Double-cliquez sur le fichier **`run.bat`**

**C'est tout.** Le script va automatiquement :

- Verifier si Python est installe (et l'installer sinon).
- Creer un environnement isole (.venv).
- Installer les bibliotheques necessaires.
- Telecharger et configurer FFmpeg automatiquement.
- Lancer l'interface.

---

## Fonctionnalites

| Fonctionnalite | Description |
|---|---|
| **Haute Vitesse** | Telechargement multi-segmente (10 fragments simultanes) |
| **Moteur Hybride** | `yt-dlp` (principal) + `pytubefix` (secours) avec 3 strategies de connexion |
| **Qualite Maximale** | Support natif 4K/8K, fusion audio/vidéo automatique |
| **Audio Avancé** | Conversion en MP3, M4A, WAV, OPUS, WMA avec controle du bitrate |
| **Metadonnees Integrees** | Les fichiers audio contiennent automatiquement l'image de couverture, le titre, l'artiste et les metadonnees YouTube |
| **Apercu Avant Telechargement** | Collez un lien et voyez le titre, la miniature et la chaine avant de telecharger. Cliquez sur l'image pour l'agrandir |
| **Mise a Jour Auto** | En mode Python : mise a jour via `git pull`. En mode EXE : popup avec lien de telechargement |
| **Multi-Format** | Vidéo : MP4, MKV. Audio : MP3, M4A, OPUS, WAV, WMA |
| **Compilation** | Executable Windows (EXE) et AppImage Linux disponibles |
| **FFmpeg Auto** | Telechargement et configuration automatiques de FFmpeg |

---

## Compilation

Lancez **`compil.bat`** pour acceder au menu de compilation.

| Option | Description |
|---|---|
| `[1] EXE Windows` | Compile un executable Windows (multi-fichiers, sans terminal, avec icone) via PyInstaller |
| `[2] AppImage Linux` | Compile une AppImage Linux (a executer sur une machine Linux) |

### Resultats

- **EXE** : `dist/YouTube-Downloader/YouTube-Downloader.exe`
- **AppImage** : `YouTube-Downloader-{version}-x86_64.AppImage`

---

## Architecture Technique

### Lanceur (`run.bat`)

Script d'amorcage qui detecte Python (py launcher, python, chemins connus), cree le venv et lance l'application.

### Moteur de Telechargement (`downloader.py`)

- Utilise `yt-dlp` avec 3 strategies de connexion (android+web, ios, web) et retry automatique.
- Fallback sur `pytubefix` si toutes les strategies echouent.
- Post-processeurs : conversion de format, integration des metadonnees (FFmpegMetadata), integration de la couverture (EmbedThumbnail).

### Gestionnaire FFmpeg (`ffmpeg_manager.py`)

Telecharge automatiquement les binaires FFmpeg (ffmpeg.exe + ffprobe.exe) dans le dossier `bin/` au premier lancement.

### Interface (`gui.py`)

Interface sombre et reactive basee sur `customtkinter` avec :

- Apercu automatique du contenu (titre + miniature) au collage du lien.
- Barre de progression et logs en temps reel.
- Selection de format et qualite.
- Changement de theme (sombre/claire).

### Systeme de Mise a Jour (`main.py`)

| Mode | Comportement |
|---|---|
| **Python** (dev) | Verification de version via GitHub + `git pull` automatique |
| **EXE / AppImage** | Verification via GitHub Releases API + popup avec lien de telechargement |

### Compilation (`scripts/`)

- `build_exe.bat` : Script de compilation Windows via PyInstaller (onedir, windowed).
- `build_appimage.sh` : Script de compilation Linux via PyInstaller + appimage-builder.
- `generate_icon.py` : Generateur d'icone (cercle rouge avec triangle blanc).
- `appimage-builder.yml` : Recette AppImage.

---

## Dependances

- `customtkinter` - Interface graphique moderne
- `yt-dlp` - Moteur de telechargement principal
- `pytubefix` - Moteur de telechargement de secours
- `pillow` - Gestion des images (miniature/preview)
- `PyInstaller` - Compilation en executable (optionnel)

---

## FAQ

**Q: Le telechargement semble bloque a 100% ?**
R: Regardez la barre de progression. Si elle indique "Conversion/Fusion...", c'est normal ! Le logiciel transforme le fichier brut en format fini.

**Q: J'ai un message "FFmpeg introuvable" ?**
R: C'est normal lors de la premiere utilisation. Le logiciel recupere les outils necessaires automatiquement.

**Q: Où sont mes fichiers ?**
R: Par defaut dans le dossier `Downloads_YT` a cote du logiciel.

**Q: Comment mettre a jour la version compilee (EXE) ?**
R: Une popup s'affichera automatiquement quand une nouvelle version sera disponible sur GitHub. Cliquez sur "Telecharger" pour aller sur la page de la release.

**Q: L'icone ne s'affiche pas dans l'EXE ?**
R: Recompilez avec `compil.bat` → `[1]`. L'icone est generee par `scripts/generate_icon.py`.
