# ARQUIVO: painel.py
# Este é o código da Interface Gráfica
import sys
import subprocess
import pyperclip
from pyngrok import ngrok
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import qrcode
from io import BytesIO 
import os

# --- Componente Botão Switch ---
class ModernSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumSize(60, 30)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color = QColor("#4CAF50") if self.isChecked() else QColor("#F44336")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.setBrush(QBrush(QColor("white")))
        x_pos = self.width() - 26 if self.isChecked() else 4
        painter.drawEllipse(x_pos, 4, 22, 22)

# --- Thread para rodar Ngrok e Servidor em segundo plano ---
class NgrokThread(QThread):
    ngrok_started = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port, server_path):
        super().__init__()
        self.port = port
        self.server_path = server_path
        self.server_process = None

    def run(self):
        try:
            # 1. Garante que Ngrok antigo morreu
            ngrok.kill()
            
            # 2. Inicia novo túnel
            public_url = ngrok.connect(self.port).public_url
            pyperclip.copy(public_url)
            
            # 3. Inicia server.py de forma SILENCIOSA (Sem janela extra)
            self.server_process = subprocess.Popen(
                ["python3", self.server_path],
                stdout=subprocess.DEVNULL, # Esconde logs do terminal
                stderr=subprocess.DEVNULL,
                stdin=subprocess.PIPE
            )
            
            self.ngrok_started.emit(public_url)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        # Mata o processo do servidor Flask
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=2)
            except:
                self.server_process.kill()
        # Mata o Ngrok
        ngrok.kill()

# --- Janela Principal ---
class NgrokServerManager(QWidget):
    def __init__(self):
        super().__init__()
        self.ngrok_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Servidor de Aplicação - Youtube Downloader')
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #121212; color: white;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Título / Status
        self.label_status = QLabel("Status: DESLIGADO")
        self.label_status.setFont(QFont('Arial', 14, QFont.Bold))
        self.label_status.setStyleSheet("color: #F44336;")
        
        # Botão
        self.switch = ModernSwitch()
        self.switch.clicked.connect(self.toggle_services)
        
        self.info_label = QLabel("Clique para iniciar")
        self.info_label.setStyleSheet("color: #888; font-size: 12px;")

        # QR Code
        self.qr_code_label = QLabel()
        self.qr_code_label.setFixedSize(300, 300)
        self.qr_code_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px;")
        self.qr_code_label.setAlignment(Qt.AlignCenter)

        self.desenv_label = QLabel("Desenvolvido por Daniel Boechat")
        self.desenv_label.setStyleSheet("color: #888; font-size: 12px;")

        # Link Texto
        self.link_label = QLabel("")
        self.link_label.setWordWrap(True)
        self.link_label.setAlignment(Qt.AlignCenter)
        self.link_label.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 10px;")

        layout.addWidget(self.label_status, alignment=Qt.AlignCenter)
        layout.addWidget(self.switch, alignment=Qt.AlignCenter)
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.qr_code_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.desenv_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.link_label, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def toggle_services(self):
        if self.switch.isChecked():
            self.start_all()
        else:
            self.stop_all()

    def start_all(self):
        # --- CONFIGURAÇÃO DO CAMINHO ---
        # Tenta pegar o diretório atual onde o script está rodando
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.join(current_dir, "server.py")

        # Se não achar no diretório atual, usa o caminho absoluto que você forneceu
        if not os.path.exists(server_path):
             server_path = "/media/daniel/Arquivos 1/Automacoes/Automacoes/Projeto 21 - Youtube Download Android/server.py"

        if not os.path.exists(server_path):
             QMessageBox.critical(self, "Erro Fatal", f"Não encontrei o arquivo server.py em:\n{server_path}")
             self.switch.setChecked(False)
             return

        self.label_status.setText("Status: INICIANDO...")
        self.label_status.setStyleSheet("color: #FFD700;")
        self.info_label.setText("Iniciando túnel e servidor...")
        
        # Limpa execuções anteriores
        if self.ngrok_thread is not None:
            self.ngrok_thread.stop()

        self.ngrok_thread = NgrokThread(5000, server_path)
        self.ngrok_thread.ngrok_started.connect(self.on_success)
        self.ngrok_thread.error_occurred.connect(self.on_error)
        self.ngrok_thread.start()

    def on_success(self, url):
        self.label_status.setText("Status: ONLINE!")
        self.label_status.setStyleSheet("color: #4CAF50;")
        self.info_label.setText("Escaneie o QR Code no App:")
        self.link_label.setText(f"{url}\n(Copiado para área de transferência!)")
        
        self.generate_qr_code(url)

    def on_error(self, error_msg):
        self.switch.setChecked(False)
        self.stop_all()
        QMessageBox.critical(self, "Erro", f"Falha ao iniciar: {error_msg}")

    def generate_qr_code(self, data):
        # Gera o QR Code
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # FIX DE RENDERIZAÇÃO: Salva em memória como PNG
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        # Carrega o PNG no PyQt (Sem distorção)
        q_pixmap = QPixmap()
        q_pixmap.loadFromData(buffer.getvalue())
        
        self.qr_code_label.setPixmap(q_pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def stop_all(self):
        if self.ngrok_thread:
            self.ngrok_thread.stop()
        
        self.label_status.setText("Status: DESLIGADO")
        self.label_status.setStyleSheet("color: #F44336;")
        self.info_label.setText("Clique para iniciar")
        self.qr_code_label.clear()
        self.link_label.setText("")

    def closeEvent(self, event):
        self.stop_all()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NgrokServerManager()
    ex.show()
    sys.exit(app.exec_())