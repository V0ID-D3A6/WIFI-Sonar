# WiFi SONAR — Watch Dogs Style HUD

## Project Overview

WiFi SONAR is a **Python 3 / PyQt6** project that emulates a **Watch Dogs-style HUD** to visualize nearby WiFi networks on a radar-like display.  
It’s designed for Linux systems and provides a visual, interactive, hacker-style interface for monitoring WiFi signals.

**Main Features:**
- Rotating points representing nearby WiFi networks  
- Scanlines and green HUD effects  
- Glitch effect and label animation when SSID is detected  
- Ping sound triggered when the sonar wave reaches a network  
- Side panel displaying SSID names and signal strength  
- Fullscreen HUD mode for immersive experience  

---

## Requirements

- Python 3  
- PyQt6  
- sox (for generating ping sound)  
- alsa-utils (Linux sound playback)  
- nmcli (Linux WiFi scanning)

Install dependencies on Debian / Kali Linux:

```bash
Instalation:

sudo apt update
sudo apt install python3-pyqt6 sox alsa-utils -y

Clone the repository:

git clone https://github.com/V0ID-D3A6/WIFI-sonar.git
cd WIFI-sonar

Generate the ping sound (if ping.wav does not exist, it will be created automatically):

sox -n -r 44100 -b 16 ping.wav synth 0.05 sine 880

Ensure main.py is present in the project folder.

Running the HUD


Run the HUD with:

python3 main.py



Controls:

F11 — toggle fullscreen / exit fullscreen

ESC — exit fullscreen or close application



How it Works

The sonar wave expands from the center of the radar.

WiFi networks are represented as points that slowly rotate around the center.

When the sonar wave touches a point, a short ping sound is played and the SSID label appears with a glitch effect.

Green flashes and scanlines enhance the Watch Dogs-style HUD feel.

The side panel displays all detected SSIDs with their signal strength percentage.



License

MIT License — feel free to use, modify, and share this project.
