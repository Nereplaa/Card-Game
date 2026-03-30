# -*- coding: utf-8 -*-
"""
Kart seçme stratejileri – Strategy Design Pattern
KartSecmeStratejisi (Interface/ABC) → KolayStrateji, OrtaStrateji
"""
from abc import ABC, abstractmethod
import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Sporcu, Brans


class KartSecmeStratejisi(ABC):
    """
    Kart seçme stratejisi için soyut arayüz (Interface).
    Strategy Pattern: algoritma ailesi tanımlanır ve değiştirilebilir yapılır.
    """

    @abstractmethod
    def kart_sec(self, kartlar: List["Sporcu"], oyun_durumu: dict) -> Optional["Sporcu"]:
        """Uygun kartı seçerek döndür"""
        pass

    @property
    @abstractmethod
    def strateji_adi(self) -> str:
        """Strateji adı"""
        pass

    def _oynanabilir_filtrele(self, kartlar: List["Sporcu"]) -> List["Sporcu"]:
        return [k for k in kartlar if k.oynanabilir_mi()]


class KolayStrateji(KartSecmeStratejisi):
    """
    Kolay strateji: Oynanabilir kartlardan rastgele birini seçer.
    """

    @property
    def strateji_adi(self) -> str:
        return "Kolay"

    def kart_sec(self, kartlar: List["Sporcu"], oyun_durumu: dict) -> Optional["Sporcu"]:
        oynanabilir = self._oynanabilir_filtrele(kartlar)
        if not oynanabilir:
            return None
        return random.choice(oynanabilir)


class OrtaStrateji(KartSecmeStratejisi):
    """
    Orta strateji: Uygun kartlar içinde güncel ortalama performansı
    en yüksek olan kartı seçer.
    """

    @property
    def strateji_adi(self) -> str:
        return "Orta"

    def kart_sec(self, kartlar: List["Sporcu"], oyun_durumu: dict) -> Optional["Sporcu"]:
        oynanabilir = self._oynanabilir_filtrele(kartlar)
        if not oynanabilir:
            return None
        # Mevcut oyun durumunu kullanarak performans hesapla
        return max(
            oynanabilir,
            key=lambda k: k.ortalama_performans(),
        )


def strateji_olustur(zorluk: str) -> KartSecmeStratejisi:
    """Zorluk seviyesine göre strateji örneği oluştur (Factory)"""
    if zorluk.lower() == "kolay":
        return KolayStrateji()
    elif zorluk.lower() == "orta":
        return OrtaStrateji()
    else:
        raise ValueError(f"Bilinmeyen zorluk seviyesi: {zorluk}")
