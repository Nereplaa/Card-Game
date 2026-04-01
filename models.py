# -*- coding: utf-8 -*-
"""
Sporcu sınıf hiyerarşisi - OOP: Abstraction, Encapsulation, Inheritance, Polymorphism
"""
from abc import ABC, abstractmethod
from enum import Enum


class Brans(Enum):
    FUTBOL = "futbolcu"
    BASKETBOL = "basketbolcu"
    VOLEYBOL = "voleybolcu"

    @classmethod
    def from_str(cls, s: str) -> "Brans":
        for b in cls:
            if b.value.lower() == s.lower().strip():
                return b
        raise ValueError(f"Bilinmeyen branş: {s}")

    def goster_adi(self) -> str:
        mapping = {
            "futbolcu": "Futbol",
            "basketbolcu": "Basketbol",
            "voleybolcu": "Voleybol",
        }
        return mapping.get(self.value, self.value)


class OzelYetenek:
    """Sporcu özel yeteneklerini temsil eden sınıf (Encapsulation)"""

    YETENEKLER = {
        "ClutchPlayer": {
            "ad": "Clutch Player",
            "aciklama": "Son 3 turda +10 performans bonusu sağlar.",
            "pasif": True,
        },
        "Captain": {
            "ad": "Captain",
            "aciklama": "Aynı branştaki takım kartlarına +5 moral etkisi kazandırır.",
            "pasif": True,
        },
        "Legend": {
            "ad": "Legend",
            "aciklama": "Bir maçta bir kez seçilen özelliği iki kat etkiler (aktif).",
            "pasif": False,
        },
        "Defender": {
            "ad": "Defender",
            "aciklama": "Rakibin özel yetenek bonusunu yarıya düşürür.",
            "pasif": True,
        },
        "Veteran": {
            "ad": "Veteran",
            "aciklama": "Enerji kaybını %50 azaltır.",
            "pasif": True,
        },
        "Finisher": {
            "ad": "Finisher",
            "aciklama": "Enerji 40'ın altındayken +8 ek bonus alır.",
            "pasif": True,
        },
    }

    def __init__(self, tur: str):
        self._tur = tur
        self._kullanildi = False
        info = self.YETENEKLER.get(
            tur, {"ad": tur, "aciklama": "Özel yetenek.", "pasif": True}
        )
        self._ad = info["ad"]
        self._aciklama = info["aciklama"]
        self._pasif = info["pasif"]

    @staticmethod
    def olustur(tur: str) -> "OzelYetenek":
        return OzelYetenek(tur)

    # --- Properties ---
    @property
    def tur(self) -> str:
        return self._tur

    @property
    def ad(self) -> str:
        return self._ad

    @property
    def aciklama(self) -> str:
        return self._aciklama

    @property
    def pasif(self) -> bool:
        return self._pasif

    @property
    def kullanildi(self) -> bool:
        return self._kullanildi

    def kullan(self):
        """Aktif yeteneği kullan (Legend gibi – yalnızca 1 kez)"""
        if not self._pasif:
            self._kullanildi = True

    def sifirla(self):
        """Maç başında sıfırla"""
        self._kullanildi = False

    def __str__(self):
        durum = "(kullanıldı)" if self._kullanildi else ""
        return f"{self._ad} {durum}"


# ---------------------------------------------------------------------------
# SOYUT SPORCU SINIFI
# ---------------------------------------------------------------------------


class Sporcu(ABC):
    """
    Soyut Sporcu sınıfı – tüm sporcu türlerinin temel sınıfı.
    Abstraction + Encapsulation + Inheritance + Polymorphism uygular.
    """

    def __init__(
        self,
        sporcu_id: int,
        ad: str,
        takim: str,
        brans: Brans,
        dayaniklilik: int,
        enerji: int,
        ozel_yetenek_adi: str,
    ):
        # Encapsulation: tüm alanlar private (_)
        self._sporcu_id = sporcu_id
        self._sporcu_adi = ad
        self._sporcu_takim = takim
        self._brans = brans
        self._dayaniklilik = dayaniklilik
        self._base_dayaniklilik = dayaniklilik
        self._max_enerji = enerji
        self._enerji = enerji
        self._seviye = 1
        self._deneyim_puani = 0
        self._kart_kullanildi_mi = False
        self._ozel_yetenek = OzelYetenek.olustur(ozel_yetenek_adi)
        self._moral = 75
        self._kullanim_sayisi = 0
        self._kazanma_sayisi = 0
        self._kaybetme_sayisi = 0
        self._first_win_after_level_up = False  # seviye sonrası ilk galibiyet bonusu

    # --- Properties (Encapsulation) ---
    @property
    def sporcu_id(self) -> int:
        return self._sporcu_id

    @property
    def sporcu_adi(self) -> str:
        return self._sporcu_adi

    @property
    def sporcu_takim(self) -> str:
        return self._sporcu_takim

    @property
    def brans(self) -> Brans:
        return self._brans

    @property
    def dayaniklilik(self) -> int:
        return self._dayaniklilik

    @property
    def enerji(self) -> int:
        return self._enerji

    @property
    def max_enerji(self) -> int:
        return self._max_enerji

    @property
    def seviye(self) -> int:
        return self._seviye

    @property
    def deneyim_puani(self) -> int:
        return self._deneyim_puani

    @property
    def moral(self) -> int:
        return self._moral

    @moral.setter
    def moral(self, value: int):
        self._moral = max(0, min(100, value))

    @property
    def ozel_yetenek(self) -> OzelYetenek:
        return self._ozel_yetenek

    @property
    def kart_kullanildi_mi(self) -> bool:
        return self._kart_kullanildi_mi

    @kart_kullanildi_mi.setter
    def kart_kullanildi_mi(self, value: bool):
        self._kart_kullanildi_mi = value

    @property
    def kazanma_sayisi(self) -> int:
        return self._kazanma_sayisi

    @property
    def kaybetme_sayisi(self) -> int:
        return self._kaybetme_sayisi

    @property
    def kullanim_sayisi(self) -> int:
        return self._kullanim_sayisi

    @property
    def first_win_after_level_up(self) -> bool:
        return self._first_win_after_level_up

    @first_win_after_level_up.setter
    def first_win_after_level_up(self, value: bool):
        self._first_win_after_level_up = value

    # --- Oynanabilirlik ---
    def oynanabilir_mi(self) -> bool:
        return self._enerji > 0 and not self._kart_kullanildi_mi

    def kritik_enerji_mi(self) -> bool:
        return 0 < self._enerji < 20

    # --- Başlangıç değeri atama ---
    def baslangic_ayarla(self, enerji: int, moral: int):
        """Oyun başında rastgele başlangıç değerleri ata"""
        self._enerji = max(0, min(self._max_enerji, enerji))
        self._moral = max(0, min(100, moral))

    # --- Enerji yönetimi ---
    def enerji_guncelle(self, miktar: int, veteran_bonus: bool = False):
        """Veteran pasifi aktifse kaybı %50 azalt"""
        if veteran_bonus and miktar < 0:
            miktar = int(miktar * 0.5)
        self._enerji = max(0, min(self._max_enerji, self._enerji + miktar))

    # --- Moral yönetimi ---
    def moral_guncelle(self, miktar: int):
        self._moral = max(0, min(100, self._moral + miktar))

    # --- Kazanma/Kaybetme kayıtları ---
    def kazanma_kaydet(self):
        self._kazanma_sayisi += 1
        self._kullanim_sayisi += 1
        self._kart_kullanildi_mi = True
        self._deneyim_puani += 2
        self._seviye_kontrol()

    def kaybetme_kaydet(self):
        self._kaybetme_sayisi += 1
        self._kullanim_sayisi += 1
        self._kart_kullanildi_mi = True

    def beraberlik_kaydet(self):
        # Beraberlikte kart "kullanıldı" sayılmaz – elde kalır ve tekrar oynanabilir
        self._kullanim_sayisi += 1
        # kart_kullanildi_mi = False kalır (kural: kartlar elde kalır)
        self._deneyim_puani += 1
        self._seviye_kontrol()

    def seviye_atla_kontrol(self) -> bool:
        onceki = self._seviye
        self._seviye_kontrol()
        return self._seviye > onceki

    def _seviye_kontrol(self):
        """Seviye atlama koşullarını kontrol et"""
        if self._seviye >= 3:
            return
        if self._seviye == 1:
            if self._kazanma_sayisi >= 2 or self._deneyim_puani >= 4:
                self._seviye_yuksel()
        elif self._seviye == 2:
            if self._kazanma_sayisi >= 4 or self._deneyim_puani >= 8:
                self._seviye_yuksel()

    def _seviye_yuksel(self):
        self._seviye += 1
        self._ozellikleri_artir(5)
        self._max_enerji += 10
        self._enerji = min(self._enerji + 10, self._max_enerji)
        self._dayaniklilik += 5
        self._first_win_after_level_up = True

    @abstractmethod
    def _ozellikleri_artir(self, miktar: int):
        """Branşa özgü özellikleri artır (Abstraction)"""
        pass

    # --- Hesaplama yardımcıları ---
    def _enerji_cezasi_hesapla(self, temel_puan: int) -> int:
        if self._enerji > 70:
            return 0
        elif 40 <= self._enerji <= 70:
            return int(temel_puan * 0.10)
        elif 0 < self._enerji < 40:
            return int(temel_puan * 0.20)
        return 0

    def _moral_bonusu_hesapla(self) -> int:
        if 90 <= self._moral <= 100:
            return 10
        elif 80 <= self._moral <= 89:
            return 5
        elif 0 <= self._moral <= 49:
            return -5
        return 0  # 50–79: normal

    def _seviye_bonusu_hesapla(self) -> int:
        return (self._seviye - 1) * 5

    # --- Soyut metotlar (Polymorphism) ---
    @abstractmethod
    def performans_hesapla(self, ozellik_adi: str, oyun_durumu: dict = None) -> dict:
        """
        Performans hesapla ve ayrıntılı sonuç döndür.
        Dönüş: {temel_puan, final_puan, ozel_yetenek_bonusu, moral_bonusu,
                enerji_cezasi, seviye_bonusu}
        """
        pass

    @abstractmethod
    def sporcu_puani_goster(self) -> str:
        pass

    @abstractmethod
    def kart_bilgisi_yazdir(self) -> dict:
        pass

    @abstractmethod
    def ozel_yetenek_uygula(self, oyun_durumu: dict) -> int:
        """Özel yetenek bonus değeri döndür"""
        pass

    @abstractmethod
    def get_ozellikler(self) -> dict:
        pass

    @abstractmethod
    def get_ozellik_listesi(self) -> list:
        pass

    def ortalama_performans(self) -> float:
        """AI için ortalama performans puanı"""
        ozellikler = self.get_ozellik_listesi()
        if not ozellikler:
            return 0.0
        total = sum(self.performans_hesapla(o)["final_puan"] for o in ozellikler)
        return total / len(ozellikler)

    def __str__(self):
        return (
            f"{self._sporcu_adi} ({self._sporcu_takim}) | "
            f"E:{self._enerji}/{self._max_enerji} | "
            f"Sv:{self._seviye} | XP:{self._deneyim_puani}"
        )

    def __repr__(self):
        return self.__str__()


# ---------------------------------------------------------------------------
# YARDIMCI: özel yetenek bonusu ortak hesaplama
# ---------------------------------------------------------------------------


def _hesapla_ozel_yetenek(sporcu: "Sporcu", oyun_durumu: dict) -> int:
    """Tüm sporcu türleri için ortak özel yetenek bonusu hesabı (Polymorphism desteği)"""
    tur = sporcu.ozel_yetenek.tur

    if tur == "ClutchPlayer":
        if oyun_durumu.get("son_3_tur", False):
            return 10

    elif tur == "Legend":
        if oyun_durumu.get("legend_aktif", False) and not sporcu.ozel_yetenek.kullanildi:
            temel = oyun_durumu.get("temel_puan", 0)
            sporcu.ozel_yetenek.kullan()
            return temel  # özellik puanını ikiye katla

    elif tur == "Finisher":
        if sporcu.enerji < 40:
            return 8

    # Veteran, Defender, Captain: bu yöntemde 0 döner, etkileri başka yerlerde işlenir
    return 0


# ---------------------------------------------------------------------------
# FUTBOLCU
# ---------------------------------------------------------------------------


class Futbolcu(Sporcu):
    """Futbolcu sınıfı – Sporcu'dan miras (Inheritance)"""

    def __init__(
        self,
        sporcu_id: int,
        ad: str,
        takim: str,
        penalti: int,
        serbest_vurus: int,
        kaleci_karsi_karsiya: int,
        dayaniklilik: int,
        enerji: int,
        ozel_yetenek_adi: str,
    ):
        super().__init__(
            sporcu_id, ad, takim, Brans.FUTBOL, dayaniklilik, enerji, ozel_yetenek_adi
        )
        self._penalti = penalti
        self._serbest_vurus = serbest_vurus
        self._kaleci_karsi_karsiya = kaleci_karsi_karsiya

    # Properties
    @property
    def penalti(self) -> int:
        return self._penalti

    @property
    def serbest_vurus(self) -> int:
        return self._serbest_vurus

    @property
    def kaleci_karsi_karsiya(self) -> int:
        return self._kaleci_karsi_karsiya

    def _ozellikleri_artir(self, miktar: int):
        self._penalti += miktar
        self._serbest_vurus += miktar
        self._kaleci_karsi_karsiya += miktar

    def get_ozellikler(self) -> dict:
        return {
            "Penaltı": self._penalti,
            "SerbestVuruş": self._serbest_vurus,
            "KaleciKarşıKarşıya": self._kaleci_karsi_karsiya,
        }

    def get_ozellik_listesi(self) -> list:
        return ["Penaltı", "SerbestVuruş", "KaleciKarşıKarşıya"]

    def _get_ozellik_degeri(self, ozellik_adi: str) -> int:
        return self.get_ozellikler().get(ozellik_adi, 0)

    def performans_hesapla(self, ozellik_adi: str, oyun_durumu: dict = None) -> dict:
        """Polymorphism: her sporcu türü kendi performansını hesaplar"""
        od = oyun_durumu or {}
        temel_puan = self._get_ozellik_degeri(ozellik_adi)
        od["temel_puan"] = temel_puan

        moral_bonusu = self._moral_bonusu_hesapla()
        enerji_cezasi = self._enerji_cezasi_hesapla(temel_puan)
        seviye_bonusu = self._seviye_bonusu_hesapla()
        ozel_yetenek_bonusu = self.ozel_yetenek_uygula(od)

        final_puan = (
            temel_puan
            + moral_bonusu
            - enerji_cezasi
            + seviye_bonusu
            + ozel_yetenek_bonusu
        )
        return {
            "temel_puan": temel_puan,
            "final_puan": max(0, final_puan),
            "ozel_yetenek_bonusu": ozel_yetenek_bonusu,
            "moral_bonusu": moral_bonusu,
            "enerji_cezasi": enerji_cezasi,
            "seviye_bonusu": seviye_bonusu,
        }

    def ozel_yetenek_uygula(self, oyun_durumu: dict) -> int:
        return _hesapla_ozel_yetenek(self, oyun_durumu)

    def sporcu_puani_goster(self) -> str:
        return (
            f"⚽ Futbolcu: {self._sporcu_adi}\n"
            f"Penaltı: {self._penalti}  SerbestVuruş: {self._serbest_vurus}  "
            f"KaleciKarşıKarşıya: {self._kaleci_karsi_karsiya}\n"
            f"Dayanıklılık: {self._dayaniklilik}  Enerji: {self._enerji}/{self._max_enerji}\n"
            f"Seviye: {self._seviye}  XP: {self._deneyim_puani}  Moral: {self._moral}\n"
            f"Özel Yetenek: {self._ozel_yetenek.ad}"
        )

    def kart_bilgisi_yazdir(self) -> dict:
        return {
            "id": self._sporcu_id,
            "ad": self._sporcu_adi,
            "takim": self._sporcu_takim,
            "brans": "Futbolcu",
            "brans_enum": self._brans,
            "ozellikler": self.get_ozellikler(),
            "dayaniklilik": self._dayaniklilik,
            "enerji": self._enerji,
            "max_enerji": self._max_enerji,
            "seviye": self._seviye,
            "deneyim": self._deneyim_puani,
            "moral": self._moral,
            "ozel_yetenek": self._ozel_yetenek.ad,
            "ozel_yetenek_aciklama": self._ozel_yetenek.aciklama,
            "kazanma": self._kazanma_sayisi,
            "kaybetme": self._kaybetme_sayisi,
            "kullanim": self._kullanim_sayisi,
        }


# ---------------------------------------------------------------------------
# BASKETBOLCU
# ---------------------------------------------------------------------------


class Basketbolcu(Sporcu):
    """Basketbolcu sınıfı – Sporcu'dan miras (Inheritance)"""

    def __init__(
        self,
        sporcu_id: int,
        ad: str,
        takim: str,
        ikilik: int,
        ucluk: int,
        serbest_atis: int,
        dayaniklilik: int,
        enerji: int,
        ozel_yetenek_adi: str,
    ):
        super().__init__(
            sporcu_id, ad, takim, Brans.BASKETBOL, dayaniklilik, enerji, ozel_yetenek_adi
        )
        self._ikilik = ikilik
        self._ucluk = ucluk
        self._serbest_atis = serbest_atis

    @property
    def ikilik(self) -> int:
        return self._ikilik

    @property
    def ucluk(self) -> int:
        return self._ucluk

    @property
    def serbest_atis(self) -> int:
        return self._serbest_atis

    def _ozellikleri_artir(self, miktar: int):
        self._ikilik += miktar
        self._ucluk += miktar
        self._serbest_atis += miktar

    def get_ozellikler(self) -> dict:
        return {
            "İkilik": self._ikilik,
            "Üçlük": self._ucluk,
            "SerbestAtış": self._serbest_atis,
        }

    def get_ozellik_listesi(self) -> list:
        return ["İkilik", "Üçlük", "SerbestAtış"]

    def _get_ozellik_degeri(self, ozellik_adi: str) -> int:
        return self.get_ozellikler().get(ozellik_adi, 0)

    def performans_hesapla(self, ozellik_adi: str, oyun_durumu: dict = None) -> dict:
        od = oyun_durumu or {}
        temel_puan = self._get_ozellik_degeri(ozellik_adi)
        od["temel_puan"] = temel_puan

        moral_bonusu = self._moral_bonusu_hesapla()
        enerji_cezasi = self._enerji_cezasi_hesapla(temel_puan)
        seviye_bonusu = self._seviye_bonusu_hesapla()
        ozel_yetenek_bonusu = self.ozel_yetenek_uygula(od)

        final_puan = (
            temel_puan
            + moral_bonusu
            - enerji_cezasi
            + seviye_bonusu
            + ozel_yetenek_bonusu
        )
        return {
            "temel_puan": temel_puan,
            "final_puan": max(0, final_puan),
            "ozel_yetenek_bonusu": ozel_yetenek_bonusu,
            "moral_bonusu": moral_bonusu,
            "enerji_cezasi": enerji_cezasi,
            "seviye_bonusu": seviye_bonusu,
        }

    def ozel_yetenek_uygula(self, oyun_durumu: dict) -> int:
        return _hesapla_ozel_yetenek(self, oyun_durumu)

    def sporcu_puani_goster(self) -> str:
        return (
            f"🏀 Basketbolcu: {self._sporcu_adi}\n"
            f"İkilik: {self._ikilik}  Üçlük: {self._ucluk}  SerbestAtış: {self._serbest_atis}\n"
            f"Dayanıklılık: {self._dayaniklilik}  Enerji: {self._enerji}/{self._max_enerji}\n"
            f"Seviye: {self._seviye}  XP: {self._deneyim_puani}  Moral: {self._moral}\n"
            f"Özel Yetenek: {self._ozel_yetenek.ad}"
        )

    def kart_bilgisi_yazdir(self) -> dict:
        return {
            "id": self._sporcu_id,
            "ad": self._sporcu_adi,
            "takim": self._sporcu_takim,
            "brans": "Basketbolcu",
            "brans_enum": self._brans,
            "ozellikler": self.get_ozellikler(),
            "dayaniklilik": self._dayaniklilik,
            "enerji": self._enerji,
            "max_enerji": self._max_enerji,
            "seviye": self._seviye,
            "deneyim": self._deneyim_puani,
            "moral": self._moral,
            "ozel_yetenek": self._ozel_yetenek.ad,
            "ozel_yetenek_aciklama": self._ozel_yetenek.aciklama,
            "kazanma": self._kazanma_sayisi,
            "kaybetme": self._kaybetme_sayisi,
            "kullanim": self._kullanim_sayisi,
        }


# ---------------------------------------------------------------------------
# VOLEYBOLCU
# ---------------------------------------------------------------------------


class Voleybolcu(Sporcu):
    """Voleybolcu sınıfı – Sporcu'dan miras (Inheritance)"""

    def __init__(
        self,
        sporcu_id: int,
        ad: str,
        takim: str,
        servis: int,
        blok: int,
        smac: int,
        dayaniklilik: int,
        enerji: int,
        ozel_yetenek_adi: str,
    ):
        super().__init__(
            sporcu_id, ad, takim, Brans.VOLEYBOL, dayaniklilik, enerji, ozel_yetenek_adi
        )
        self._servis = servis
        self._blok = blok
        self._smac = smac

    @property
    def servis(self) -> int:
        return self._servis

    @property
    def blok(self) -> int:
        return self._blok

    @property
    def smac(self) -> int:
        return self._smac

    def _ozellikleri_artir(self, miktar: int):
        self._servis += miktar
        self._blok += miktar
        self._smac += miktar

    def get_ozellikler(self) -> dict:
        return {
            "Servis": self._servis,
            "Blok": self._blok,
            "Smaç": self._smac,
        }

    def get_ozellik_listesi(self) -> list:
        return ["Servis", "Blok", "Smaç"]

    def _get_ozellik_degeri(self, ozellik_adi: str) -> int:
        return self.get_ozellikler().get(ozellik_adi, 0)

    def performans_hesapla(self, ozellik_adi: str, oyun_durumu: dict = None) -> dict:
        od = oyun_durumu or {}
        temel_puan = self._get_ozellik_degeri(ozellik_adi)
        od["temel_puan"] = temel_puan

        moral_bonusu = self._moral_bonusu_hesapla()
        enerji_cezasi = self._enerji_cezasi_hesapla(temel_puan)
        seviye_bonusu = self._seviye_bonusu_hesapla()
        ozel_yetenek_bonusu = self.ozel_yetenek_uygula(od)

        final_puan = (
            temel_puan
            + moral_bonusu
            - enerji_cezasi
            + seviye_bonusu
            + ozel_yetenek_bonusu
        )
        return {
            "temel_puan": temel_puan,
            "final_puan": max(0, final_puan),
            "ozel_yetenek_bonusu": ozel_yetenek_bonusu,
            "moral_bonusu": moral_bonusu,
            "enerji_cezasi": enerji_cezasi,
            "seviye_bonusu": seviye_bonusu,
        }

    def ozel_yetenek_uygula(self, oyun_durumu: dict) -> int:
        return _hesapla_ozel_yetenek(self, oyun_durumu)

    def sporcu_puani_goster(self) -> str:
        return (
            f"🏐 Voleybolcu: {self._sporcu_adi}\n"
            f"Servis: {self._servis}  Blok: {self._blok}  Smaç: {self._smac}\n"
            f"Dayanıklılık: {self._dayaniklilik}  Enerji: {self._enerji}/{self._max_enerji}\n"
            f"Seviye: {self._seviye}  XP: {self._deneyim_puani}  Moral: {self._moral}\n"
            f"Özel Yetenek: {self._ozel_yetenek.ad}"
        )

    def kart_bilgisi_yazdir(self) -> dict:
        return {
            "id": self._sporcu_id,
            "ad": self._sporcu_adi,
            "takim": self._sporcu_takim,
            "brans": "Voleybolcu",
            "brans_enum": self._brans,
            "ozellikler": self.get_ozellikler(),
            "dayaniklilik": self._dayaniklilik,
            "enerji": self._enerji,
            "max_enerji": self._max_enerji,
            "seviye": self._seviye,
            "deneyim": self._deneyim_puani,
            "moral": self._moral,
            "ozel_yetenek": self._ozel_yetenek.ad,
            "ozel_yetenek_aciklama": self._ozel_yetenek.aciklama,
            "kazanma": self._kazanma_sayisi,
            "kaybetme": self._kaybetme_sayisi,
            "kullanim": self._kullanim_sayisi,
        }
