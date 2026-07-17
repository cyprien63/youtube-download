#!/bin/bash
# ================================================================
#   Compilation AppImage - YouTube Downloader
#   A executer sur une machine Linux
# ================================================================

set -e
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  Compilation en AppImage (Linux)"
echo "============================================================"
echo ""

# Verification des outils
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python3 non trouve."
    exit 1
fi

if ! command -v appimage-builder &> /dev/null; then
    echo "[!] app-image-builder non installe. Installation..."
    pip3 install appimage-builder
fi

# Recuperer la version
VERSION=$(python3 -c "exec(open('version.py').read()); print(VERSION)")
echo "Version : $VERSION"

# Nettoyage
echo "[1/4] Nettoyage..."
rm -rf AppDir build dist

# Compilation PyInstaller
echo "[2/4] Compilation PyInstaller..."
python3 -m PyInstaller \
    --noconfirm \
    --onedir \
    --name "youtube-downloader" \
    --hidden-import customtkinter \
    --hidden-import yt_dlp \
    --hidden-import pytubefix \
    --hidden-import PIL \
    --collect-data customtkinter \
    main.py

# Preparation AppDir
echo "[3/4] Preparation AppDir..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p AppDir/usr/share/applications

cp -r dist/youtube-downloader/* AppDir/usr/bin/
cp scripts/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/youtube-downloader.png

cat > AppDir/usr/bin/AppRun << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/bin:${HERE}/usr/bin:${HERE}/usr/sbin:${HERE}/usr/games:${HERE}/bin:${HERE}/sbin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/lib:${HERE}/usr/lib:${HERE}/usr/lib/i386-linux-gnu:${HERE}/usr/lib/x86_64-linux-gnu:${HERE}/usr/lib32:${HERE}/usr/lib64:${HERE}/share/../lib:${LD_LIBRARY_PATH}"
exec "${HERE}/bin/youtube-downloader" "$@"
APPRUN
chmod +x AppDir/usr/bin/AppRun

cat > AppDir/usr/share/applications/youtube-downloader.desktop << DESKTOP
[Desktop Entry]
Type=Application
Name=YouTube Downloader
Exec=youtube-downloader
Icon=youtube-downloader
Categories=AudioVideo;Network;
DESKTOP

# Creation AppImage
echo "[4/4] Creation AppImage..."
VERSION=$VERSION appimage-builder --recipe scripts/appimage-builder.yml 2>/dev/null || {
    echo "[INFO] Utilisation de linuxdeploy en fallback..."
    appimagekit deploy AppDir 2>/dev/null || {
        echo "[ERREUR] Impossible de creer l'AppImage."
        echo "Vous pouvez installer appimagekit : https://github.com/AppImage/AppImageKit"
        exit 1
    }
}

echo ""
echo "============================================================"
echo "  COMPILATION TERMINEE"
echo "  AppImage : YouTube-Downloader-$VERSION-x86_64.AppImage"
echo "============================================================"
