# 📺 UltraYouTube Downloader

**UltraYouTube Downloader** est une application de bureau professionnelle conçue pour télécharger des vidéos et musiques YouTube avec une fiabilité maximale.

Contrairement aux autres téléchargeurs qui cessent de fonctionner dès que YouTube change son code, ce logiciel utilise une **architecture à double moteur** (Hybrid Engine) : il combine la puissance de `yt-dlp` (le standard de l'industrie) avec la flexibilité de `pytubefix` en cas de panne.

---

## 🚀 Démarrage Rapide (Utilisateurs Windows)

Vous n'avez besoin d'aucune connaissance technique.

1. Téléchargez le dossier du projet.
2. Double-cliquez sur le fichier :
   👉 **`run.bat`**

**C'est tout.** Le script va automatiquement :
- Vérifier si Python est installé (et l'installer sinon).
- Créer une zone isolée pour le logiciel (environnement virtuel).
- Installer les bibliothèques nécessaires.
- Lancer l'interface.

---

## ✨ Fonctionnalités Clés

*   **⚡ Haute Vitesse** : Téléchargement multi-segmenté (jusqu'à 15 connexions simultanées).
*   **🛡️ Robustesse (Failover)** : Si le moteur principal (`yt-dlp`) échoue sur une vidéo spécifique, le logiciel bascule automatiquement sur le moteur de secours (`pytubefix`).
*   **📺 Qualité Maximale** : Supporte la 4K (2160p), 1440p, 1080p, etc.
*   **🎵 Audio Haute Fidélité** : Conversion en MP3, M4A, WAV avec sélection du bitrate (320kbps, etc.).
*   **🔄 Mises à jour Auto** : Le logiciel vérifie automatiquement GitHub au démarrage pour se mettre à jour.

---

## 🧠 Comment ça marche ? (Analyse du Code)

Si vous êtes développeur ou curieux, voici comment le projet est architecturé. Le code est modulaire pour faciliter la maintenance.

### 1. Le Lanceur (`run.bat`)
C'est le point d'entrée pour Windows. C'est un script Batch avancé qui agit comme un "installateur silencieux".
- Il vérifie la présence de `winget` et de `python`.
- Si Python manque, il le télécharge et l'installe sans intervention utilisateur.
- Il configure un environnement virtuel `.venv` pour ne pas polluer votre système.
- Il lance `main.py`.

### 2. Le Gestionnaire (`main.py`)
C'est le cerveau administratif de l'application. Avant de lancer l'interface, il effectue des tâches critiques :
- **Auto-Update** : Il compare la version locale (`version.py`) avec celle sur GitHub. Si une nouvelle version existe, il fait un `git pull` automatique.
- **Vérification des dépendances** : Il s'assure que `yt-dlp`, `customtkinter` et `pytubefix` sont installés/réparés.
- Enfin, il importe et lance `gui.py`.

### 3. L'Interface (`gui.py`)
Utilise **CustomTkinter** pour une interface moderne et sombre.
- **Threading** : L'interface ne "gèle" jamais pendant un téléchargement. L'action est envoyée dans un *thread* (processus parallèle) via la méthode `start_thread`.
- **Logs en temps réel** : Redirige la sortie du téléchargement vers la zone de texte en bas de l'application pour que vous voyiez exactement ce qui se passe.

### 4. Le Moteur de Téléchargement (`downloader.py`)
C'est ici que réside l'intelligence du téléchargement.
- **Classe `DownloadManager`** : Elle contient la logique "Try/Catch".
- **Étape 1 (yt-dlp)** : Tente de télécharger avec `yt-dlp` en utilisant des options optimisées (fichiers temporaires, fusion audio/vidéo via FFmpeg si présent).
- **Étape 2 (Fallback)** : Si une erreur survient, il capture l'exception et lance `_download_pytube` qui utilise la librairie `pytubefix`.
- **Gestion FFmpeg** : Le script détecte si FFmpeg est installé sur le PC. S'il est là, il permet de fusionner la meilleure piste vidéo (souvent sans son en 1080p+) avec la meilleure piste audio. Sinon, il se rabat sur les formats standards (720p max souvent).

### 5. Les Utilitaires (`utils.py`)
Un système de logging thread-safe. Il permet d'écrire des messages depuis n'importe quel fichier (`log("message")`) qui seront affichés à la fois dans la console du développeur et dans la zone de texte de l'interface graphique.

---

## 🛠️ Installation Manuelle (Développeurs)

Si vous ne souhaitez pas utiliser `run.bat`, vous pouvez utiliser les commandes standards :

**Pré-requis** : Python 3.10+ et Git.

```bash
# 1. Cloner le repo
git clone https://github.com/votre-repo/youtube-download.git
cd youtube-download

# 2. Créer l'environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
# Windows :
.\.venv\Scripts\activate
# Mac/Linux :
source .venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer
python main.py
```

## ❓ FAQ Technique

**Q: Pourquoi les vidéos 1080p n'ont pas de son parfois ?**
R: YouTube sépare les flux vidéo et audio pour les hautes qualités (DASH). Pour les recombiner, le logiciel a besoin de **FFmpeg**. Si vous n'avez pas FFmpeg, le logiciel essaiera de trouver la meilleure qualité "unique" (souvent 720p).

**Q: Le téléchargement reste à 0% ?**
R: Vérifiez votre connexion internet. Si cela persiste, YouTube a peut-être bloqué votre IP temporairement ou changé son code (le logiciel basculera sur le moteur de secours, mais cela peut prendre quelques secondes).

**Q: Où sont les fichiers ?**
R: Par défaut dans un dossier `Downloads_YT` créé à côté du logiciel, ou là où vous l'avez indiqué via le bouton "Browse".