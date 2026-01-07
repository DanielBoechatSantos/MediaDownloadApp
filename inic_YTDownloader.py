# Inicializador - Youtube Download

import sys
import subprocess
import threading
import pyperclip
from pyngrok import ngrok
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont

class ModernSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumSize(60, 30)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Cores baseadas no estado
        bg_color = QColor("#4CAF50") if self.isChecked() else QColor("#F44336")
        circle_color = QColor("white")
        
        # Desenha o fundo (pílula)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        # Desenha o círculo do interruptor
        x_pos = self.width() - 26 if self.isChecked() else 4
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(x_pos, 4, 22, 22)

class NgrokServerManager(QWidget):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Controlador Ngrok & Server')
        self.setFixedSize(400, 250)
        self.setStyleSheet("background-color: #121212; color: white;")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label_status = QLabel("Status: DESLIGADO")
        self.label_status.setFont(QFont('Arial', 12, QFont.Bold))
        self.label_status.setStyleSheet("color: #F44336; margin-bottom: 20px;")
        
        self.switch = ModernSwitch()
        self.switch.clicked.connect(self.toggle_services)

        self.info_label = QLabel("Clique para iniciar Ngrok e Servidor")
        self.info_label.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")

        layout.addWidget(self.label_status, alignment=Qt.AlignCenter)
        layout.addWidget(self.switch, alignment=Qt.AlignCenter)
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)

    def toggle_services(self):
        if self.switch.isChecked():
            self.start_all()
        else:
            self.stop_all()

    def start_all(self):
        try:
            # 1. Iniciar Ngrok (Porta 5000 - ajuste se seu server.py usar outra)
            public_url = ngrok.connect(5000).public_url
            pyperclip.copy(public_url)
            
            # 2. Iniciar server.py
            path = "/media/daniel/Arquivos 1/Automacoes/Automacoes/Projeto 21 - Youtube Download Android/server.py"
            self.server_process = subprocess.Popen(["python3", path])
            
            self.label_status.setText(f"Status: ONLINE\nLink copiado!")
            self.label_status.setStyleSheet("color: #4CAF50;")
        except Exception as e:
            self.label_status.setText(f"Erro: {str(e)}")
            self.switch.setChecked(False)

    def stop_all(self):
        if self.server_process:
            self.server_process.terminate()
        ngrok.kill()
        self.label_status.setText("Status: DESLIGADO")
        self.label_status.setStyleSheet("color: #F44336;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NgrokServerManager()
    ex.show()
    sys.exit(app.exec_())