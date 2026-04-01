# -*- coding: utf-8 -*-
"""
PyQt5 Arayüzü – Akıllı Sporcu Kart Ligi Simülasyonu
Yeni Tasarım v2: Cyberpunk/Spor Karışımı Dark Tema
Premium kart görünümü, branş banner, anlık güncelleme, bug düzeltmeleri
"""
import sys
from typing import Optional, List

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget,
    QFrame, QScrollArea, QGridLayout, QTextEdit, QSplitter,
    QProgressBar, QMessageBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

from models import Sporcu, Brans
from players import Kullanici, Bilgisayar
from strategies import strateji_olustur
from game_engine import VeriOkuyucu, OyunYonetici


# ---------------------------------------------------------------------------
# RENK PALETİ — Cyberpunk / Spor Dark Tema
# ---------------------------------------------------------------------------

RENKLER = {
    # Arka planlar
    "bg_dark":        "#0B0B1A",
    "bg_card":        "#11112B",
    "bg_panel":       "#0A1535",
    "bg_card_hover":  "#181840",
    # Aksan renkler
    "accent":         "#00E5FF",   # neon cyan
    "accent2":        "#FF1E78",   # neon pembe
    "accent3":        "#7C3AED",   # mor
    # Metin
    "text_primary":   "#E8E8FF",
    "text_secondary": "#6B7FC4",
    # Branş renkleri
    "futbol":         "#00FF87",   # neon yeşil
    "basketbol":      "#FF6B35",   # turuncu
    "voleybol":       "#00BFFF",   # mavi
    # Enerji barı
    "enerji_yuksek":  "#00FF87",
    "enerji_orta":    "#FFB800",
    "enerji_dusuk":   "#FF5500",
    "enerji_kritik":  "#FF1E1E",
    # Sonuç
    "kazanildi":      "#00FF87",
    "kaybedildi":     "#FF1E78",
    "beraberlik":     "#7B8ECC",
    # Özel
    "altin":          "#FFD700",
}

BRANS_RENKLER = {
    Brans.FUTBOL:    RENKLER["futbol"],
    Brans.BASKETBOL: RENKLER["basketbol"],
    Brans.VOLEYBOL:  RENKLER["voleybol"],
}

BRANS_IKONLAR = {
    Brans.FUTBOL:    "⚽",
    Brans.BASKETBOL: "🏀",
    Brans.VOLEYBOL:  "🏐",
}

STIL_TEMEL = f"""
QWidget {{
    background-color: {RENKLER["bg_dark"]};
    color: {RENKLER["text_primary"]};
    font-family: "Segoe UI", "Consolas", Arial, sans-serif;
}}
QScrollBar:vertical {{
    background: {RENKLER["bg_card"]};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {RENKLER["bg_panel"]};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ height: 0px; }}
QToolTip {{
    background-color: {RENKLER["bg_panel"]};
    color: {RENKLER["text_primary"]};
    border: 1px solid {RENKLER["accent"]};
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 11px;
}}
"""

# Kart minimum boyutları (sabit değil, esnek)
KART_W = 195
KART_H = 350


# ---------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------

def _stat_renk(val: int) -> str:
    if val >= 80:
        return RENKLER["enerji_yuksek"]
    elif val >= 60:
        return RENKLER["enerji_orta"]
    return RENKLER["enerji_dusuk"]


def _enerji_renk(e: int) -> str:
    if e > 70:
        return RENKLER["enerji_yuksek"]
    elif e >= 40:
        return RENKLER["enerji_orta"]
    elif e >= 20:
        return RENKLER["enerji_dusuk"]
    return RENKLER["enerji_kritik"]


def _ayirici(renk: str) -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"QFrame {{ background: {renk}40; border: none; margin: 0; }}")
    return sep


def _mini_bar_row(ikon: str, val: int, max_val: int, renk: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(4)

    ikon_lb = QLabel(ikon)
    ikon_lb.setFixedWidth(18)
    ikon_lb.setStyleSheet("font-size: 11px; background: transparent; border: none;")
    row.addWidget(ikon_lb)

    bar = QProgressBar()
    bar.setMaximum(max(max_val, 1))
    bar.setValue(min(val, max_val))
    bar.setFixedHeight(10)
    bar.setTextVisible(False)
    bar.setStyleSheet(f"""
        QProgressBar::chunk {{ background: {renk}; border-radius: 4px; }}
        QProgressBar {{ background: #131330; border-radius: 4px; border: none; }}
    """)
    row.addWidget(bar, 1)

    val_lb = QLabel(str(val))
    val_lb.setFixedWidth(28)
    val_lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val_lb.setStyleSheet(f"font-size: 10px; color: {renk}; background: transparent; border: none;")
    row.addWidget(val_lb)

    return row


# ---------------------------------------------------------------------------
# PREMIUM KART WİDGET'I
# ---------------------------------------------------------------------------

class KartWidget(QFrame):
    """
    Premium sporcu kartı:
      - Üst header strip (branş renkli gradient)
      - Image placeholder (PNG entegrasyon için hazır alan)
      - Özellik mini stat barları
      - Enerji ve dayanıklılık barları
      - Özel yetenek badge
    """

    secildi = pyqtSignal(object)   # Sporcu nesnesi

    def __init__(self, sporcu: Sporcu, secilecek: bool = True, parent=None):
        super().__init__(parent)
        self._sporcu = sporcu
        self._secilecek = secilecek
        self._secili = False
        self.setMinimumSize(KART_W, KART_H)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._setStyle()
        self._buildUI()

    # ── Stil ──────────────────────────────────────────────────────────────
    def _setStyle(self):
        br = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        border = RENKLER["accent"] if self._secili else (br + "99")
        self.setStyleSheet(f"""
            KartWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #161632, stop:1 {RENKLER["bg_card"]});
                border: 2px solid {border};
                border-radius: 12px;
            }}
            KartWidget:hover {{
                border: 2px solid {br};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1E48, stop:1 #161632);
            }}
        """)
        cursor = (Qt.PointingHandCursor
                  if self._secilecek and self._sporcu.oynanabilir_mi()
                  else Qt.ArrowCursor)
        self.setCursor(cursor)

    # ── UI İnşaası ────────────────────────────────────────────────────────
    def _buildUI(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        br = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        ikon = BRANS_IKONLAR.get(self._sporcu.brans, "")

        # ── 1. HEADER STRIP ───────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(38)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {br}60, stop:0.55 {br}20, stop:1 transparent);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {br}44;
            }}
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(7, 3, 7, 3)
        h_lay.setSpacing(4)

        ikon_lb = QLabel(ikon)
        ikon_lb.setStyleSheet("font-size: 17px; background: transparent; border: none;")
        h_lay.addWidget(ikon_lb)

        ad_lb = QLabel(self._sporcu.sporcu_adi)
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        ad_lb.setFont(f)
        ad_lb.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        ad_lb.setWordWrap(True)
        h_lay.addWidget(ad_lb, 1)

        stars = "★" * self._sporcu.seviye + "☆" * (3 - self._sporcu.seviye)
        sv_lb = QLabel(stars)
        sv_lb.setStyleSheet(f"color: {RENKLER['altin']}; font-size: 12px; "
                            f"background: transparent; border: none;")
        sv_lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h_lay.addWidget(sv_lb)

        lay.addWidget(header)

        # ── 2. IMAGE PLACEHOLDER ──────────────────────────────────────────
        # Bu alan ileride yapay zeka PNG görsellerini barındıracak.
        img_wrap = QWidget()
        img_wrap.setStyleSheet("background: transparent; border: none;")
        img_wrap_lay = QVBoxLayout(img_wrap)
        img_wrap_lay.setContentsMargins(7, 5, 7, 2)
        img_wrap_lay.setSpacing(0)

        img_frame = QFrame()
        img_frame.setFixedHeight(96)
        img_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #07071A, stop:0.5 #0D0D26, stop:1 #07071A);
                border: 1px dashed {br}70;
                border-radius: 7px;
            }}
        """)
        img_inner = QVBoxLayout(img_frame)
        img_inner.setAlignment(Qt.AlignCenter)
        img_inner.setSpacing(2)

        cam_lb = QLabel("📷")
        cam_lb.setAlignment(Qt.AlignCenter)
        cam_lb.setStyleSheet("font-size: 22px; background: transparent; border: none;")
        img_inner.addWidget(cam_lb)

        res_lb = QLabel("Resim Alanı")
        res_lb.setAlignment(Qt.AlignCenter)
        res_lb.setStyleSheet(f"color: {br}55; font-size: 10px; letter-spacing: 1px; "
                             f"background: transparent; border: none;")
        img_inner.addWidget(res_lb)

        img_wrap_lay.addWidget(img_frame)
        lay.addWidget(img_wrap)

        # ── 3. TAKIM ADI ──────────────────────────────────────────────────
        takim_lb = QLabel(f"🏟 {self._sporcu.sporcu_takim}")
        takim_lb.setAlignment(Qt.AlignCenter)
        takim_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 10px; "
                               f"background: transparent; margin: 1px 0;")
        lay.addWidget(takim_lb)

        # ── 4. STAT MINI BARLAR ───────────────────────────────────────────
        lay.addWidget(_ayirici(br))

        stats_w = QWidget()
        stats_w.setStyleSheet("background: transparent; border: none;")
        stats_lay = QVBoxLayout(stats_w)
        stats_lay.setContentsMargins(7, 3, 7, 3)
        stats_lay.setSpacing(3)

        ozellikler = self._sporcu.get_ozellikler()
        for oz_ad, oz_val in ozellikler.items():
            row = QHBoxLayout()
            row.setSpacing(4)

            # 6 karakter kısaltma
            kisa = oz_ad[:6]
            lbl = QLabel(kisa)
            lbl.setFixedWidth(38)
            lbl.setStyleSheet("font-size: 10px; color: #9999BB; background: transparent;")
            row.addWidget(lbl)

            mini = QProgressBar()
            mini.setMaximum(100)
            mini.setValue(min(oz_val, 100))
            mini.setFixedHeight(8)
            mini.setTextVisible(False)
            sc = _stat_renk(oz_val)
            mini.setStyleSheet(f"""
                QProgressBar::chunk {{ background: {sc}; border-radius: 3px; }}
                QProgressBar {{ background: #131330; border-radius: 3px; border: none; }}
            """)
            row.addWidget(mini, 1)

            val_lb = QLabel(str(oz_val))
            val_lb.setFixedWidth(24)
            val_lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lb.setStyleSheet(f"font-size: 10px; color: {sc}; font-weight: bold; "
                                 f"background: transparent;")
            row.addWidget(val_lb)

            stats_lay.addLayout(row)

        lay.addWidget(stats_w)

        # ── 5. ENERJİ & DAYANIKLILIK BARLARI ─────────────────────────────
        lay.addWidget(_ayirici(br))

        bars_w = QWidget()
        bars_w.setStyleSheet("background: transparent; border: none;")
        bars_lay = QVBoxLayout(bars_w)
        bars_lay.setContentsMargins(7, 4, 7, 4)
        bars_lay.setSpacing(4)

        e_renk = _enerji_renk(self._sporcu.enerji)
        bars_lay.addLayout(
            _mini_bar_row("⚡", self._sporcu.enerji, self._sporcu.max_enerji, e_renk)
        )
        bars_lay.addLayout(
            _mini_bar_row("💪", self._sporcu.dayaniklilik, 100, "#4488FF")
        )

        lay.addWidget(bars_w)

        # ── 6. ÖZEL YETENEk BADGE ─────────────────────────────────────────
        ozy = self._sporcu.ozel_yetenek
        ozy_frame = QFrame()
        ozy_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(241,196,15, 0.11);
                border-top: 1px solid #F1C40F33;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)
        ozy_inner = QHBoxLayout(ozy_frame)
        ozy_inner.setContentsMargins(7, 3, 7, 3)

        ozy_lb = QLabel(f"✨ {ozy.ad}")
        ozy_lb.setStyleSheet("color: #F1C40F; font-size: 10px; font-weight: bold; "
                             "background: transparent; border: none;")
        ozy_lb.setToolTip(ozy.aciklama)
        ozy_inner.addWidget(ozy_lb, 1)

        xp_lb = QLabel(f"XP:{self._sporcu.deneyim_puani}")
        xp_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 10px; "
                            f"background: transparent; border: none;")
        ozy_inner.addWidget(xp_lb)

        lay.addWidget(ozy_frame)

        # ── 7. OVERLAY'LER ────────────────────────────────────────────────
        if not self._sporcu.oynanabilir_mi():
            used_lb = QLabel("KULLANILDI")
            used_lb.setAlignment(Qt.AlignCenter)
            used_lb.setStyleSheet(
                f"color: {RENKLER['kaybedildi']}; font-weight: bold; font-size: 12px; "
                f"background: rgba(0,0,0,0.60); border: none; border-radius: 5px; "
                f"margin: 2px 7px; padding: 3px;"
            )
            # Header'dan hemen sonraya ekle
            lay.insertWidget(1, used_lb)
        elif self._sporcu.kritik_enerji_mi():
            kritik_lb = QLabel("⚠ KRİTİK ENERJİ")
            kritik_lb.setAlignment(Qt.AlignCenter)
            kritik_lb.setStyleSheet(
                f"color: {RENKLER['enerji_kritik']}; font-size: 10px; font-weight: bold; "
                f"background: rgba(255,30,30,0.15); border: none; border-radius: 3px; "
                f"margin: 0 7px 2px 7px; padding: 2px;"
            )
            # Stat barların üstüne ekle
            lay.insertWidget(lay.count() - 1, kritik_lb)

    # ── Güncelleme (Bug Fix: setParent(None) ile anlık kaldırma) ──────────
    def guncelle(self):
        """Sporcu durumu değiştiğinde kartı yeniden render et."""
        self._setStyle()
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().setParent(None)   # deleteLater() yerine anlık kaldırma
        self._buildUI()

    # ── Seçim durumu ──────────────────────────────────────────────────────
    def sec(self):
        self._secili = True
        br = BRANS_RENKLER.get(self._sporcu.brans, "#888")
        self.setStyleSheet(f"""
            KartWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #262660, stop:1 #1A1A48);
                border: 3px solid {RENKLER['accent']};
                border-radius: 12px;
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
# BRANŞ GÖSTERGESİ — Sıradaki branşı büyük ve çarpıcı gösterir
# ---------------------------------------------------------------------------

class BransGostergesi(QFrame):
    """
    Büyük ve belirgin branş göstergesi.
    Kart seçmeden önce ekranın üst kısmında mevcut branşı gösterir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(95)
        self._build()
        self._brans_gizle()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {RENKLER["bg_panel"]};
                border: 1px solid {RENKLER["accent"]}44;
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(3)
        lay.setAlignment(Qt.AlignCenter)

        # Küçük etiket
        self._etiket = QLabel("SIRASIYLA BRANŞ")
        self._etiket.setAlignment(Qt.AlignCenter)
        self._etiket.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 11px; "
            f"letter-spacing: 2px; background: transparent; border: none;"
        )
        lay.addWidget(self._etiket)

        # Büyük branş etiketi (ikon + ad)
        self._ana_lb = QLabel("")
        self._ana_lb.setAlignment(Qt.AlignCenter)
        f = QFont("Segoe UI", 23)
        f.setBold(True)
        self._ana_lb.setFont(f)
        self._ana_lb.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._ana_lb)

        # Alt açıklama
        self._alt_lb = QLabel("")
        self._alt_lb.setAlignment(Qt.AlignCenter)
        self._alt_lb.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(self._alt_lb)

    def guncelle(self, brans: Optional[Brans], tur_no: int = 0):
        if brans is None:
            self._brans_gizle()
            return

        renk = BRANS_RENKLER.get(brans, "#FFF")
        ikon = BRANS_IKONLAR.get(brans, "")
        ad = brans.goster_adi().upper()

        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {renk}22, stop:0.5 {renk}10, stop:1 {renk}22);
                border: 2px solid {renk}66;
                border-radius: 12px;
            }}
        """)
        self._ana_lb.setText(f"{ikon}  {ad}")
        self._ana_lb.setStyleSheet(
            f"color: {renk}; background: transparent; border: none; "
            f"text-shadow: 0 0 20px {renk};"
        )
        self._etiket.setText(f"TUR {tur_no}  ·  BRANŞ SEÇİMİ")
        self._alt_lb.setText("Aşağıdan kartınızı seçin ve turu oynayın")
        self.show()

    def _brans_gizle(self):
        self._ana_lb.setText("—")
        self._ana_lb.setStyleSheet(f"color: {RENKLER['text_secondary']}; "
                                   f"background: transparent; border: none;")
        self._etiket.setText("BRANŞ BEKLENİYOR")
        self._alt_lb.setText("")
        self.setStyleSheet(f"""
            QFrame {{
                background: {RENKLER["bg_panel"]};
                border: 1px solid {RENKLER["accent"]}22;
                border-radius: 12px;
            }}
        """)


# ---------------------------------------------------------------------------
# KART PANELİ — Scroll edilebilir kart grid'i
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
        self.setStyleSheet(
            f"background-color: {RENKLER['bg_dark']}; border: none;"
        )

        container = QWidget()
        vlay = QVBoxLayout(container)
        vlay.setAlignment(Qt.AlignTop)
        vlay.setSpacing(6)
        vlay.setContentsMargins(4, 4, 4, 4)

        self._baslik_lb = QLabel(baslik)
        self._baslik_lb.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {RENKLER['accent']}; "
            f"margin-bottom: 4px; background: transparent;"
        )
        vlay.addWidget(self._baslik_lb)

        self._grid = QGridLayout()
        self._grid.setSpacing(8)
        vlay.addLayout(self._grid)

        self.setWidget(container)

    def kartlari_yukle(self, sporcular: List[Sporcu]):
        """
        Tüm kart widget'larını temizle ve yeniden yükle.
        Bug Fix: setParent(None) ile widget'lar anlık kaldırılır
        (eski deleteLater() gecikmeye neden oluyordu).
        """
        self._kart_widgetlari.clear()
        self._secili_widget = None

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)   # anlık kaldırma

        for idx, sporcu in enumerate(sporcular):
            kw = KartWidget(sporcu, secilecek=self._secilecek)
            kw.secildi.connect(self._kart_sec)
            self._kart_widgetlari.append(kw)
            self._grid.addWidget(kw, idx // 2, idx % 2)

    def _kart_sec(self, sporcu: Sporcu):
        if self._secili_widget:
            self._secili_widget.sec_kaldir()
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
        """Mevcut kart widget'larını yeniden render et."""
        for kw in self._kart_widgetlari:
            kw.guncelle()

    def baslik_guncelle(self, yeni_baslik: str):
        self._baslik_lb.setText(yeni_baslik)

    def filtrele(self, brans: Optional[Brans]):
        """Belirli branştaki kartları aktif et, diğerlerini pasif yap."""
        for kw in self._kart_widgetlari:
            if brans is None or kw.sporcu.brans == brans:
                kw.setEnabled(True)
                kw.setStyleSheet(kw.styleSheet())
            else:
                kw.setEnabled(False)


# ---------------------------------------------------------------------------
# ORTA PANEL — Skor, branş, karşılaştırma, moral, tur oyna
# ---------------------------------------------------------------------------

class OrtaPanel(QWidget):
    tur_oyna_sinyal = pyqtSignal()
    legend_aktif_degisti = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(8, 8, 8, 8)

        # ── SKOR TABLOSU ──────────────────────────────────────────────────
        skor_frame = QFrame()
        skor_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {RENKLER["bg_panel"]}, stop:1 #081028);
                border: 1px solid {RENKLER["accent"]}33;
                border-radius: 12px;
                padding: 6px;
            }}
        """)
        skor_outer = QVBoxLayout(skor_frame)
        skor_outer.setSpacing(2)
        skor_outer.setContentsMargins(8, 8, 8, 8)

        skor_row = QHBoxLayout()
        skor_row.setSpacing(8)

        self._k_skor_lb = QLabel("0")
        self._k_skor_lb.setStyleSheet(
            f"font-size: 36px; font-weight: bold; color: {RENKLER['accent']}; "
            f"background: transparent; border: none;"
        )
        self._k_skor_lb.setAlignment(Qt.AlignCenter)

        vs_lb = QLabel("VS")
        vs_lb.setStyleSheet(
            f"font-size: 15px; color: {RENKLER['text_secondary']}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        vs_lb.setAlignment(Qt.AlignCenter)

        self._b_skor_lb = QLabel("0")
        self._b_skor_lb.setStyleSheet(
            f"font-size: 36px; font-weight: bold; color: {RENKLER['accent2']}; "
            f"background: transparent; border: none;"
        )
        self._b_skor_lb.setAlignment(Qt.AlignCenter)

        skor_row.addWidget(self._k_skor_lb, 1)
        skor_row.addWidget(vs_lb)
        skor_row.addWidget(self._b_skor_lb, 1)
        skor_outer.addLayout(skor_row)

        isim_row = QHBoxLayout()
        self._k_oyuncu_lb = QLabel("Oyuncu")
        self._k_oyuncu_lb.setAlignment(Qt.AlignCenter)
        self._k_oyuncu_lb.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 12px; background: transparent; border: none;"
        )
        self._b_oyuncu_lb = QLabel("Bilgisayar")
        self._b_oyuncu_lb.setAlignment(Qt.AlignCenter)
        self._b_oyuncu_lb.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 12px; background: transparent; border: none;"
        )
        isim_row.addWidget(self._k_oyuncu_lb, 1)
        isim_row.addStretch()
        isim_row.addWidget(self._b_oyuncu_lb, 1)
        skor_outer.addLayout(isim_row)

        lay.addWidget(skor_frame)

        # ── BRANŞ GÖSTERGESİ (Büyük, belirgin) ───────────────────────────
        self._brans_gostergesi = BransGostergesi()
        lay.addWidget(self._brans_gostergesi)

        # ── TUR BİLGİSİ ───────────────────────────────────────────────────
        self._tur_bilgi_lb = QLabel("Oyun başlamaya hazır.")
        self._tur_bilgi_lb.setAlignment(Qt.AlignCenter)
        self._tur_bilgi_lb.setWordWrap(True)
        self._tur_bilgi_lb.setStyleSheet(
            f"font-size: 13px; color: {RENKLER['text_secondary']}; "
            f"background: {RENKLER['bg_card']}; border: 1px solid {RENKLER['accent']}22; "
            f"border-radius: 8px; padding: 7px;"
        )
        lay.addWidget(self._tur_bilgi_lb)

        # ── KARŞILAŞTIRMA SONUÇLARI ───────────────────────────────────────
        karsi_box = QGroupBox("Son Tur Sonucu")
        karsi_box.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px; font-weight: bold; color: {RENKLER['text_secondary']};
                border: 1px solid {RENKLER['accent']}33; border-radius: 8px;
                margin-top: 6px; padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        """)
        karsi_lay = QVBoxLayout(karsi_box)
        karsi_lay.setContentsMargins(4, 4, 4, 4)

        self._karsi_text = QTextEdit()
        self._karsi_text.setReadOnly(True)
        self._karsi_text.setMinimumHeight(145)
        self._karsi_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._karsi_text.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: #CCCCEE; "
            f"font-size: 12px; border: none; font-family: Consolas, monospace;"
        )
        karsi_lay.addWidget(self._karsi_text)
        lay.addWidget(karsi_box)

        # ── MORAL BARLAR ──────────────────────────────────────────────────
        moral_frame = QFrame()
        moral_frame.setStyleSheet(
            f"background: {RENKLER['bg_card']}; border: 1px solid {RENKLER['accent']}22; "
            f"border-radius: 8px;"
        )
        moral_g = QGridLayout(moral_frame)
        moral_g.setContentsMargins(10, 6, 10, 6)
        moral_g.setSpacing(4)

        self._k_moral_bar = self._make_moral_bar("#00E5FF")
        self._b_moral_bar = self._make_moral_bar("#FF1E78")

        moral_g.addWidget(QLabel("💙 Moral:"), 0, 0)
        moral_g.addWidget(self._k_moral_bar, 0, 1)
        moral_g.addWidget(QLabel("❤ Moral:"), 1, 0)
        moral_g.addWidget(self._b_moral_bar, 1, 1)

        for lbl in moral_frame.findChildren(QLabel):
            lbl.setStyleSheet(f"color: {RENKLER['text_secondary']}; font-size: 12px; "
                              f"background: transparent;")
        lay.addWidget(moral_frame)

        # ── LEGEND CHECKBOX ───────────────────────────────────────────────
        self._legend_cb = QCheckBox("⚡ Legend Yeteneği Aktif Et (1× Kullanım)")
        self._legend_cb.setStyleSheet(
            f"color: {RENKLER['altin']}; font-size: 12px; background: transparent;"
        )
        self._legend_cb.setVisible(False)
        self._legend_cb.stateChanged.connect(
            lambda s: self.legend_aktif_degisti.emit(s == Qt.Checked)
        )
        lay.addWidget(self._legend_cb)

        # ── TUR OYNA BUTONU ───────────────────────────────────────────────
        self._btn_tur = QPushButton("▶  TURU OYNA")
        self._btn_tur.setFixedHeight(50)
        self._btn_tur.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {RENKLER["accent2"]}, stop:1 {RENKLER["accent3"]});
                color: white; font-size: 16px; font-weight: bold;
                border-radius: 12px; border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF4499, stop:1 #9B50FF);
            }}
            QPushButton:disabled {{
                background: #2A2A44; color: #555577; border: none;
            }}
        """)
        self._btn_tur.clicked.connect(self.tur_oyna_sinyal.emit)
        self._btn_tur.setEnabled(False)
        lay.addWidget(self._btn_tur)

        lay.addStretch()

    # ── Yardımcı ──────────────────────────────────────────────────────────
    @staticmethod
    def _make_moral_bar(renk: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setMaximum(100)
        bar.setValue(75)
        bar.setFixedHeight(10)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar::chunk {{ background: {renk}; border-radius: 4px; }}
            QProgressBar {{ background: #1A1A35; border-radius: 4px; border: none; }}
        """)
        return bar

    # ── Güncelleme ────────────────────────────────────────────────────────
    def skor_guncelle(self, k_skor: int, b_skor: int):
        self._k_skor_lb.setText(str(k_skor))
        self._b_skor_lb.setText(str(b_skor))

    def moral_guncelle(self, k_moral: int, b_moral: int):
        self._k_moral_bar.setValue(k_moral)
        self._b_moral_bar.setValue(b_moral)

    def tur_bilgisi_guncelle(self, metin: str):
        self._tur_bilgi_lb.setText(metin)

    def brans_guncelle(self, brans: Optional[Brans], tur_no: int = 0):
        self._brans_gostergesi.guncelle(brans, tur_no)

    def karsilastirma_goster(self, metin: str):
        self._karsi_text.setText(metin)

    def btn_tur_oyna_aktif(self, aktif: bool):
        self._btn_tur.setEnabled(aktif)

    def legend_cb_goster(self, goster: bool):
        self._legend_cb.setVisible(goster)

    def legend_cb_sifirla(self):
        self._legend_cb.setChecked(False)
        self._legend_cb.setVisible(False)

    def oyuncu_adi_guncelle(self, k_ad: str, b_ad: str):
        self._k_oyuncu_lb.setText(k_ad)
        self._b_oyuncu_lb.setText(b_ad)


# ---------------------------------------------------------------------------
# HOŞGELDİN EKRANI
# ---------------------------------------------------------------------------

class HosgeldinEkrani(QWidget):
    oyun_baslat = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(18)
        lay.setContentsMargins(40, 40, 40, 40)

        # ── Başlık ────────────────────────────────────────────────────────
        baslik = QLabel("AKILLI SPORCU\nKART LİGİ")
        baslik.setAlignment(Qt.AlignCenter)
        f = QFont("Segoe UI", 30)
        f.setBold(True)
        baslik.setFont(f)
        baslik.setStyleSheet(
            f"color: {RENKLER['accent']}; "
            f"background: transparent; border: none; line-height: 1.2;"
        )
        lay.addWidget(baslik)

        alt = QLabel("SİMÜLASYON  v2.0")
        alt.setAlignment(Qt.AlignCenter)
        alt.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 13px; "
            f"letter-spacing: 4px; background: transparent; border: none;"
        )
        lay.addWidget(alt)

        # ── Ayırıcı ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {RENKLER['accent']}44; border: none; margin: 10px 80px;")
        lay.addWidget(sep)

        # ── Zorluk seçimi ─────────────────────────────────────────────────
        zorluk_lb = QLabel("ZORLUK SEVİYESİ SEÇİN")
        zorluk_lb.setAlignment(Qt.AlignCenter)
        zorluk_lb.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 13px; "
            f"letter-spacing: 3px; background: transparent; border: none;"
        )
        lay.addWidget(zorluk_lb)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(28)

        self._btn_kolay = self._make_btn("⚡  KOLAY", RENKLER["futbol"], "#00AA55")
        self._btn_orta = self._make_btn("🔥  ORTA", RENKLER["basketbol"], "#CC4400")

        self._btn_kolay.clicked.connect(lambda: self.oyun_baslat.emit("Kolay"))
        self._btn_orta.clicked.connect(lambda: self.oyun_baslat.emit("Orta"))

        btn_row.addWidget(self._btn_kolay)
        btn_row.addWidget(self._btn_orta)
        lay.addLayout(btn_row)

        # ── Bilgi metni ───────────────────────────────────────────────────
        bilgi_frame = QFrame()
        bilgi_frame.setStyleSheet(
            f"background: {RENKLER['bg_card']}; border: 1px solid {RENKLER['accent']}22; "
            f"border-radius: 12px;"
        )
        bilgi_lay = QVBoxLayout(bilgi_frame)
        bilgi_lay.setContentsMargins(20, 14, 20, 14)

        bilgi_metni = (
            f"<center>"
            f"<span style='color:{RENKLER['futbol']}; font-size:14px;'>⚽ Futbolcu</span>"
            f"  &nbsp;  "
            f"<span style='color:{RENKLER['basketbol']}; font-size:14px;'>🏀 Basketbolcu</span>"
            f"  &nbsp;  "
            f"<span style='color:{RENKLER['voleybol']}; font-size:14px;'>🏐 Voleybolcu</span>"
            f"<br><br>"
            f"<span style='color:{RENKLER['text_secondary']}; font-size:11px;'>"
            f"Her oyuncuya 12 kart dağıtılır &nbsp;·&nbsp; "
            f"Tur sırası: Futbol → Basketbol → Voleybol → ...<br>"
            f"Enerji, moral ve özel yetenekler belirleyici rol oynar."
            f"</span></center>"
        )
        bilgi_lb = QLabel(bilgi_metni)
        bilgi_lb.setWordWrap(True)
        bilgi_lb.setStyleSheet("background: transparent; border: none;")
        bilgi_lay.addWidget(bilgi_lb)

        lay.addWidget(bilgi_frame)

    @staticmethod
    def _make_btn(metin: str, renk: str, hover_renk: str) -> QPushButton:
        btn = QPushButton(metin)
        btn.setMinimumSize(170, 58)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {renk}CC, stop:1 {renk}88);
                color: #0B0B1A; font-size: 16px; font-weight: bold;
                border-radius: 14px; border: 2px solid {renk};
            }}
            QPushButton:hover {{
                background: {renk};
                color: #0B0B1A;
                border-color: white;
            }}
            QPushButton:pressed {{
                background: {hover_renk};
            }}
        """)
        return btn


# ---------------------------------------------------------------------------
# OYUN EKRANI
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
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(5)

        # ── Üst bar ───────────────────────────────────────────────────────
        self._ust_bar = QLabel("⚡  Akıllı Sporcu Kart Ligi Simülasyonu")
        self._ust_bar.setAlignment(Qt.AlignCenter)
        self._ust_bar.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {RENKLER['bg_panel']}, stop:0.5 #0E1A3A, stop:1 {RENKLER['bg_panel']}); "
            f"color: {RENKLER['accent']}; font-size: 14px; font-weight: bold; "
            f"padding: 7px; border-radius: 8px; "
            f"border: 1px solid {RENKLER['accent']}33;"
        )
        lay.addWidget(self._ust_bar)

        # ── Splitter: Sol | Orta | Sağ ────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {RENKLER['bg_panel']}; width: 3px; }}"
        )

        # Sol: Kullanıcı kartları
        sol = QWidget()
        sol.setMinimumWidth(360)
        sol_lay = QVBoxLayout(sol)
        sol_lay.setContentsMargins(4, 4, 4, 4)
        sol_lay.setSpacing(6)

        k_baslik = QLabel("🙋  SENİN KARTLARIN")
        k_baslik.setStyleSheet(
            f"color: {RENKLER['accent']}; font-weight: bold; font-size: 14px; "
            f"background: transparent; margin-bottom: 2px;"
        )
        sol_lay.addWidget(k_baslik)

        self._kullanici_panel = KartPaneli("", secilecek=True)
        self._kullanici_panel.kart_secildi.connect(self._kullanici_kart_sec)
        sol_lay.addWidget(self._kullanici_panel)
        splitter.addWidget(sol)

        # Orta: Oyun kontrol
        self._orta_panel = OrtaPanel()
        self._orta_panel.tur_oyna_sinyal.connect(self._tur_oyna)
        self._orta_panel.legend_aktif_degisti.connect(self._legend_degisti)
        self._orta_panel.setMinimumWidth(275)
        splitter.addWidget(self._orta_panel)

        # Sağ: Bilgisayar kartları
        sag = QWidget()
        sag.setMinimumWidth(360)
        sag_lay = QVBoxLayout(sag)
        sag_lay.setContentsMargins(4, 4, 4, 4)
        sag_lay.setSpacing(6)

        b_ust = QHBoxLayout()
        b_baslik = QLabel("🤖  BİLGİSAYAR KARTLARI")
        b_baslik.setStyleSheet(
            f"color: {RENKLER['accent2']}; font-weight: bold; font-size: 14px; background: transparent;"
        )
        b_ust.addWidget(b_baslik, 1)

        self._btn_goster = QPushButton("👁 Göster")
        self._btn_goster.setFixedWidth(90)
        self._btn_goster.setStyleSheet(
            f"background: {RENKLER['bg_panel']}; color: {RENKLER['text_secondary']}; "
            f"border: 1px solid {RENKLER['accent']}44; border-radius: 6px; "
            f"font-size: 12px; padding: 4px 8px;"
        )
        self._btn_goster.clicked.connect(self._bilgisayar_kartlari_toggle)
        b_ust.addWidget(self._btn_goster)
        sag_lay.addLayout(b_ust)

        self._bilgisayar_panel = KartPaneli("", secilecek=False)
        sag_lay.addWidget(self._bilgisayar_panel)
        splitter.addWidget(sag)

        splitter.setSizes([400, 300, 400])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        lay.addWidget(splitter, 1)

        # ── Alt durum çubuğu ──────────────────────────────────────────────
        alt_bar = QFrame()
        alt_bar.setStyleSheet(
            f"background: {RENKLER['bg_card']}; border: 1px solid {RENKLER['accent']}18; "
            f"border-radius: 6px;"
        )
        alt_lay = QHBoxLayout(alt_bar)
        alt_lay.setContentsMargins(10, 4, 10, 4)

        self._durum_lb = QLabel("Oyun başlamayı bekliyor...")
        self._durum_lb.setStyleSheet(
            f"color: {RENKLER['text_secondary']}; font-size: 12px; background: transparent;"
        )
        alt_lay.addWidget(self._durum_lb, 1)

        self._tur_sayisi_lb = QLabel("Tur: —")
        self._tur_sayisi_lb.setStyleSheet(
            f"color: {RENKLER['accent']}; font-size: 12px; background: transparent;"
        )
        alt_lay.addWidget(self._tur_sayisi_lb, alignment=Qt.AlignRight)
        lay.addWidget(alt_bar)

    # ── Oyun kurulum ──────────────────────────────────────────────────────

    def oyun_kur(self, kullanici: Kullanici, bilgisayar: Bilgisayar, yonetici: OyunYonetici):
        self._kullanici = kullanici
        self._bilgisayar = bilgisayar
        self._yonetici = yonetici
        self._secilen_kart = None
        self._legend_aktif = False

        self._orta_panel.oyuncu_adi_guncelle(kullanici.oyuncu_adi, bilgisayar.oyuncu_adi)
        self._orta_panel.karsilastirma_goster("")
        self._orta_panel.tur_bilgisi_guncelle("Hazır — kart seçin")
        self._tum_guncelle()
        self._sonraki_tur_hazirla()

    def _tum_guncelle(self):
        """Tüm panelleri anlık güncelle."""
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
        if self._yonetici.oyun_bitti:
            self._oyun_bitti()
            return

        durum = self._yonetici.tur_baslat()

        if durum["durum"] == "oyun_bitti":
            self._oyun_bitti()
            return

        elif durum["durum"] == "atla":
            self._orta_panel.tur_bilgisi_guncelle(durum["mesaj"])
            self._orta_panel.brans_guncelle(None)
            self._durum_lb.setText(durum["mesaj"])
            self._tum_guncelle()
            QTimer.singleShot(1200, self._sonraki_tur_hazirla)

        elif durum["durum"].startswith("hukmen_"):
            self._orta_panel.tur_bilgisi_guncelle(durum["mesaj"])
            self._durum_lb.setText(durum["mesaj"])
            kaydi = durum.get("tur_kaydi", {})
            self._orta_panel.karsilastirma_goster(
                f"HÜKMEN GALİBİYET\n{durum['mesaj']}\n\n"
                f"Skor: {kaydi.get('kullanici_skor', 0)} — {kaydi.get('bilgisayar_skor', 0)}"
            )
            self._tum_guncelle()
            QTimer.singleShot(1500, self._sonraki_tur_hazirla)

        else:  # normal
            brans = durum["brans"]
            kullanici_filtre = durum.get("kullanici_filtre", brans)
            tur_no = self._yonetici.mevcut_tur_no + 1

            self._orta_panel.brans_guncelle(brans, tur_no)
            self._orta_panel.tur_bilgisi_guncelle(durum.get("mesaj", ""))
            self._durum_lb.setText(f"Sıradaki: {brans.goster_adi()}")
            self._tur_sayisi_lb.setText(f"Tur: {tur_no}")

            self._kullanici_panel.filtrele(kullanici_filtre)
            self._orta_panel.legend_cb_sifirla()
            self._secilen_kart = None
            self._kullanici_panel.secimi_kaldir()
            self._orta_panel.btn_tur_oyna_aktif(False)

    def _kullanici_kart_sec(self, sporcu: Sporcu):
        if not sporcu.oynanabilir_mi():
            return
        self._secilen_kart = sporcu
        if sporcu.ozel_yetenek.tur == "Legend" and not sporcu.ozel_yetenek.kullanildi:
            self._orta_panel.legend_cb_goster(True)
        else:
            self._orta_panel.legend_cb_sifirla()
        self._orta_panel.btn_tur_oyna_aktif(True)
        self._durum_lb.setText(f"Seçilen: {sporcu.sporcu_adi} — 'TURU OYNA'ya basın")

    def _legend_degisti(self, aktif: bool):
        self._legend_aktif = aktif

    def _tur_oyna(self):
        if not self._secilen_kart:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir kart seçin!")
            return

        brans = self._yonetici.mevcut_brans()
        oyun_durumu = {
            "son_3_tur": self._yonetici.son_3_tur_mu(),
            "tur_no": self._yonetici.mevcut_tur_no + 1,
        }
        b_kart = self._bilgisayar.kart_sec(brans, oyun_durumu)
        if not b_kart:
            QMessageBox.information(self, "Bilgi", "Bilgisayarın oynayacak kartı kalmadı.")
            self._sonraki_tur_hazirla()
            return

        # Turu oyna (backend enerjileri anlık günceller)
        sonuc = self._yonetici.tur_oyna(self._secilen_kart, b_kart, self._legend_aktif)

        # Sonucu göster ve UI'ı anlık güncelle (Bug Fix: setParent(None) sayesinde anlık)
        self._sonucu_goster(sonuc)
        self._tum_guncelle()

        self._orta_panel.legend_cb_sifirla()
        self._legend_aktif = False
        self._secilen_kart = None

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
            kazanan_metin = (
                f"🏆 KAZANAN: {self._kullanici.oyuncu_adi} "
                f"(+{sonuc['kullanici_puan_kazanildi']} puan)"
            )
        elif kazanan == "bilgisayar":
            kazanan_metin = (
                f"💻 KAZANAN: {self._bilgisayar.oyuncu_adi} "
                f"(+{sonuc['bilgisayar_puan_kazanildi']} puan)"
            )
        else:
            kazanan_metin = "🤝 BERABERLIK"

        metin = (
            f"{'─' * 35}\n"
            f"TUR {sonuc['tur_no']}  ·  Özellik: {oz}\n"
            f"{'─' * 35}\n"
            f"[SEN]  {k.sporcu_adi}\n"
            f"  Temel:{kp['temel_puan']}  Moral:{kp['moral_bonusu']:+}  "
            f"EnerjCeza:-{kp['enerji_cezasi']}  Sv:{kp['seviye_bonusu']:+}\n"
            f"  Özel:{kp['ozel_yetenek_bonusu']:+}  →  TOPLAM: {kp['final_puan']}\n\n"
            f"[PC]   {b.sporcu_adi}\n"
            f"  Temel:{bp['temel_puan']}  Moral:{bp['moral_bonusu']:+}  "
            f"EnerjCeza:-{bp['enerji_cezasi']}  Sv:{bp['seviye_bonusu']:+}\n"
            f"  Özel:{bp['ozel_yetenek_bonusu']:+}  →  TOPLAM: {bp['final_puan']}\n\n"
            f"{kazanan_metin}\n"
            f"Skor: {sonuc['kullanici_skor']} — {sonuc['bilgisayar_skor']}\n"
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
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignTop)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        # Başlık
        self._baslik_lb = QLabel("OYUN SONA ERDİ")
        self._baslik_lb.setAlignment(Qt.AlignCenter)
        f = QFont("Segoe UI", 26)
        f.setBold(True)
        self._baslik_lb.setFont(f)
        self._baslik_lb.setStyleSheet(
            f"color: {RENKLER['accent']}; background: transparent; border: none;"
        )
        lay.addWidget(self._baslik_lb)

        # Kazanan
        self._kazanan_lb = QLabel("")
        self._kazanan_lb.setAlignment(Qt.AlignCenter)
        self._kazanan_lb.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {RENKLER['altin']}; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(self._kazanan_lb)

        # Kriter
        self._kriter_lb = QLabel("")
        self._kriter_lb.setAlignment(Qt.AlignCenter)
        self._kriter_lb.setStyleSheet(
            f"font-size: 14px; color: {RENKLER['text_secondary']}; background: transparent; border: none;"
        )
        lay.addWidget(self._kriter_lb)

        # Tab: İstatistikler + Tur Geçmişi
        self._tab = QTabWidget()
        self._tab.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {RENKLER['accent']}33; border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {RENKLER['bg_card']}; color: {RENKLER['text_secondary']};
                padding: 8px 18px; border-radius: 4px; font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background: {RENKLER['bg_panel']}; color: {RENKLER['text_primary']};
            }}
        """)

        # İstatistik tablosu
        istat_w = QWidget()
        istat_lay = QVBoxLayout(istat_w)
        istat_lay.setContentsMargins(4, 4, 4, 4)

        self._istat_tablo = QTableWidget(0, 4)
        self._istat_tablo.setHorizontalHeaderLabels(["Kriter", "Oyuncu", "Bilgisayar", "Fark"])
        self._istat_tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._istat_tablo.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: {RENKLER['text_primary']}; "
            f"gridline-color: {RENKLER['bg_panel']}; font-size: 13px; border: none;"
        )
        self._istat_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self._istat_tablo.verticalHeader().setVisible(False)
        istat_lay.addWidget(self._istat_tablo)
        self._tab.addTab(istat_w, "📊 İstatistikler")

        # Tur geçmişi
        gecmis_w = QWidget()
        gecmis_lay = QVBoxLayout(gecmis_w)
        gecmis_lay.setContentsMargins(4, 4, 4, 4)
        self._gecmis_text = QTextEdit()
        self._gecmis_text.setReadOnly(True)
        self._gecmis_text.setStyleSheet(
            f"background: {RENKLER['bg_card']}; color: #CCCCEE; "
            f"font-size: 12px; border: none; font-family: Consolas, monospace;"
        )
        gecmis_lay.addWidget(self._gecmis_text)
        self._tab.addTab(gecmis_w, "📜 Tur Geçmişi")

        lay.addWidget(self._tab)

        # Yeni oyun butonu
        btn = QPushButton("🔄  YENİ OYUN")
        btn.setFixedHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {RENKLER["accent2"]}, stop:1 {RENKLER["accent3"]});
                color: white; font-size: 16px; font-weight: bold;
                border-radius: 14px; border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF4499, stop:1 #9B50FF);
            }}
        """)
        btn.clicked.connect(self.yeni_oyun_sinyal.emit)
        lay.addWidget(btn)

    def raporu_yukle(self, rapor: dict):
        k = rapor["kullanici"]
        b = rapor["bilgisayar"]
        istat = rapor["istatistik"]

        self._kazanan_lb.setText(f"🏆  {rapor['kazanan']}")
        self._kriter_lb.setText(rapor["kriter"])

        self._istat_tablo.setHorizontalHeaderLabels(
            ["Kriter", k["ad"], b["ad"], "Fark"]
        )

        satirlar = [
            ("Toplam Puan",      k["skor"],                   b["skor"]),
            ("Galibiyet",        k["galibiyet"],               b["galibiyet"]),
            ("Mağlubiyet",       k["maglubiyet"],              b["maglubiyet"]),
            ("Beraberlik",       k["beraberlik"],              b["beraberlik"]),
            ("Öz.Yetenek Gal.", k["ozel_yetenek_galibiyet"], b["ozel_yetenek_galibiyet"]),
            ("Kalan Enerji",     k["kalan_enerji"],            b["kalan_enerji"]),
            ("Max Sv. Kart",     k["max_seviye_kart"],         b["max_seviye_kart"]),
            ("Seri Sayısı",      k["seri_sayisi"],             b["seri_sayisi"]),
            ("Final Moral",      k["moral"],                   b["moral"]),
        ]

        self._istat_tablo.setRowCount(len(satirlar))
        for row, (kriter, kv, bv) in enumerate(satirlar):
            self._istat_tablo.setItem(row, 0, QTableWidgetItem(kriter))
            self._istat_tablo.setItem(row, 1, QTableWidgetItem(str(kv)))
            self._istat_tablo.setItem(row, 2, QTableWidgetItem(str(bv)))
            fark = kv - bv
            fark_item = QTableWidgetItem(f"{fark:+d}")
            if fark > 0:
                fark_item.setForeground(QColor(RENKLER["kazanildi"]))
            elif fark < 0:
                fark_item.setForeground(QColor(RENKLER["kaybedildi"]))
            else:
                fark_item.setForeground(QColor(RENKLER["beraberlik"]))
            self._istat_tablo.setItem(row, 3, fark_item)

        # Tur geçmişi metni
        metin = (
            f"Toplam Oynanan Tur: {istat['toplam_tur']}\n"
            f"Atlanan Tur:        {istat['atlanan_tur']}\n\n"
            + "=" * 45 + "\n"
        )
        for t in istat["tur_gecmisi"]:
            brans_ad = (t["brans"].goster_adi()
                        if hasattr(t.get("brans"), "goster_adi")
                        else str(t.get("brans", "")))
            if t.get("tip") == "normal":
                kaz = t.get("kazanan", "?")
                kaz_m = "SEN" if kaz == "kullanici" else ("PC" if kaz == "bilgisayar" else "BERABERE")
                metin += (
                    f"Tur {t['tur_no']:>2}: {brans_ad:<10} | {t.get('secilen_ozellik','?'):<18} | "
                    f"{t.get('kullanici_kart','?'):<18}({t.get('kullanici_final',0):>3}) vs "
                    f"{t.get('bilgisayar_kart','?'):<18}({t.get('bilgisayar_final',0):>3}) → {kaz_m}\n"
                )
            elif t.get("tip") == "hukmen":
                kaz = t.get("kazanan", "?")
                kaz_m = "SEN (hükmen)" if kaz == "kullanici" else "PC (hükmen)"
                metin += f"Tur {t['tur_no']:>2}: {brans_ad:<10} | HÜKMEN → {kaz_m}\n"

        self._gecmis_text.setText(metin)


# ---------------------------------------------------------------------------
# ANA PENCERE
# ---------------------------------------------------------------------------

class AnaWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Akıllı Sporcu Kart Ligi Simülasyonu")
        self.setMinimumSize(1100, 760)
        self.resize(1400, 900)
        self.setStyleSheet(STIL_TEMEL)

        self._tum_sporcular = []
        self._veri_hatalari = []
        self._verileri_yukle()

        self._stacked = QStackedWidget()
        self.setCentralWidget(self._stacked)

        self._hosgeldin = HosgeldinEkrani()
        self._oyun_ekrani = OyunEkrani()
        self._sonu_ekrani = OyunSonuEkrani()

        self._stacked.addWidget(self._hosgeldin)    # index 0
        self._stacked.addWidget(self._oyun_ekrani)  # index 1
        self._stacked.addWidget(self._sonu_ekrani)  # index 2

        self._hosgeldin.oyun_baslat.connect(self._oyun_baslat)
        self._oyun_ekrani.oyun_bitti_sinyal.connect(self._oyun_bitti)
        self._sonu_ekrani.yeni_oyun_sinyal.connect(self._yeni_oyun)

        self._stacked.setCurrentIndex(0)

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
        # Bug Fix 1: Her yeni oyunda veriler yeniden yüklenir.
        # Böylece önceki oyunda kullanılmış/enerji düşmüş sporcu nesneleri
        # sıfırdan oluşturulur; eski nesneler bir sonraki oyuna taşınmaz.
        self._verileri_yukle()

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
        # Hoşgeldin ekranına dön; oyun başlatıldığında _verileri_yukle() çağrılır.
        self._stacked.setCurrentIndex(0)
