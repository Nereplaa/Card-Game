# -*- coding: utf-8 -*-
"""
PyQt5 Arayüzü – Akıllı Sporcu Kart Ligi Simülasyonu
Dinamik güncelleme, kart widget'ları, istatistik ekranı, oyun sonu raporu
"""
import sys
from typing import Optional, List

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QFrame, QScrollArea, QGridLayout, QTextEdit, QSplitter,
    QProgressBar, QDialog, QDialogButtonBox, QMessageBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QIcon

from models import Sporcu, Brans
from players import Kullanici, Bilgisayar
from strategies import strateji_olustur
from game_engine import VeriOkuyucu, OyunYonetici

# ---------------------------------------------------------------------------
# RENK PALETI
# ---------------------------------------------------------------------------
RENKLER = {
    "bg_dark": "#1A1A2E",
    "bg_card": "#16213E",
    "bg_panel": "#0F3460",
    "accent": "#E94560",
    "accent2": "#533483",
    "text_primary": "#EAEAEA",
    "text_secondary": "#A8DADC",
    "futbol": "#2ECC71",
    "basketbol": "#E67E22",
    "voleybol": "#3498DB",
    "enerji_yuksek": "#2ECC71",
    "enerji_orta": "#F39C12",
    "enerji_dusuk": "#E74C3C",
    "enerji_kritik": "#C0392B",
    "kazanildi": "#27AE60",
    "kaybedildi": "#C0392B",
    "beraberlik": "#95A5A6",
    "skor_bg": "#E94560",
}

BRANS_RENKLER = {
    Brans.FUTBOL: RENKLER["futbol"],
    Brans.BASKETBOL: RENKLER["basketbol"],
    Brans.VOLEYBOL: RENKLER["voleybol"],
}

BRANS_IKONLAR = {
    Brans.FUTBOL: "⚽",
    Brans.BASKETBOL: "🏀",
    Brans.VOLEYBOL: "🏐",
}

STIL_TEMEL = f"""
QWidget {{
    background-color: {RENKLER["bg_dark"]};
    color: {RENKLER["text_primary"]};
    font-family: "Segoe UI", Arial, sans-serif;
}}
QScrollBar:vertical {{
    background: {RENKLER["bg_card"]};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {RENKLER["bg_panel"]};
    border-radius: 4px;
}}
"""


# ---------------------------------------------------------------------------
# KART WİDGET'I
# ---------------------------------------------------------------------------

class KartWidget(QFrame):
    """Tek bir sporcu kartını gösteren özel widget."""

    secildi = pyqtSignal(object)  # Sporcu nesnesi

    def __init__(self, sporcu: Sporcu, secilecek: bool = True, parent=None):
        super().__init__(parent)
        self._sporcu = sporcu
        self._secilecek = secilecek
        self._secili = False
        self._setStyle()
        self._buildUI()

    def _setStyle(self):
        brans_renk = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(195, 230)
        self.setStyleSheet(f"""
            KartWidget {{
                background-color: {RENKLER["bg_card"]};
                border: 2px solid {brans_renk};
                border-radius: 10px;
                padding: 4px;
            }}
            KartWidget:hover {{
                border: 2px solid #FFFFFF;
                background-color: #1e2d50;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor if self._secilecek else Qt.ArrowCursor)

    def _buildUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        brans_renk = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        ikon = BRANS_IKONLAR.get(self._sporcu.brans, "")

        # Başlık: branş ikonu + ad
        baslik = QLabel(f"{ikon} {self._sporcu.sporcu_adi}")
        baslik.setStyleSheet(f"color: {brans_renk}; font-weight: bold; font-size: 12px;")
        baslik.setWordWrap(True)
        layout.addWidget(baslik)

        # Takım
        takim_lb = QLabel(self._sporcu.sporcu_takim)
        takim_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 10px;")
        layout.addWidget(takim_lb)

        # Özellikler
        ozellikler = self._sporcu.get_ozellikler()
        for oz_ad, oz_val in ozellikler.items():
            oz_lb = QLabel(f"{oz_ad}: {oz_val}")
            oz_lb.setStyleSheet("font-size: 10px; color: #CCC;")
            layout.addWidget(oz_lb)

        # Dayanıklılık + Seviye
        stats_lb = QLabel(
            f"Dayanıklılık: {self._sporcu.dayaniklilik}  |  Sv: {self._sporcu.seviye}"
        )
        stats_lb.setStyleSheet("font-size: 10px; color: #AAA;")
        layout.addWidget(stats_lb)

        # Enerji bar
        enerji_label = QLabel(f"Enerji: {self._sporcu.enerji}/{self._sporcu.max_enerji}")
        enerji_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(enerji_label)

        self._enerji_bar = QProgressBar()
        self._enerji_bar.setMaximum(self._sporcu.max_enerji)
        self._enerji_bar.setValue(self._sporcu.enerji)
        self._enerji_bar.setFixedHeight(10)
        self._enerji_bar.setTextVisible(False)
        self._guncelle_enerji_renk()
        layout.addWidget(self._enerji_bar)

        # Özel yetenek
        ozy = self._sporcu.ozel_yetenek
        ozy_lb = QLabel(f"✨ {ozy.ad}")
        ozy_lb.setStyleSheet("font-size: 9px; color: #F1C40F; font-style: italic;")
        ozy_lb.setToolTip(ozy.aciklama)
        layout.addWidget(ozy_lb)

        # Oynanamaz işareti
        if not self._sporcu.oynanabilir_mi():
            overlay = QLabel("KULLANILDI")
            overlay.setAlignment(Qt.AlignCenter)
            overlay.setStyleSheet(
                "color: red; font-weight: bold; font-size: 11px; background: rgba(0,0,0,0.5);"
            )
            layout.addWidget(overlay)

        layout.addStretch()

    def _guncelle_enerji_renk(self):
        e = self._sporcu.enerji
        if e > 70:
            renk = RENKLER["enerji_yuksek"]
        elif e >= 40:
            renk = RENKLER["enerji_orta"]
        elif e >= 20:
            renk = RENKLER["enerji_dusuk"]
        else:
            renk = RENKLER["enerji_kritik"]
        self._enerji_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {renk}; border-radius: 4px; }}"
            f"QProgressBar {{ background-color: #333; border-radius: 4px; }}"
        )

    def guncelle(self):
        """Kart durumu değiştiğinde yeniden render et"""
        # Widget'ı temizle
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            if w:
                w.deleteLater()
        self._buildUI()

    def sec(self):
        self._secili = True
        brans_renk = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        self.setStyleSheet(f"""
            KartWidget {{
                background-color: #2a3a60;
                border: 3px solid {RENKLER["accent"]};
                border-radius: 10px;
            }}
        """)

    def sec_kaldir(self):
        self._secili = False
        self._setStyle()

    def mousePressEvent(self, event):
        if self._secilecek and self._sporcu.oynanabilir_mi():
            self.secildi.emit(self._sporcu)

    @property
    def sporcu(self) -> Sporcu:
        return self._sporcu


# ---------------------------------------------------------------------------
# HOŞGELDİN / BAŞLANGIÇ EKRANI
# ---------------------------------------------------------------------------

class HosgeldinEkrani(QWidget):
    oyun_baslat = pyqtSignal(str)  # zorluk: 'Kolay' | 'Orta'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Başlık
        baslik = QLabel("🏆 AKILLI SPORCU KART LİGİ")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet(
            f"color: {RENKLER['accent']}; font-size: 28px; font-weight: bold;"
        )
        layout.addWidget(baslik)

        alt_baslik = QLabel("Simülasyon v1.0")
        alt_baslik.setAlignment(Qt.AlignCenter)
        alt_baslik.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 14px;")
        layout.addWidget(alt_baslik)

        # Ayırıcı
        layout.addSpacing(30)

        # Zorluk seçimi
        zorluk_lb = QLabel("Zorluk Seviyesi Seçin:")
        zorluk_lb.setAlignment(Qt.AlignCenter)
        zorluk_lb.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(zorluk_lb)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(30)

        self._btn_kolay = QPushButton("🟢  KOLAY")
        self._btn_orta = QPushButton("🟡  ORTA")

        for btn, renk in [(self._btn_kolay, "#27AE60"), (self._btn_orta, "#E67E22")]:
            btn.setFixedSize(160, 60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {renk}; color: white;
                    border-radius: 12px; font-size: 16px; font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: white; color: {renk};
                }}
            """)
            btn_layout.addWidget(btn)

        self._btn_kolay.clicked.connect(lambda: self.oyun_baslat.emit("Kolay"))
        self._btn_orta.clicked.connect(lambda: self.oyun_baslat.emit("Orta"))

        layout.addLayout(btn_layout)

        # Bilgi kutusu
        layout.addSpacing(20)
        bilgi = QLabel(
            "⚽ Futbolcu  |  🏀 Basketbolcu  |  🏐 Voleybolcu\n"
            "Her oyuncuya 12 kart dağıtılır (4 x 3 branş)\n"
            "Tur sırası: Futbol → Basketbol → Voleybol → ..."
        )
        bilgi.setAlignment(Qt.AlignCenter)
        bilgi.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 12px; line-height: 1.6;")
        layout.addWidget(bilgi)


# ---------------------------------------------------------------------------
# KART PANELİ (scrollable grid)
# ---------------------------------------------------------------------------

class KartPaneli(QScrollArea):
    kart_secildi = pyqtSignal(object)

    def __init__(self, baslik: str, secilecek: bool = True, parent=None):
        super().__init__(parent)
        self._secilecek = secilecek
        self._kart_widgetlari: List[KartWidget] = []
        self._secili_widget: Optional[KartWidget] = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(f"background-color: {RENKLER['bg_dark']}; border: none;")

        container = QWidget()
        vlay = QVBoxLayout(container)
        vlay.setAlignment(Qt.AlignTop)

        self._baslik_lb = QLabel(baslik)
        self._baslik_lb.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {RENKLER['accent']}; margin-bottom: 6px;"
        )
        vlay.addWidget(self._baslik_lb)

        self._grid = QGridLayout()
        self._grid.setSpacing(10)
        vlay.addLayout(self._grid)

        self.setWidget(container)

    def kartlari_yukle(self, sporcular: List[Sporcu]):
        """Tüm kart widget'larını temizle ve yeniden yükle"""
        self._kart_widgetlari.clear()
        self._secili_widget = None

        # Grid'i temizle
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, sporcu in enumerate(sporcular):
            kw = KartWidget(sporcu, secilecek=self._secilecek)
            kw.secildi.connect(self._kart_sec)
            self._kart_widgetlari.append(kw)
            self._grid.addWidget(kw, idx // 2, idx % 2)

    def _kart_sec(self, sporcu: Sporcu):
        # Seçimi kaldır
        if self._secili_widget:
            self._secili_widget.sec_kaldir()
        # Yeni seçim
        for kw in self._kart_widgetlari:
            if kw.sporcu is sporcu:
                kw.sec()
                self._secili_widget = kw
                break
        self.kart_secildi.emit(sporcu)

    def secimi_kaldir(self):
        if self._secili_widget:
            self._secili_widget.sec_kaldir()
            self._secili_widget = None

    def kartlari_guncelle(self):
        for kw in self._kart_widgetlari:
            kw.guncelle()

    def baslik_guncelle(self, yeni_baslik: str):
        self._baslik_lb.setText(yeni_baslik)

    def filtrele(self, brans: Optional[Brans]):
        """Belirli branştaki kartları göster/diğerlerini soluklaştır"""
        for kw in self._kart_widgetlari:
            if brans is None or kw.sporcu.brans == brans:
                kw.setEnabled(True)
                kw.setGraphicsEffect(None)
            else:
                kw.setEnabled(False)


# ---------------------------------------------------------------------------
# ORTA PANEL: TUR BİLGİSİ, KARŞILAŞTIRMA, SONUÇ
# ---------------------------------------------------------------------------

class OrtaPanel(QWidget):

    tur_oyna_sinyal = pyqtSignal()
    legend_aktif_degisti = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # SKOR TABLOSU
        skor_frame = QFrame()
        skor_frame.setStyleSheet(
            f"background-color: {RENKLER['bg_panel']}; border-radius: 10px; padding: 8px;"
        )
        skor_lay = QHBoxLayout(skor_frame)

        self._k_skor_lb = QLabel("0")
        self._k_skor_lb.setStyleSheet(
            f"font-size: 36px; font-weight: bold; color: {RENKLER['accent']};"
        )
        self._k_skor_lb.setAlignment(Qt.AlignCenter)

        vs_lb = QLabel("VS")
        vs_lb.setStyleSheet("font-size: 18px; color: #AAA; font-weight: bold;")
        vs_lb.setAlignment(Qt.AlignCenter)

        self._b_skor_lb = QLabel("0")
        self._b_skor_lb.setStyleSheet(
            f"font-size: 36px; font-weight: bold; color: {RENKLER['accent2']};"
        )
        self._b_skor_lb.setAlignment(Qt.AlignCenter)

        self._k_oyuncu_lb = QLabel("Oyuncu")
        self._k_oyuncu_lb.setAlignment(Qt.AlignCenter)
        self._k_oyuncu_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 11px;")

        self._b_oyuncu_lb = QLabel("Bilgisayar")
        self._b_oyuncu_lb.setAlignment(Qt.AlignCenter)
        self._b_oyuncu_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 11px;")

        k_col = QVBoxLayout()
        k_col.addWidget(self._k_oyuncu_lb)
        k_col.addWidget(self._k_skor_lb)

        b_col = QVBoxLayout()
        b_col.addWidget(self._b_oyuncu_lb)
        b_col.addWidget(self._b_skor_lb)

        skor_lay.addLayout(k_col)
        skor_lay.addWidget(vs_lb)
        skor_lay.addLayout(b_col)

        layout.addWidget(skor_frame)

        # TUR BİLGİSİ
        self._tur_bilgi_lb = QLabel("Oyun başlamaya hazır.")
        self._tur_bilgi_lb.setAlignment(Qt.AlignCenter)
        self._tur_bilgi_lb.setWordWrap(True)
        self._tur_bilgi_lb.setStyleSheet(
            f"font-size: 13px; color: {RENKLER['text_secondary']}; "
            f"background: {RENKLER['bg_card']}; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(self._tur_bilgi_lb)

        # BRANŞ GÖSTERGESİ
        self._brans_lb = QLabel("")
        self._brans_lb.setAlignment(Qt.AlignCenter)
        self._brans_lb.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(self._brans_lb)

        # KARŞILAŞTIRMA SONUÇLARI
        self._karsilastirma_box = QGroupBox("Son Tur Sonucu")
        self._karsilastirma_box.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px; font-weight: bold; color: {RENKLER['text_secondary']};
                border: 1px solid {RENKLER['bg_panel']}; border-radius: 8px; padding-top: 10px;
            }}
        """)
        karsi_lay = QVBoxLayout(self._karsilastirma_box)
        self._karsi_text = QTextEdit()
        self._karsi_text.setReadOnly(True)
        self._karsi_text.setFixedHeight(160)
        self._karsi_text.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: #DDD; font-size: 11px; border: none;"
        )
        karsi_lay.addWidget(self._karsi_text)
        layout.addWidget(self._karsilastirma_box)

        # MORAL GÖSTERGELERİ
        moral_frame = QFrame()
        moral_frame.setStyleSheet(
            f"background: {RENKLER['bg_card']}; border-radius: 8px; padding: 6px;"
        )
        moral_lay = QGridLayout(moral_frame)
        moral_lay.addWidget(QLabel("Moral (Oyuncu):"), 0, 0)
        self._k_moral_bar = QProgressBar()
        self._k_moral_bar.setMaximum(100)
        self._k_moral_bar.setValue(75)
        self._k_moral_bar.setFixedHeight(12)
        self._k_moral_bar.setStyleSheet(
            "QProgressBar::chunk { background: #3498DB; border-radius: 4px; }"
            "QProgressBar { background: #333; border-radius: 4px; }"
        )
        moral_lay.addWidget(self._k_moral_bar, 0, 1)

        moral_lay.addWidget(QLabel("Moral (Bilgisayar):"), 1, 0)
        self._b_moral_bar = QProgressBar()
        self._b_moral_bar.setMaximum(100)
        self._b_moral_bar.setValue(75)
        self._b_moral_bar.setFixedHeight(12)
        self._b_moral_bar.setStyleSheet(
            "QProgressBar::chunk { background: #9B59B6; border-radius: 4px; }"
            "QProgressBar { background: #333; border-radius: 4px; }"
        )
        moral_lay.addWidget(self._b_moral_bar, 1, 1)
        layout.addWidget(moral_frame)

        # LEGEND CHECKBOX (Legend özel yeteneği için)
        self._legend_cb = QCheckBox("Legend Yeteneği Aktif Et (1x Kullanım)")
        self._legend_cb.setStyleSheet("color: #F1C40F; font-size: 11px;")
        self._legend_cb.setVisible(False)
        self._legend_cb.stateChanged.connect(
            lambda s: self.legend_aktif_degisti.emit(s == Qt.Checked)
        )
        layout.addWidget(self._legend_cb)

        # TUR OYNA BUTONU
        self._btn_tur_oyna = QPushButton("▶  TURU OYNA")
        self._btn_tur_oyna.setFixedHeight(50)
        self._btn_tur_oyna.setStyleSheet(f"""
            QPushButton {{
                background-color: {RENKLER['accent']};
                color: white; font-size: 16px; font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{ background-color: #FF6B6B; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
        """)
        self._btn_tur_oyna.clicked.connect(self.tur_oyna_sinyal.emit)
        self._btn_tur_oyna.setEnabled(False)
        layout.addWidget(self._btn_tur_oyna)

        layout.addStretch()

    # --- Güncelleme metotları ---

    def skor_guncelle(self, k_skor: int, b_skor: int):
        self._k_skor_lb.setText(str(k_skor))
        self._b_skor_lb.setText(str(b_skor))

    def moral_guncelle(self, k_moral: int, b_moral: int):
        self._k_moral_bar.setValue(k_moral)
        self._b_moral_bar.setValue(b_moral)

    def tur_bilgisi_guncelle(self, metin: str):
        self._tur_bilgi_lb.setText(metin)

    def brans_guncelle(self, brans: Optional[Brans]):
        if brans:
            ikon = BRANS_IKONLAR.get(brans, "")
            renk = BRANS_RENKLER.get(brans, "#FFF")
            self._brans_lb.setText(f"{ikon} {brans.goster_adi()}")
            self._brans_lb.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {renk};")
        else:
            self._brans_lb.setText("")

    def karsilastirma_goster(self, metin: str):
        self._karsi_text.setText(metin)

    def btn_tur_oyna_aktif(self, aktif: bool):
        self._btn_tur_oyna.setEnabled(aktif)

    def legend_cb_goster(self, goster: bool):
        self._legend_cb.setVisible(goster)

    def legend_cb_sifirla(self):
        self._legend_cb.setChecked(False)
        self._legend_cb.setVisible(False)

    def oyuncu_adi_guncelle(self, k_ad: str, b_ad: str):
        self._k_oyuncu_lb.setText(k_ad)
        self._b_oyuncu_lb.setText(b_ad)


# ---------------------------------------------------------------------------
# OYUN EKRANI (Ana oyun görünümü)
# ---------------------------------------------------------------------------

class OyunEkrani(QWidget):

    oyun_bitti_sinyal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._yonetici: Optional[OyunYonetici] = None
        self._kullanici: Optional[Kullanici] = None
        self._bilgisayar: Optional[Bilgisayar] = None
        self._secilen_kart = None
        self._legend_aktif = False
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(5, 5, 5, 5)
        main_lay.setSpacing(5)

        # Üst bilgi çubuğu
        self._ust_bar = QLabel("Akıllı Sporcu Kart Ligi Simülasyonu")
        self._ust_bar.setAlignment(Qt.AlignCenter)
        self._ust_bar.setStyleSheet(
            f"background: {RENKLER['bg_panel']}; color: {RENKLER['accent']}; "
            f"font-size: 14px; font-weight: bold; padding: 5px; border-radius: 6px;"
        )
        main_lay.addWidget(self._ust_bar)

        # Ana splitter: Sol | Orta | Sağ
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {RENKLER['bg_panel']}; width: 3px; }}")

        # SOL: Kullanıcı kartları
        sol_panel = QWidget()
        sol_lay = QVBoxLayout(sol_panel)
        sol_lay.setContentsMargins(4, 4, 4, 4)

        k_baslik = QLabel("🙋 SENİN KARTLARIN")
        k_baslik.setStyleSheet(
            f"color: {RENKLER['accent']}; font-weight: bold; font-size: 13px; margin-bottom: 4px;"
        )
        sol_lay.addWidget(k_baslik)

        self._kullanici_panel = KartPaneli("", secilecek=True)
        self._kullanici_panel.kart_secildi.connect(self._kullanici_kart_sec)
        sol_lay.addWidget(self._kullanici_panel)

        splitter.addWidget(sol_panel)

        # ORTA: Oyun kontrol paneli
        self._orta_panel = OrtaPanel()
        self._orta_panel.tur_oyna_sinyal.connect(self._tur_oyna)
        self._orta_panel.legend_aktif_degisti.connect(self._legend_degisti)
        self._orta_panel.setMinimumWidth(260)
        splitter.addWidget(self._orta_panel)

        # SAĞ: Bilgisayar kartları
        sag_panel = QWidget()
        sag_lay = QVBoxLayout(sag_panel)
        sag_lay.setContentsMargins(4, 4, 4, 4)

        b_ust = QHBoxLayout()
        b_baslik = QLabel("🤖 BİLGİSAYAR KARTLARI")
        b_baslik.setStyleSheet(
            f"color: {RENKLER['accent2']}; font-weight: bold; font-size: 13px;"
        )
        b_ust.addWidget(b_baslik)

        self._btn_goster = QPushButton("👁 Göster")
        self._btn_goster.setFixedWidth(80)
        self._btn_goster.setStyleSheet(
            f"background: {RENKLER['bg_panel']}; color: white; "
            f"border-radius: 6px; font-size: 11px; padding: 4px;"
        )
        self._btn_goster.clicked.connect(self._bilgisayar_kartlari_toggle)
        b_ust.addWidget(self._btn_goster)
        sag_lay.addLayout(b_ust)

        self._bilgisayar_panel = KartPaneli("", secilecek=False)
        sag_lay.addWidget(self._bilgisayar_panel)

        splitter.addWidget(sag_panel)

        splitter.setSizes([320, 280, 320])
        main_lay.addWidget(splitter)

        # Alt durum çubuğu
        alt_bar = QFrame()
        alt_bar.setStyleSheet(f"background: {RENKLER['bg_card']}; border-radius: 6px;")
        alt_lay = QHBoxLayout(alt_bar)
        alt_lay.setContentsMargins(10, 5, 10, 5)
        self._durum_lb = QLabel("Oyun başlamayı bekliyor...")
        self._durum_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 11px;")
        alt_lay.addWidget(self._durum_lb)

        self._tur_sayisi_lb = QLabel("Tur: 0")
        self._tur_sayisi_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 11px;")
        alt_lay.addWidget(self._tur_sayisi_lb, alignment=Qt.AlignRight)
        main_lay.addWidget(alt_bar)

    # --- Oyun kurulum ---

    def oyun_kur(self, kullanici: Kullanici, bilgisayar: Bilgisayar, yonetici: OyunYonetici):
        self._kullanici = kullanici
        self._bilgisayar = bilgisayar
        self._yonetici = yonetici

        self._orta_panel.oyuncu_adi_guncelle(kullanici.oyuncu_adi, bilgisayar.oyuncu_adi)
        self._tum_guncelle()
        self._sonraki_tur_hazirla()

    def _tum_guncelle(self):
        """Tüm panelleri güncelle"""
        k_kartlar = self._kullanici.get_tum_kartlar()
        b_kartlar = self._bilgisayar.get_tum_kartlar()

        self._kullanici_panel.kartlari_yukle(k_kartlar)
        if self._bilgisayar.kartlar_goster:
            self._bilgisayar_panel.kartlari_yukle(b_kartlar)
        else:
            self._bilgisayar_panel.kartlari_yukle([])

        self._orta_panel.skor_guncelle(self._kullanici.skor, self._bilgisayar.skor)
        self._orta_panel.moral_guncelle(self._kullanici.moral, self._bilgisayar.moral)

    def _sonraki_tur_hazirla(self):
        """Bir sonraki turu hazırla"""
        if self._yonetici.oyun_bitti:
            self._oyun_bitti()
            return

        durum = self._yonetici.tur_baslat()

        if durum["durum"] == "oyun_bitti":
            self._oyun_bitti()
            return

        elif durum["durum"] == "atla":
            self._orta_panel.tur_bilgisi_guncelle(durum["mesaj"])
            self._durum_lb.setText(durum["mesaj"])
            self._tum_guncelle()
            QTimer.singleShot(1200, self._sonraki_tur_hazirla)

        elif durum["durum"].startswith("hukmen_"):
            self._orta_panel.tur_bilgisi_guncelle(durum["mesaj"])
            self._durum_lb.setText(durum["mesaj"])
            kaydi = durum.get("tur_kaydi", {})
            self._orta_panel.karsilastirma_goster(
                f"HÜKMEN GALİBİYET\n{durum['mesaj']}\n\n"
                f"Skor: {kaydi.get('kullanici_skor',0)} - {kaydi.get('bilgisayar_skor',0)}"
            )
            self._tum_guncelle()
            QTimer.singleShot(1500, self._sonraki_tur_hazirla)

        else:  # normal
            brans = durum["brans"]
            self._orta_panel.brans_guncelle(brans)
            self._orta_panel.tur_bilgisi_guncelle(
                f"Tur {self._yonetici.mevcut_tur_no + 1} – {brans.goster_adi()} branşı\n"
                f"Bu branştan bir kart seçin ve 'TURU OYNA' düğmesine tıklayın."
            )
            self._durum_lb.setText(f"Sıradaki branş: {brans.goster_adi()}")
            self._tur_sayisi_lb.setText(f"Tur: {self._yonetici.mevcut_tur_no + 1}")

            # Branş kartlarını filtrele/vurgula
            self._kullanici_panel.filtrele(brans)

            # Legend checkbox: kullanıcının seçtiği kartın Legend özelliği varsa göster
            self._orta_panel.legend_cb_sifirla()
            self._secilen_kart = None
            self._kullanici_panel.secimi_kaldir()
            self._orta_panel.btn_tur_oyna_aktif(False)

    def _kullanici_kart_sec(self, sporcu: Sporcu):
        if not sporcu.oynanabilir_mi():
            return
        self._secilen_kart = sporcu
        # Legend kontrolü
        if sporcu.ozel_yetenek.tur == "Legend" and not sporcu.ozel_yetenek.kullanildi:
            self._orta_panel.legend_cb_goster(True)
        else:
            self._orta_panel.legend_cb_sifirla()

        self._orta_panel.btn_tur_oyna_aktif(True)
        self._durum_lb.setText(f"Seçilen: {sporcu.sporcu_adi} – 'TURU OYNA'ya basın")

    def _legend_degisti(self, aktif: bool):
        self._legend_aktif = aktif

    def _tur_oyna(self):
        if not self._secilen_kart:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir kart seçin!")
            return

        brans = self._yonetici.mevcut_brans()

        # Bilgisayar kart seçimi
        oyun_durumu = {
            "son_3_tur": self._yonetici.son_3_tur_mu(),
            "tur_no": self._yonetici.mevcut_tur_no + 1,
        }
        b_kart = self._bilgisayar.kart_sec(brans, oyun_durumu)
        if not b_kart:
            QMessageBox.information(self, "Bilgi", "Bilgisayarın oynayacak kartı kalmadı.")
            self._sonraki_tur_hazirla()
            return

        # Turu oyna
        sonuc = self._yonetici.tur_oyna(self._secilen_kart, b_kart, self._legend_aktif)

        # Sonucu göster
        self._sonucu_goster(sonuc)
        self._tum_guncelle()
        self._orta_panel.legend_cb_sifirla()
        self._legend_aktif = False
        self._secilen_kart = None

        # Bir sonraki tura hazırlan
        if sonuc.get("oyun_bitti"):
            QTimer.singleShot(1800, self._oyun_bitti)
        else:
            QTimer.singleShot(1500, self._sonraki_tur_hazirla)

    def _sonucu_goster(self, sonuc: dict):
        k = sonuc["kullanici_kart"]
        b = sonuc["bilgisayar_kart"]
        kp = sonuc["kullanici_performans"]
        bp = sonuc["bilgisayar_performans"]
        oz = sonuc["secilen_ozellik"]
        kazanan = sonuc["kazanan"]

        if kazanan == "kullanici":
            kazanan_metin = f"🏆 KAZANAN: {self._kullanici.oyuncu_adi} (+{sonuc['kullanici_puan_kazanildi']} puan)"
            renk = RENKLER["kazanildi"]
        elif kazanan == "bilgisayar":
            kazanan_metin = f"💻 KAZANAN: {self._bilgisayar.oyuncu_adi} (+{sonuc['bilgisayar_puan_kazanildi']} puan)"
            renk = RENKLER["kaybedildi"]
        else:
            kazanan_metin = "🤝 BERABERLIK"
            renk = RENKLER["beraberlik"]

        metin = (
            f"{'─' * 38}\n"
            f"TUR {sonuc['tur_no']}  |  Seçilen Özellik: {oz}\n"
            f"{'─' * 38}\n"
            f"[SEN]  {k.sporcu_adi}\n"
            f"  Temel: {kp['temel_puan']}  Moral: {kp['moral_bonusu']:+}  "
            f"Enerji Ceza: -{kp['enerji_cezasi']}  Sv: {kp['seviye_bonusu']:+}\n"
            f"  Özel: {kp['ozel_yetenek_bonusu']:+}  →  TOPLAM: {kp['final_puan']}\n\n"
            f"[PC]   {b.sporcu_adi}\n"
            f"  Temel: {bp['temel_puan']}  Moral: {bp['moral_bonusu']:+}  "
            f"Enerji Ceza: -{bp['enerji_cezasi']}  Sv: {bp['seviye_bonusu']:+}\n"
            f"  Özel: {bp['ozel_yetenek_bonusu']:+}  →  TOPLAM: {bp['final_puan']}\n\n"
            f"{kazanan_metin}\n"
            f"Skor: {sonuc['kullanici_skor']} – {sonuc['bilgisayar_skor']}\n"
        )

        if sonuc.get("k_seviye_atladi"):
            metin += f"\n⬆ {k.sporcu_adi} seviye atladı! (Sv {k.seviye})"
        if sonuc.get("b_seviye_atladi"):
            metin += f"\n⬆ {b.sporcu_adi} seviye atladı! (Sv {b.seviye})"

        self._orta_panel.karsilastirma_goster(metin)
        self._orta_panel.tur_bilgisi_guncelle(kazanan_metin)
        self._durum_lb.setText(kazanan_metin)

    def _bilgisayar_kartlari_toggle(self):
        self._bilgisayar.kartlar_goster_toggle()
        if self._bilgisayar.kartlar_goster:
            self._btn_goster.setText("🙈 Gizle")
            self._bilgisayar_panel.kartlari_yukle(self._bilgisayar.get_tum_kartlar())
        else:
            self._btn_goster.setText("👁 Göster")
            self._bilgisayar_panel.kartlari_yukle([])

    def _oyun_bitti(self):
        rapor = self._yonetici.tam_rapor()
        self.oyun_bitti_sinyal.emit(rapor)


# ---------------------------------------------------------------------------
# OYUN SONU EKRANI
# ---------------------------------------------------------------------------

class OyunSonuEkrani(QWidget):

    yeni_oyun_sinyal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self._baslik_lb = QLabel("OYUN SONA ERDİ")
        self._baslik_lb.setAlignment(Qt.AlignCenter)
        self._baslik_lb.setStyleSheet(
            f"color: {RENKLER['accent']}; font-size: 26px; font-weight: bold;"
        )
        layout.addWidget(self._baslik_lb)

        self._kazanan_lb = QLabel("")
        self._kazanan_lb.setAlignment(Qt.AlignCenter)
        self._kazanan_lb.setStyleSheet("font-size: 20px; font-weight: bold; color: #F1C40F;")
        layout.addWidget(self._kazanan_lb)

        self._kriter_lb = QLabel("")
        self._kriter_lb.setAlignment(Qt.AlignCenter)
        self._kriter_lb.setStyleSheet(f"font-size: 12px; color: {RENKLER['text_secondary']};")
        layout.addWidget(self._kriter_lb)

        # Tab widget: İstatistikler + Tur Geçmişi
        self._tab = QTabWidget()
        self._tab.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {RENKLER['bg_panel']}; border-radius: 6px; }}
            QTabBar::tab {{ background: {RENKLER['bg_card']}; color: #AAA; padding: 8px 16px; border-radius: 4px; }}
            QTabBar::tab:selected {{ background: {RENKLER['bg_panel']}; color: white; }}
        """)

        # İstatistik tablosu
        istat_widget = QWidget()
        istat_lay = QVBoxLayout(istat_widget)
        self._istat_tablo = QTableWidget(0, 4)
        self._istat_tablo.setHorizontalHeaderLabels(
            ["Kriter", self._oyuncu_adi("Oyuncu"), self._oyuncu_adi("Bilgisayar"), "Fark"]
        )
        self._istat_tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._istat_tablo.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: #DDD; "
            f"gridline-color: {RENKLER['bg_panel']}; font-size: 12px; border: none;"
        )
        self._istat_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        istat_lay.addWidget(self._istat_tablo)
        self._tab.addTab(istat_widget, "📊 İstatistikler")

        # Tur geçmişi
        gecmis_widget = QWidget()
        gecmis_lay = QVBoxLayout(gecmis_widget)
        self._gecmis_text = QTextEdit()
        self._gecmis_text.setReadOnly(True)
        self._gecmis_text.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: #DDD; font-size: 11px; border: none;"
        )
        gecmis_lay.addWidget(self._gecmis_text)
        self._tab.addTab(gecmis_widget, "📜 Tur Geçmişi")

        layout.addWidget(self._tab)

        # Yeni oyun butonu
        btn = QPushButton("🔄  YENİ OYUN")
        btn.setFixedHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {RENKLER['accent']}; color: white;
                font-size: 16px; font-weight: bold; border-radius: 12px;
            }}
            QPushButton:hover {{ background-color: #FF6B6B; }}
        """)
        btn.clicked.connect(self.yeni_oyun_sinyal.emit)
        layout.addWidget(btn)

    def _oyuncu_adi(self, varsayilan: str) -> str:
        return varsayilan

    def raporu_yukle(self, rapor: dict):
        k = rapor["kullanici"]
        b = rapor["bilgisayar"]
        istat = rapor["istatistik"]

        self._kazanan_lb.setText(f"🏆  {rapor['kazanan']}")
        self._kriter_lb.setText(rapor["kriter"])

        # Tablo başlıkları güncelle
        self._istat_tablo.setHorizontalHeaderLabels(
            ["Kriter", k["ad"], b["ad"], "Fark"]
        )

        satirlar = [
            ("Toplam Puan", k["skor"], b["skor"]),
            ("Galibiyet", k["galibiyet"], b["galibiyet"]),
            ("Mağlubiyet", k["maglubiyet"], b["maglubiyet"]),
            ("Beraberlik", k["beraberlik"], b["beraberlik"]),
            ("Öz.Yetenek Gal.", k["ozel_yetenek_galibiyet"], b["ozel_yetenek_galibiyet"]),
            ("Kalan Enerji", k["kalan_enerji"], b["kalan_enerji"]),
            ("Max Sv. Kart", k["max_seviye_kart"], b["max_seviye_kart"]),
            ("Seri Sayısı", k["seri_sayisi"], b["seri_sayisi"]),
            ("Final Moral", k["moral"], b["moral"]),
        ]

        self._istat_tablo.setRowCount(len(satirlar))
        for row, (kriter, kv, bv) in enumerate(satirlar):
            self._istat_tablo.setItem(row, 0, QTableWidgetItem(kriter))
            self._istat_tablo.setItem(row, 1, QTableWidgetItem(str(kv)))
            self._istat_tablo.setItem(row, 2, QTableWidgetItem(str(bv)))
            fark = kv - bv
            fark_item = QTableWidgetItem(f"{fark:+d}" if isinstance(fark, int) else str(fark))
            if isinstance(fark, (int, float)):
                if fark > 0:
                    fark_item.setForeground(QColor(RENKLER["kazanildi"]))
                elif fark < 0:
                    fark_item.setForeground(QColor(RENKLER["kaybedildi"]))
            self._istat_tablo.setItem(row, 3, fark_item)

        # Tur geçmişi
        tur_metni = f"Toplam Oynanan Tur: {istat['toplam_tur']}\n"
        tur_metni += f"Atlanan Tur: {istat['atlanan_tur']}\n\n"
        tur_metni += "=" * 45 + "\n"
        for t in istat["tur_gecmisi"]:
            if t.get("tip") == "normal":
                brans = t["brans"].goster_adi() if hasattr(t.get("brans"), "goster_adi") else str(t.get("brans", ""))
                kaz = t.get("kazanan", "?")
                kaz_metin = "SEN" if kaz == "kullanici" else ("PC" if kaz == "bilgisayar" else "BERABERE")
                tur_metni += (
                    f"Tur {t['tur_no']}: {brans} | {t.get('secilen_ozellik','?')} | "
                    f"{t.get('kullanici_kart','?')} ({t.get('kullanici_final',0)}) vs "
                    f"{t.get('bilgisayar_kart','?')} ({t.get('bilgisayar_final',0)}) → {kaz_metin}\n"
                )
            elif t.get("tip") == "hukmen":
                brans = t["brans"].goster_adi() if hasattr(t.get("brans"), "goster_adi") else str(t.get("brans", ""))
                kaz = t.get("kazanan", "?")
                kaz_metin = "SEN (hükmen)" if kaz == "kullanici" else "PC (hükmen)"
                tur_metni += f"Tur {t['tur_no']}: {brans} | HÜKMEN → {kaz_metin}\n"
        self._gecmis_text.setText(tur_metni)


# ---------------------------------------------------------------------------
# ANA PENCERE
# ---------------------------------------------------------------------------

class AnaWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Akıllı Sporcu Kart Ligi Simülasyonu")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet(STIL_TEMEL)

        self._tum_sporcular = []
        self._veri_hatalari = []
        self._verileri_yukle()

        self._stacked = QStackedWidget()
        self.setCentralWidget(self._stacked)

        # Ekranlar
        self._hosgeldin = HosgeldinEkrani()
        self._oyun_ekrani = OyunEkrani()
        self._sonu_ekrani = OyunSonuEkrani()

        self._stacked.addWidget(self._hosgeldin)   # index 0
        self._stacked.addWidget(self._oyun_ekrani) # index 1
        self._stacked.addWidget(self._sonu_ekrani) # index 2

        # Bağlantılar
        self._hosgeldin.oyun_baslat.connect(self._oyun_baslat)
        self._oyun_ekrani.oyun_bitti_sinyal.connect(self._oyun_bitti)
        self._sonu_ekrani.yeni_oyun_sinyal.connect(self._yeni_oyun)

        self._stacked.setCurrentIndex(0)

        # Veri hataları varsa uyar
        if self._veri_hatalari:
            QTimer.singleShot(200, self._veri_hatasi_goster)

    def _verileri_yukle(self):
        import os
        dosya = os.path.join(os.path.dirname(__file__), "sporcular.csv")
        okuyucu = VeriOkuyucu(dosya)
        self._tum_sporcular = okuyucu.oku()
        self._veri_hatalari = okuyucu.hatalar

    def _veri_hatasi_goster(self):
        if self._veri_hatalari:
            mesaj = "Veri yüklenirken bazı hatalar oluştu:\n\n" + "\n".join(self._veri_hatalari)
            QMessageBox.warning(self, "Veri Hatası", mesaj)
        if len(self._tum_sporcular) < 24:
            QMessageBox.critical(
                self, "Kritik Hata",
                f"Yeterli sporcu verisi yüklenemedi ({len(self._tum_sporcular)}/24).\n"
                "Lütfen 'sporcular.csv' dosyasını kontrol edin.",
            )

    def _oyun_baslat(self, zorluk: str):
        if len(self._tum_sporcular) < 24:
            QMessageBox.critical(self, "Hata", "Yeterli sporcu verisi yok! Oyun başlatılamıyor.")
            return

        strateji = strateji_olustur(zorluk)
        kullanici = Kullanici(1, "Oyuncu")
        bilgisayar = Bilgisayar(strateji, 2, f"Bilgisayar ({zorluk})")

        yonetici = OyunYonetici()
        yonetici.oyunu_kur(kullanici, bilgisayar)
        yonetici.kartlari_dagit(self._tum_sporcular)

        self._oyun_ekrani.oyun_kur(kullanici, bilgisayar, yonetici)
        self._stacked.setCurrentIndex(1)

    def _oyun_bitti(self, rapor: dict):
        self._sonu_ekrani.raporu_yukle(rapor)
        self._stacked.setCurrentIndex(2)

    def _yeni_oyun(self):
        self._stacked.setCurrentIndex(0)
