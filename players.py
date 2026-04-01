# -*- coding: utf-8 -*-
"""
Oyuncu sınıf hiyerarşisi – Oyuncu (Abstract) → Kullanici, Bilgisayar
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Sporcu, Brans
    from strategies import KartSecmeStratejisi


class Oyuncu(ABC):
    """
    Soyut oyuncu sınıfı.
    Encapsulation + Abstraction + Inheritance uygular.
    """

    def __init__(self, oyuncu_id: int, oyuncu_adi: str):
        self._oyuncu_id = oyuncu_id
        self._oyuncu_adi = oyuncu_adi
        self._skor: int = 0
        self._moral: int = 75
        self._kart_listesi: List["Sporcu"] = []
        self._galibiyet_serisi: int = 0
        self._kaybetme_serisi: int = 0
        self._toplam_galibiyet: int = 0
        self._toplam_beraberlik: int = 0
        self._toplam_maglubiyet: int = 0
        self._ozel_yetenek_galibiyet: int = 0
        self._toplam_seri_sayisi: int = 0  # kaç kez seri yapıldı
        self._son_brans_kayiplar: dict = {}  # aynı branşta üst üste kayıp takibi

    # --- Properties (Encapsulation) ---
    @property
    def oyuncu_id(self) -> int:
        return self._oyuncu_id

    @property
    def oyuncu_adi(self) -> str:
        return self._oyuncu_adi

    @property
    def skor(self) -> int:
        return self._skor

    @property
    def moral(self) -> int:
        return self._moral

    @moral.setter
    def moral(self, value: int):
        self._moral = max(0, min(100, value))

    @property
    def kart_listesi(self) -> List["Sporcu"]:
        return self._kart_listesi

    @property
    def galibiyet_serisi(self) -> int:
        return self._galibiyet_serisi

    @property
    def kaybetme_serisi(self) -> int:
        return self._kaybetme_serisi

    @property
    def toplam_galibiyet(self) -> int:
        return self._toplam_galibiyet

    @property
    def toplam_beraberlik(self) -> int:
        return self._toplam_beraberlik

    @property
    def toplam_maglubiyet(self) -> int:
        return self._toplam_maglubiyet

    @property
    def ozel_yetenek_galibiyet(self) -> int:
        return self._ozel_yetenek_galibiyet

    @property
    def toplam_seri_sayisi(self) -> int:
        return self._toplam_seri_sayisi

    # --- Kart yönetimi ---
    def kartlari_al(self, kartlar: List["Sporcu"]):
        self._kart_listesi = list(kartlar)

    def get_brans_kartlari(self, brans: "Brans") -> List["Sporcu"]:
        """Belirli branştaki oynanabilir kartları döndür"""
        return [k for k in self._kart_listesi if k.brans == brans and k.oynanabilir_mi()]

    def get_oynanabilir_kartlar(self) -> List["Sporcu"]:
        return [k for k in self._kart_listesi if k.oynanabilir_mi()]

    def get_tum_kartlar(self) -> List["Sporcu"]:
        return list(self._kart_listesi)

    # --- Skor ve sonuç ---
    def skor_ekle(self, miktar: int):
        self._skor += miktar

    def galibiyet_kaydet(self, ozel_yetenek_ile: bool = False):
        self._toplam_galibiyet += 1
        self._galibiyet_serisi += 1
        self._kaybetme_serisi = 0
        if ozel_yetenek_ile:
            self._ozel_yetenek_galibiyet += 1

    def maglubiyet_kaydet(self, brans: "Brans" = None):
        self._toplam_maglubiyet += 1
        self._kaybetme_serisi += 1
        self._galibiyet_serisi = 0
        if brans:
            self._son_brans_kayiplar[brans] = self._son_brans_kayiplar.get(brans, 0) + 1
        else:
            self._son_brans_kayiplar = {}

    def beraberlik_kaydet(self, brans: "Brans" = None):
        self._toplam_beraberlik += 1
        if brans:
            self._son_brans_kayiplar[brans] = 0  # beraberlikte sıfırla

    def brans_ust_uste_kayip(self, brans: "Brans") -> int:
        return self._son_brans_kayiplar.get(brans, 0)

    def seri_kaydet(self):
        self._toplam_seri_sayisi += 1

    # --- İstatistik yardımcıları ---
    def toplam_kalan_enerji(self) -> int:
        return sum(k.enerji for k in self._kart_listesi if k.oynanabilir_mi())

    def max_seviyeli_kart_sayisi(self) -> int:
        return sum(1 for k in self._kart_listesi if k.seviye == 3)

    def moral_durumu(self) -> str:
        if self._moral >= 80:
            return "Yüksek"
        elif self._moral >= 50:
            return "Normal"
        return "Düşük"

    def moral_guncelle(self, miktar: int):
        self._moral = max(0, min(100, self._moral + miktar))

    def captain_moral_bonusu_uygula(self, brans: "Brans", takim: str, miktar: int = 5):
        """Captain özelliği: aynı branş ve takımdaki kartlara moral bonusu"""
        for kart in self._kart_listesi:
            if kart.brans == brans and kart.sporcu_takim == takim and kart.oynanabilir_mi():
                kart.moral_guncelle(miktar)

    def kartlara_moral_uygula(self, miktar: int):
        """Takım morali değiştiğinde tüm oynanabilir kartların moralini güncelle"""
        for kart in self._kart_listesi:
            if kart.oynanabilir_mi():
                kart.moral_guncelle(miktar)

    # --- Soyut metot ---
    @abstractmethod
    def kart_sec(self, brans: "Brans", oyun_durumu: dict) -> Optional["Sporcu"]:
        """Kart seçme mantığı (Polymorphism)"""
        pass

    def __str__(self):
        return f"{self._oyuncu_adi} | Skor:{self._skor} | Moral:{self._moral}"


# ---------------------------------------------------------------------------
# KULLANICI
# ---------------------------------------------------------------------------


class Kullanici(Oyuncu):
    """Kullanıcı sınıfı – GUI üzerinden kart seçer"""

    def __init__(self, oyuncu_id: int = 1, oyuncu_adi: str = "Oyuncu"):
        super().__init__(oyuncu_id, oyuncu_adi)
        self._secilen_kart: Optional["Sporcu"] = None
        self._legend_aktif: bool = False  # GUI'den aktifleştirilir

    @property
    def secilen_kart(self) -> Optional["Sporcu"]:
        return self._secilen_kart

    @secilen_kart.setter
    def secilen_kart(self, kart: Optional["Sporcu"]):
        self._secilen_kart = kart

    @property
    def legend_aktif(self) -> bool:
        return self._legend_aktif

    @legend_aktif.setter
    def legend_aktif(self, value: bool):
        self._legend_aktif = value

    def kart_sec(self, brans: "Brans", oyun_durumu: dict) -> Optional["Sporcu"]:
        """GUI'de önceden set edilen kartı döndür"""
        return self._secilen_kart


# ---------------------------------------------------------------------------
# BİLGİSAYAR
# ---------------------------------------------------------------------------


class Bilgisayar(Oyuncu):
    """Bilgisayar sınıfı – yapay zekâ stratejisi ile kart seçer"""

    def __init__(
        self,
        strateji: "KartSecmeStratejisi",
        oyuncu_id: int = 2,
        oyuncu_adi: str = "Bilgisayar",
    ):
        super().__init__(oyuncu_id, oyuncu_adi)
        self._strateji = strateji
        self._kartlar_goster: bool = True

    @property
    def strateji(self) -> "KartSecmeStratejisi":
        return self._strateji

    @strateji.setter
    def strateji(self, value: "KartSecmeStratejisi"):
        self._strateji = value

    @property
    def kartlar_goster(self) -> bool:
        return self._kartlar_goster

    def kartlar_goster_toggle(self):
        self._kartlar_goster = not self._kartlar_goster

    def kart_sec(self, brans: "Brans", oyun_durumu: dict) -> Optional["Sporcu"]:
        """Strateji ile kart seç"""
        brans_kartlari = self.get_brans_kartlari(brans)

        if not brans_kartlari:
            # Branş kartı yoksa diğer oynanabilir kartlardan seç
            brans_kartlari = self.get_oynanabilir_kartlar()

        if not brans_kartlari:
            return None

        return self._strateji.kart_sec(brans_kartlari, oyun_durumu)
