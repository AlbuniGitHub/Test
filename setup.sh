#!/bin/bash

# Git-Repository klonen
git clone https://github.com/AlbuniGitHub/Bluetooth_Robotersteuerung
cd repository

# Abhängigkeiten installieren (falls eine requirements.txt vorhanden ist)
pip install -r requirements.txt

# Buildozer installieren, falls noch nicht geschehen
pip install buildozer

# Fehlende Pakete installieren
sudo apt update
sudo apt install -y python3-pip python3-dev build-essential
sudo apt install -y openjdk-8-jdk
sudo apt install -y libncurses5 libncurses5-dev

# Buildozer verwenden, um das Projekt zu erstellen
buildozer android debug
