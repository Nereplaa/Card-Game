# -*- coding: utf-8 -*-
"""
Akıllı Sporcu Kart Ligi Simülasyonu – Giriş Noktası
Kocaeli Sağlık ve Teknoloji Üniversitesi – Programlama Lab 2 – Proje 1

Gereksinimler:
    pip install PyQt5
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui import AnaWindow


def main():
    # Yüksek çözünürlüklü ekranlar için ölçekleme
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Akıllı Sporcu Kart Ligi")
    app.setApplicationVersion("1.0")

    pencere = AnaWindow()
    pencere.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
