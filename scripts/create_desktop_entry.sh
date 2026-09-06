#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
mkdir -p "$DESKTOP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/MeshCom-Guru.desktop"
ICON="$PROJECT_DIR/icons/meshcom.svg"
[ -f "$ICON" ] || ICON="$PROJECT_DIR/icons/icon.svg"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=MeshCom-Guru
Comment=MeshCom Python Client
Exec=python3 "$PROJECT_DIR/main.py"
Path=$PROJECT_DIR
Icon=$ICON
Terminal=false
Categories=Utility;Network;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"
command -v gio >/dev/null 2>&1 && gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
echo "Desktop-Verknüpfung erstellt: $DESKTOP_FILE"
