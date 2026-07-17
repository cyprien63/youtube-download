# YouTube Downloader v5.3.3

Application de bureau professionnelle pour telecharger des videos et musiques YouTube avec une fiabilite maximale.

---

## Demarrage Rapide

### Mode Python ( developpement )

1. Clonez le depot : `git clone https://github.com/cyprien63/youtube-download.git`
2. Double-cliquez sur **`run.bat`**

Le script automatiquement :
- Detecte et installe Python 3.12+ si necessaire
- Cree un environnement virtuel (.venv)
- Installe toutes les dependances
- Telecharge et configure FFmpeg
- **Se met a jour tout seul** a chaque lancement (`git pull`)

### Mode Compile ( utilisateurs finaux )

1. Telechargez le dossier ou l'executable
2. Lancez **`YouTube-Downloader.exe`** (Windows)

> Pas besoin de Python installe. L'application est autonome.

---

## Fonctionnalites

| Fonctionnalite | Description |
|---|---|
| **Telechargement Rapide** | Multi-segmente, 10 fragments simultanes, retries automatiques |
| **Moteur Hybride** | `yt-dlp` (principal) + `pytubefix` (secours) avec 3 strategies de connexion |
| **Qualite Maximale** | Support 4K/8K, fusion audio/vidéo automatique |
| **Audio Complet** | MP3, M4A, WAV, OPUS, WMA avec controle du bitrate (64-320 kbps) |
| **Metadonnees Integrees** | Image de couverture, titre, artiste, description integres dans les fichiers audio |
| **Apercu Avant Telechargement** | Titre, miniature et chaine affiches avant de lancer le telechargement |
| **Mise a Jour Auto** | `git pull` en mode Python / popup avec lien de telechargement en mode EXE |
| **Multi-Format** | Vidéo : MP4, MKV. Audio : MP3, M4A, OPUS, WAV, WMA |
| **FFmpeg Auto** | Telechargement et configuration automatiques au premier lancement |
| **Thème Sombre/Clair** | Interface personnalisable |
| **Compilation** | Executable Windows (EXE) et AppImage Linux |

---

## Compilation

Lancez **`compil.bat`** pour acceder au menu de compilation.

```
============================================================
       YouTube Downloader - Systeme de Compilation
============================================================

  [1] Compiler en EXE (Windows, multi-fichiers, sans terminal)
  [2] Compiler en AppImage (Linux)
  [3] Quitter
============================================================
```

### EXE Windows

- Utilise PyInstaller en mode `--onedir` (dossier multi-fichiers)
- Sans terminal (`--windowed`)
- Avec icone personalisee (cercle rouge / triangle blanc)
- Necessite Python 3.12+ et le venv

**Sortie** : `dist/YouTube-Downloader/YouTube-Downloader.exe`

### AppImage Linux

- A executer sur une machine Linux
- Utilise PyInstaller + appimage-builder
- Genere une AppImage portable

**Sortie** : `YouTube-Downloader-{version}-x86_64.AppImage`

---

## Architecture Technique

```
youtube-download/
  main.py                Point d'entree, mise a jour, compilation
  version.py             Version actuelle
  run.bat                Lanceur Windows (auto-install Python + venv)
  compil.bat             Menu de compilation
  requirements.txt       Dependances Python
  src/
    gui.py               Interface graphique (customtkinter)
    downloader.py        Moteur de telechargement (yt-dlp + pytubefix)
    ffmpeg_manager.py    Gestion et telechargement de FFmpeg
    utils.py             Logger thread-safe pour la GUI
  scripts/
    build_exe.bat        Script de compilation Windows
    build_appimage.sh    Script de compilation Linux
    appimage-builder.yml Recette AppImage
    generate_icon.py     Generateur d'icone
    icon.ico             Icone Windows
    icon.png             Icone Linux
  bin/                   Binaires FFmpeg (telecharges auto)
```

### Moteur de Telechargement (`downloader.py`)

- **Strategies de connexion** : 3 essais separes (android+web, ios, web) avec retry automatique et backoff
- **Post-processeurs** : Conversion de format (FFmpegVideoConvertor), integration des metadonnees (FFmpegMetadata), integration de la couverture (EmbedThumbnail)
- **Fallback** : Si yt-dlp echoue, bascule sur pytubefix automatiquement

### Gestionnaire FFmpeg (`ffmpeg_manager.py`)

- Recherche FFmpeg dans le PATH systeme
- Sinon telecharge un build statique Windows depuis GitHub dans `bin/`
- Gere les deux URLs de fallback (yt-dlp/FFmpeg-Builds + gyan.dev)

### Interface (`gui.py`)

- Basee sur customtkinter (theme sombre par defaut)
- **Apercu** : Collez un lien YouTube, le titre + miniature + chaine s'affichent automatiquement (debounce 600ms)
- **Preview** : Cliquez sur la miniature pour l'agrandir dans une fenetre separee
- Barre de progression avec pourcentage, vitesse et ETA
- Logs en temps reel avec timestamps

### Systeme de Mise a Jour (`main.py`)

| Mode | Comportement |
|---|---|
| **Python** (dev) | `git pull --ff-only` automatique a chaque lancement |
| **EXE / AppImage** | Verification via GitHub Releases API + version.py en fallback. Popup tkinter avec lien de telechargement |

### Protection Mode Compile

Le code detecte `sys.frozen` (PyInstaller) pour :
- Desactiver l'installation de dependances (elles sont dans l'exe)
- Utiliser le bon chemin pour les donnees (`os.path.dirname(sys.executable)`)
- Logger les erreurs dans `crash.log` (car la console est masquee)

---

## Dependances

| Package | Role |
|---|---|
| `customtkinter` | Interface graphique moderne |
| `yt-dlp` | Moteur de telechargement principal |
| `pytubefix` | Moteur de telechargement de secours |
| `pillow` | Gestion des images (miniature, apercu) |
| `PyInstaller` | Compilation en executable (optionnel) |

---

## FAQ

**Q: Le telechargement semble bloque a 100% ?**
R: La barre indique "Conversion/Fusion..." ? C'est normal. Le logiciel transforme le fichier brut en format fini. Cela peut prendre 10 a 60 secondes.

**Q: J'ai un message "FFmpeg introuvable" ?**
R: Normal a la premiere utilisation. FFmpeg est telecharge automatiquement (~80 Mo). Cela ne se reproduira plus.

**Q: Ou sont mes fichiers ?**
R: Par defaut dans le dossier `Downloads_YT` a cote du logiciel. Vous pouvez changer le chemin dans l'interface.

**Q: Comment mettre a jour la version Python ?**
R: Relancez simplement `run.bat`. Il effectue un `git pull` automatique et relance avec la derniere version.

**Q: Comment mettre a jour la version compilee (EXE) ?**
R: Une popup s'affiche automatiquement quand une nouvelle version est disponible. Cliquez sur "Telecharger" pour aller sur la page GitHub Releases.

**Q: L'application ne s'ouvre pas en mode compile ?**
R: Verifiez le fichier `crash.log` a cote de l'executable. Il contient les erreurs memes quand la console est masquee.

**Q: Comment regenerer les icones ?**
R: `scripts/generate_icon.py` genere `icon.ico` (Windows) et `icon.png` (Linux). Recompilez avec `compil.bat` apres.

**Q: Le popup de mise a jour n'apparait pas ?**
R: Verifiez qu'une GitHub Release existe pour la nouvelle version. Sans release, le popup ne s'affiche pas en mode compile.
