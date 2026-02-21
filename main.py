import sys  
import subprocess  
import math  
import random  
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsTextItem  
from PyQt6.QtGui import QPen, QColor, QFont, QBrush  
from PyQt6.QtCore import QTimer, Qt  
import os  
  
WIDTH = 1400  
HEIGHT = 800  
RADAR_SIZE = 800  
CENTER_X = RADAR_SIZE // 2  
CENTER_Y = HEIGHT // 2  
MAX_RADIUS = 360  
PANEL_X = RADAR_SIZE + 20  
HUD_GREEN = QColor(0, 255, 120)  
  
PING_FILE = "ping.wav"  
if not os.path.isfile(PING_FILE):  
    os.system(f"sox -n -r 44100 -b 16 {PING_FILE} synth 0.05 sine 880")  
  
def scan_wifi():  
    result = subprocess.run(  
        ["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi", "list"],  
        capture_output=True,  
        text=True  
    )  
    nets = []  
    for line in result.stdout.splitlines():  
        if not line:  
            continue  
        p = line.split(":")  
        if len(p) != 2:  
            continue  
        ssid, signal = p  
        nets.append({  
            "ssid": ssid if ssid else "<hidden>",  
            "signal": int(signal)  
        })  
    return nets  
  
class HUD(QGraphicsView):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("WiFi SONAR — WD HUD v7")  
        self.setFixedSize(WIDTH, HEIGHT)  
        self.setStyleSheet("background-color: black;")  
        self.scene = QGraphicsScene(0, 0, WIDTH, HEIGHT)  
        self.setScene(self.scene)  
  
        self.sonar_r = 0  
        self.full = False  
        self.positions = {}  # ssid -> [angle, radius]  
        self.triggered_ssid = set()  
        self.glitch_effects = {}  
        self.scanlines_offset = 0  
        self.rotation_speed = 0.01  # radian/frame  
  
        self.timer = QTimer()  
        self.timer.timeout.connect(self.draw)  
        self.timer.start(60)  
  
    def keyPressEvent(self, e):  
        if e.key() == Qt.Key.Key_F11:  
            self.full = not self.full  
            self.showFullScreen() if self.full else self.showNormal()  
        if e.key() == Qt.Key.Key_Escape and self.full:  
            self.full = False  
            self.showNormal()  
  
    def draw_grid(self):  
        pen = QPen(QColor(0, 255, 120, 20))  
        step = 80  
        for x in range(0, RADAR_SIZE, step):  
            self.scene.addLine(x, 0, x, HEIGHT, pen)  
        for y in range(0, HEIGHT, step):  
            self.scene.addLine(0, y, RADAR_SIZE, y, pen)  
  
    def draw_scanlines(self):  
        self.scanlines_offset += 2  
        if self.scanlines_offset > HEIGHT:  
            self.scanlines_offset = 0  
        pen = QPen(QColor(0, 255, 120, 50))  
        for y in range(-20, HEIGHT, 20):  
            self.scene.addLine(0, y + self.scanlines_offset, RADAR_SIZE, y + self.scanlines_offset, pen)  
  
    def draw(self):  
        self.scene.clear()  
        self.draw_grid()  
        self.draw_scanlines()  
  
        # CENTER  
        self.scene.addEllipse(CENTER_X - 6, CENTER_Y - 6, 12, 12, QPen(HUD_GREEN), QBrush(HUD_GREEN))  
  
        # STATIC RINGS  
        for r in range(120, MAX_RADIUS + 1, 120):  
            self.scene.addEllipse(CENTER_X - r, CENTER_Y - r, r * 2, r * 2, QPen(QColor(0, 255, 120, 30)))  
  
        # SONAR WAVE  
        self.scene.addEllipse(CENTER_X - self.sonar_r, CENTER_Y - self.sonar_r, self.sonar_r * 2, self.sonar_r * 2,  
                              QPen(QColor(0, 255, 120, 120)))  
  
        self.sonar_r += 3  
        if self.sonar_r > MAX_RADIUS:  
            self.sonar_r = 0  
            self.triggered_ssid.clear()  
            self.glitch_effects.clear()  
  
        nets = scan_wifi()  
  
        # PANEL BOCZNY  
        panel_title = QGraphicsTextItem("NETWORKS")  
        panel_title.setFont(QFont("Courier New", 14, QFont.Weight.Bold))  
        panel_title.setDefaultTextColor(HUD_GREEN)  
        panel_title.setPos(PANEL_X, 20)  
        self.scene.addItem(panel_title)  
        y_offset = 60  
  
        for n in nets:  
            ssid = n["ssid"]  
            signal = n["signal"]  
  
            if ssid not in self.positions:  
                # radius zależny od sygnału, kąty losowe  
                radius = max(50, (100 - signal) * 3)  
                angle = random.uniform(0, 2 * math.pi)  
                self.positions[ssid] = [angle, radius]  
  
            # ROTATION  
            self.positions[ssid][0] += self.rotation_speed  
            angle = self.positions[ssid][0]  
            radius = self.positions[ssid][1]  
  
            x = CENTER_X + math.cos(angle) * radius  
            y = CENTER_Y + math.sin(angle) * radius  
  
            if signal >= 60:  
                c = QColor(0, 255, 120)  
            elif signal >= 40:  
                c = QColor(255, 200, 0)  
            else:  
                c = QColor(255, 80, 80)  
  
            # POINT  
            self.scene.addEllipse(x - 4, y - 4, 8, 8, QPen(c), QBrush(c))  
  
            # LABEL + GLITCH EFFECT  
            show_label = False  
            if self.sonar_r >= radius - 6 and self.sonar_r <= radius + 6:  
                show_label = True  
                if ssid not in self.triggered_ssid:  
                    os.system(f"aplay -q {PING_FILE} &")  
                    self.triggered_ssid.add(ssid)  
                    self.glitch_effects[ssid] = 6  
  
            if ssid in self.glitch_effects and self.glitch_effects[ssid] > 0:  
                flash_c = QColor(random.randint(0, 255), 255, random.randint(0, 255))  
                t = QGraphicsTextItem(ssid)  
                t.setFont(QFont("Courier New", 11, QFont.Weight.Bold))  
                t.setDefaultTextColor(flash_c)  
                t.setPos(x + random.randint(-2, 2), y + random.randint(-2, 2))  
                self.scene.addItem(t)  
                self.glitch_effects[ssid] -= 1  
            elif show_label:  
                t = QGraphicsTextItem(ssid)  
                t.setFont(QFont("Courier New", 9))  
                t.setDefaultTextColor(c)  
                t.setPos(x + 8, y - 6)  
                self.scene.addItem(t)  
  
            # PANEL ENTRY  
            line = QGraphicsTextItem(f"{ssid}  [{signal}%]")  
            line.setFont(QFont("Courier New", 10))  
            line.setDefaultTextColor(c)  
            line.setPos(PANEL_X, y_offset)  
            self.scene.addItem(line)  
            y_offset += 22  
  
        # GREEN FLASHES AROUND CENTER  
        for i in range(2):  
            r_flash = self.sonar_r + i * 15  
            alpha = max(0, 120 - i*40)  
            self.scene.addEllipse(CENTER_X - r_flash, CENTER_Y - r_flash, r_flash * 2, r_flash * 2,  
                                  QPen(QColor(0, 255, 120, alpha)))  
  
if __name__ == "__main__":  
    app = QApplication(sys.argv)  
    hud = HUD()  
    hud.show()  
    sys.exit(app.exec())  
