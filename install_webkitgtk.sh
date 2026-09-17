#!/bin/bash
set -e
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi
$SUDO apt-get update
$SUDO apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 libwebkit2gtk-4.1-0 gir1.2-gdkx11-3.0

echo
 echo "WebKitGTK ist installiert. MeshCom-Guru jetzt neu starten."
