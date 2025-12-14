# UltraYouTube Downloader

**Logiciel professionnel de téléchargement YouTube (Vidéo & Audio).**

---

## 🚀 Démarrage Rapide (Le plus simple)

Ne vous embêtez pas avec les commandes compliquées. 

**Double-cliquez simplement sur :**
👉 **`run.bat`**

Ce fichier va automatiquement :
1. Détecter si Python est là.
2. Créer l'environnement virtuel et installer les fichiers manquants si nécessaire.
3. Lancer l'application sans erreur de sécurité.

---

## 📂 Structure du projet

Pour plus de clarté, le code a été séparé en plusieurs fichiers :

- **`main.py`** : Le point d'entrée. C'est lui qui vérifie que tout est installé (`auto-install`).
- **`gui.py`** : Contient toute l'interface graphique (boutons, fenêtres).
- **`downloader.py`** : Contient la logique de téléchargement (yt-dlp + pytube).
- **`utils.py`** : Outils divers (logs).
- **`run.bat`** : Le lanceur automatique pour Windows.

## 🛠️ Installation Manuelle (Avancé)

Si vous préférez tout faire à la main :

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## ⚙️ Compilation en .exe

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name "UltraDownloader" main.py
```
*(Note : PyInstaller va scanner et inclure automatiquement gui.py, downloader.py, etc.)*

---
## ❓ FAQ

**Pourquoi `run.bat` ?**
Pour éviter les erreurs "Exécution de scripts désactivée" sur PowerShell. Il utilise directement l'exécutable Python sans passer par le script d'activation restreint par Windows.

**Mises à jour ?**
Le logiciel vérifie et installe les mises à jour des bibliothèques au démarrage (si non-compilé).