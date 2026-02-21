import sys
import subprocess
import math
import random
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsView, QGraphicsScene, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPen, QColor, QFont, QBrush
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtMultimedia import QSoundEffect

WIDTH = 1400
HEIGHT = 800
RADAR_SIZE = 800
CENTER_X = RADAR_SIZE // 2
CENTER_Y = HEIGHT // 2
HUD_GREEN = QColor(0, 255, 120)
SWEEP_COLOR = QColor(0, 255, 120, 50)

# Tworzenie profilu sieci na podstawie nazwy
def detect_profile(ssid):
    s = ssid.lower()
    if "mobile" in s or "4g" in s or "lte" in s:
        return "MOBILE"
    elif "home" in s or "wifi" in s or "router" in s:
        return "HOME"
    elif "router" in s:
        return "ROUTER"
    return "UNKNOWN"

# Funkcja skanująca Wi-Fi
def scan_wifi():
    subprocess.run(["nmcli","dev","wifi","rescan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = subprocess.run(["nmcli","-t","-f","SSID,SIGNAL,BSSID","dev","wifi","list"], capture_output=True, text=True)
    nets=[]
    for line in result.stdout.splitlines():
        if not line.strip(): continue
        parts=line.split(":")
        if len(parts)<3: continue
        ssid, signal, bssid = parts[0] or "<hidden>", parts[1], parts[2]
        try: signal=int(signal)
        except ValueError: signal=0
        nets.append({
            "id":bssid,
            "ssid":ssid,
            "signal":signal,
            "status":"CONNECTED" if signal>75 else ("ACTIVE" if signal>40 else "WEAK"),
            "profile":detect_profile(ssid)
        })
    return nets

class HUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WiFi SONAR – Watch Dogs HUD")
        self.setFixedSize(WIDTH, HEIGHT)
        self.setStyleSheet("background-color:black;")
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # Radar
        self.view = QGraphicsView()
        self.view.setFixedSize(RADAR_SIZE, HEIGHT)
        self.scene = QGraphicsScene(0, 0, RADAR_SIZE, HEIGHT)
        self.view.setScene(self.scene)
        self.layout.addWidget(self.view)

        # Panel boczny
        self.panel_widget = QWidget()
        self.panel_layout = QVBoxLayout()
        self.panel_widget.setLayout(self.panel_layout)
        self.layout.addWidget(self.panel_widget)

        # Lista sieci
        self.panel_list = QListWidget()
        self.panel_layout.addWidget(self.panel_list)

        # Info panel
        self.panel_info = QLabel()
        self.panel_info.setStyleSheet(
            "color: rgb(0,255,120); font-family:Courier New; font-size:14px; background-color:black;"
        )
        self.panel_info.setWordWrap(True)
        self.panel_layout.addWidget(self.panel_info)
        self.panel_list.itemClicked.connect(self.show_info)

        # Dźwięk ping
        self.ping_sound = QSoundEffect()
        self.ping_sound.setSource(QUrl.fromLocalFile("ping.wav"))
        self.ping_sound.setVolume(0.5)

        # HUD variables
        self.positions = {}  # bssid -> [angle,radius]
        self.nets = []
        self.sweep_angle = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_hud)
        self.timer.start(100)  # update co 0.1s

    def draw_grid(self):
        pen = QPen(QColor(0,255,120,30))
        step = 80
        for x in range(0,RADAR_SIZE,step):
            self.scene.addLine(x,0,x,HEIGHT,pen)
        for y in range(0,HEIGHT,step):
            self.scene.addLine(0,y,RADAR_SIZE,y,pen)
        for r in range(100,RADAR_SIZE//2,100):
            self.scene.addEllipse(CENTER_X-r, CENTER_Y-r, r*2, r*2, QPen(QColor(0,255,120,50)))

    def show_info(self, item):
        key = item.data(Qt.ItemDataRole.UserRole)
        net = next((n for n in self.nets if n['id']==key), None)
        if net:
            # Odtwarzanie dźwięku
            self.ping_sound.play()
            # Pełny BSSID i info
            self.panel_info.setText(
                f"SSID: {net['ssid']}\n"
                f"Signal: {net['signal']}%\n"
                f"Status: {net['status']}\n"
                f"BSSID: {net['id']}\n"
                f"Profile: {net['profile']}"
            )

    def update_hud(self):
        self.scene.clear()
        self.draw_grid()

        # Center
        self.scene.addEllipse(CENTER_X-6, CENTER_Y-6, 12, 12, QPen(HUD_GREEN), QBrush(HUD_GREEN))

        # Radar sweep
        self.sweep_angle += 0.05
        if self.sweep_angle > 2*math.pi: self.sweep_angle -= 2*math.pi
        sweep_length = RADAR_SIZE//2
        end_x = CENTER_X + math.cos(self.sweep_angle) * sweep_length
        end_y = CENTER_Y + math.sin(self.sweep_angle) * sweep_length
        self.scene.addLine(CENTER_X, CENTER_Y, end_x, end_y, QPen(SWEEP_COLOR,2))

        # Skanowanie sieci
        self.nets = scan_wifi()
        self.panel_list.clear()
        for n in self.nets:
            # Lista boczna z kolorami według sygnału
            item = QListWidgetItem(n['ssid'])
            if n['signal'] >= 60:
                item.setForeground(QBrush(QColor(0,255,120)))
            elif n['signal'] >= 40:
                item.setForeground(QBrush(QColor(255,200,0)))
            else:
                item.setForeground(QBrush(QColor(255,80,80)))
            item.setData(Qt.ItemDataRole.UserRole, n['id'])
            self.panel_list.addItem(item)

            # Pozycja punktu na radarze
            if n['id'] not in self.positions:
                angle = random.uniform(0,2*math.pi)
                radius = max(50,(100-n['signal'])*3)
                self.positions[n['id']] = [angle,radius]
            angle,radius = self.positions[n['id']]
            angle += 0.01
            self.positions[n['id']][0] = angle
            x = CENTER_X + math.cos(angle)*radius
            y = CENTER_Y + math.sin(angle)*radius

            # Kolor punktu
            if n['signal']>=60: c = QColor(0,255,120)
            elif n['signal']>=40: c = QColor(255,200,0)
            else: c = QColor(255,80,80)

            self.scene.addEllipse(x-5, y-5, 10, 10, QPen(c), QBrush(c))

            # Etykieta SSID na radarze
            t = self.scene.addText(n['ssid'], QFont("Courier New",9))
            t.setDefaultTextColor(c)
            t.setPos(x+8, y-6)

if __name__=="__main__":
    app = QApplication(sys.argv)
    hud = HUD()
    hud.show()
    sys.exit(app.exec())
