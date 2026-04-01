# -*- coding: utf-8 -*-
"""
Oyun Motoru: VeriOkuyucu, MacIstatistik, OyunYonetici
"""
import csv
import os
import random
from typing import List, Optional, Dict, Tuple

from models import Sporcu, Futbolcu, Basketbolcu, Voleybolcu, Brans
from players import Kullanici, Bilgisayar
from strategies import KartSecmeStratejisi


# ---------------------------------------------------------------------------
# VERİ OKUYUCU
# ---------------------------------------------------------------------------


class VeriOkuyucu:
    """Sporcu verilerini CSV/TXT dosyasından okur ve Sporcu nesnelerine dönüştürür."""

    def __init__(self, dosya_yolu: str):
        self._dosya_yolu = dosya_yolu
        self._hatalar: List[str] = []

    @property
    def hatalar(self) -> List[str]:
        return list(self._hatalar)

    def oku(self) -> List[Sporcu]:
        """Dosyadan tüm sporcu nesnelerini oku. Hatalı satırlar atlanır."""
        self._hatalar = []
        sporcular: List[Sporcu] = []

        if not os.path.exists(self._dosya_yolu):
            self._hatalar.append(f"Dosya bulunamadı: {self._dosya_yolu}")
            return sporcular

        try:
            with open(self._dosya_yolu, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for satir_no, satir in enumerate(reader, start=2):
                    try:
                        sporcu = self._satir_parse(satir_no, satir, len(sporcular) + 1)
                        if sporcu:
                            sporcular.append(sporcu)
                    except Exception as e:
                        self._hatalar.append(f"Satır {satir_no}: {e}")
        except Exception as e:
            self._hatalar.append(f"Dosya okuma hatası: {e}")

        return sporcular

    def _satir_parse(self, satir_no: int, satir: dict, sporcu_id: int) -> Optional[Sporcu]:
        gerekli = ["tur", "ad", "takim", "ozellik1", "ozellik2", "ozellik3",
                   "dayaniklilik", "enerji", "ozel_yetenek"]
        for alan in gerekli:
            if alan not in satir or not str(satir[alan]).strip():
                raise ValueError(f"Eksik alan: '{alan}'")

        tur = satir["tur"].strip().lower()
        ad = satir["ad"].strip()
        takim = satir["takim"].strip()

        try:
            o1 = int(satir["ozellik1"].strip())
            o2 = int(satir["ozellik2"].strip())
            o3 = int(satir["ozellik3"].strip())
            day = int(satir["dayaniklilik"].strip())
            enerji = int(satir["enerji"].strip())
        except ValueError as e:
            raise ValueError(f"Sayısal değer hatası: {e}")

        for deger, isim in [(o1, "ozellik1"), (o2, "ozellik2"), (o3, "ozellik3"),
                            (day, "dayaniklilik"), (enerji, "enerji")]:
            if not (0 <= deger <= 150):
                raise ValueError(f"'{isim}' geçersiz değer: {deger} (0-150 arası olmalı)")

        ozy = satir["ozel_yetenek"].strip()

        if tur == "futbolcu":
            return Futbolcu(sporcu_id, ad, takim, o1, o2, o3, day, enerji, ozy)
        elif tur == "basketbolcu":
            return Basketbolcu(sporcu_id, ad, takim, o1, o2, o3, day, enerji, ozy)
        elif tur == "voleybolcu":
            return Voleybolcu(sporcu_id, ad, takim, o1, o2, o3, day, enerji, ozy)
        else:
            raise ValueError(f"Bilinmeyen sporcu türü: '{tur}'")


# ---------------------------------------------------------------------------
# MAÇ İSTATİSTİĞİ
# ---------------------------------------------------------------------------


class MacIstatistik:
    """Tüm maç verilerini tutar, tur sonu ve maç sonu raporları oluşturur."""

    def __init__(self):
        self._turlar: List[dict] = []
        self._toplam_tur = 0
        self._atlanan_turlar = 0

    def tur_kaydet(self, tur_sonucu: dict):
        self._turlar.append(tur_sonucu)
        self._toplam_tur += 1

    def atlanan_tur_kaydet(self):
        self._atlanan_turlar += 1

    @property
    def tur_gecmisi(self) -> List[dict]:
        return list(self._turlar)

    @property
    def toplam_tur(self) -> int:
        return self._toplam_tur

    @property
    def atlanan_turlar(self) -> int:
        return self._atlanan_turlar

    def tur_sayisi_brans(self, brans: Brans) -> int:
        return sum(1 for t in self._turlar if t.get("brans") == brans)

    def mac_raporu_olustur(self, kullanici: "Kullanici", bilgisayar: "Bilgisayar") -> str:
        lines = [
            "=" * 55,
            "          MAÇ SONU RAPORU",
            "=" * 55,
            f"  {kullanici.oyuncu_adi:<20}  vs  {bilgisayar.oyuncu_adi}",
            f"  Skor:  {kullanici.skor:<20}       {bilgisayar.skor}",
            f"  Galibiyet:  {kullanici.toplam_galibiyet:<15}       {bilgisayar.toplam_galibiyet}",
            f"  Mağlubiyet: {kullanici.toplam_maglubiyet:<15}       {bilgisayar.toplam_maglubiyet}",
            f"  Beraberlik: {kullanici.toplam_beraberlik:<15}       {bilgisayar.toplam_beraberlik}",
            f"  Özel Yetenek Gal.: {kullanici.ozel_yetenek_galibiyet:<10}  {bilgisayar.ozel_yetenek_galibiyet}",
            f"  Kalan Enerji: {kullanici.toplam_kalan_enerji():<13}  {bilgisayar.toplam_kalan_enerji()}",
            "-" * 55,
            f"  Toplam Oynanan Tur: {self._toplam_tur}",
            f"  Atlanan Tur:        {self._atlanan_turlar}",
            "=" * 55,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# OYUN YÖNETİCİ
# ---------------------------------------------------------------------------


class OyunYonetici:
    """
    Oyun akışını yönetir: tur başlatır, kartları karşılaştırır,
    puanları günceller, kazananı belirler.
    """

    BRANS_SIRASI = [Brans.FUTBOL, Brans.BASKETBOL, Brans.VOLEYBOL]

    def __init__(self):
        self._kullanici: Optional[Kullanici] = None
        self._bilgisayar: Optional[Bilgisayar] = None
        self._mevcut_tur_no: int = 0          # 0 tabanlı; oynanan tur sayısı
        self._max_tur: int = 12               # teorik maksimum tur (12 kart/oyuncu)
        self._istatistik = MacIstatistik()
        self._oyun_bitti: bool = False
        self._brans_indeks: int = 0           # sıra içindeki branş indeksi
        self._legend_kullanildi_kullanici: bool = False
        self._legend_kullanildi_bilgisayar: bool = False

    # --- Kurulum ---
    def oyunu_kur(self, kullanici: Kullanici, bilgisayar: Bilgisayar):
        self._kullanici = kullanici
        self._bilgisayar = bilgisayar
        self._mevcut_tur_no = 0
        self._brans_indeks = 0
        self._oyun_bitti = False

    def kartlari_dagit(self, tum_sporcular: List[Sporcu]):
        """
        24 kart: 8 Futbolcu, 8 Basketbolcu, 8 Voleybolcu.
        Her oyuncuya branş başına 4 kart rastgele dağıtılır.
        """
        futbolar = [s for s in tum_sporcular if s.brans == Brans.FUTBOL]
        basketlar = [s for s in tum_sporcular if s.brans == Brans.BASKETBOL]
        voleylar = [s for s in tum_sporcular if s.brans == Brans.VOLEYBOL]

        random.shuffle(futbolar)
        random.shuffle(basketlar)
        random.shuffle(voleylar)

        kullanici_kartlar = futbolar[:4] + basketlar[:4] + voleylar[:4]
        bilgisayar_kartlar = futbolar[4:] + basketlar[4:] + voleylar[4:]

        self._kullanici.kartlari_al(kullanici_kartlar)
        self._bilgisayar.kartlari_al(bilgisayar_kartlar)

    # --- Özellikler ---
    @property
    def istatistik(self) -> MacIstatistik:
        return self._istatistik

    @property
    def oyun_bitti(self) -> bool:
        return self._oyun_bitti

    @property
    def mevcut_tur_no(self) -> int:
        return self._mevcut_tur_no

    def mevcut_brans(self) -> Brans:
        return self.BRANS_SIRASI[self._brans_indeks % 3]

    def son_3_tur_mu(self) -> bool:
        """Toplam kalan kart sayısı 6 veya altındaysa son 3 tur kabul edilir."""
        kalan = (
            len(self._kullanici.get_oynanabilir_kartlar())
            + len(self._bilgisayar.get_oynanabilir_kartlar())
        )
        return kalan <= 6

    # --- Tur akışı ---
    def tur_baslat(self) -> dict:
        """
        Sıradaki turun durumunu belirle.
        Döner: { 'durum': ..., 'brans': Brans, 'mesaj': str, 'kullanici_filtre': Brans|None }
        Durum: 'normal' | 'hukmen_kullanici' | 'hukmen_bilgisayar' | 'atla' | 'oyun_bitti'

        Kural:
          - Hükmen sadece ELİ TAMAMEN BOŞ olan oyuncuya karşı uygulanır.
          - Sadece branş kartı yoksa ama diğer kartları varsa → o oyuncu başka branştan oynayabilir.
          - Her iki oyuncunun da bu branşa ait kartı yoksa tur atlanır.
        """
        if self._oyun_bitti:
            return {"durum": "oyun_bitti", "brans": None, "mesaj": "Oyun sona erdi."}

        brans = self.mevcut_brans()

        # Toplam oynanabilir kart kontrolü (hükmen için)
        k_tum = self._kullanici.get_oynanabilir_kartlar()
        b_tum = self._bilgisayar.get_oynanabilir_kartlar()

        if not k_tum and not b_tum:
            self._oyun_bitti = True
            return {"durum": "oyun_bitti", "brans": None, "mesaj": "Her iki oyuncunun da kartı kalmadı."}

        # Hükmen: elin tamamen boşsa (branştan bağımsız)
        if not k_tum and b_tum:
            return self._hukmen_isle(brans, kazanan="bilgisayar",
                                     mesaj_sebebi="kullanıcının hiç kartı kalmadı")
        if k_tum and not b_tum:
            return self._hukmen_isle(brans, kazanan="kullanici",
                                     mesaj_sebebi="bilgisayarın hiç kartı kalmadı")

        # Branşa ait kart kontrolü
        k_brans = self._kullanici.get_brans_kartlari(brans)
        b_brans = self._bilgisayar.get_brans_kartlari(brans)

        # Her iki oyuncuda da bu branşta kart yoksa: tur atlanır
        if not k_brans and not b_brans:
            self._istatistik.atlanan_tur_kaydet()
            self._brans_indeks += 1
            self._mevcut_tur_no += 1
            return {
                "durum": "atla",
                "brans": brans,
                "mesaj": f"Her iki oyuncuda da {brans.goster_adi()} kartı kalmadı. Tur atlandı.",
            }

        # Normal oyun:
        # Eğer oyuncunun bu branşa ait kartı yoksa diğer kartlarından seçebilir
        # kullanici_filtre: None → tüm kartları göster, Brans → sadece branş kartlarını göster
        kullanici_filtre = brans if k_brans else None

        tur_mesaj = f"Tur {self._mevcut_tur_no + 1} – {brans.goster_adi()} branşı"
        if not k_brans:
            tur_mesaj += f"\n⚠ {brans.goster_adi()} kartınız kalmadı – başka branştan oynayabilirsiniz."

        return {
            "durum": "normal",
            "brans": brans,
            "kullanici_filtre": kullanici_filtre,
            "mesaj": tur_mesaj,
        }

    def _hukmen_isle(self, brans: Brans, kazanan: str, mesaj_sebebi: str = "") -> dict:
        """Hükmen galibiyet işle – yalnızca elin tamamen boş olduğu durumda çağrılır"""
        puan = 8
        if kazanan == "kullanici":
            self._kullanici.skor_ekle(puan)
            self._kullanici.galibiyet_kaydet(ozel_yetenek_ile=False)
            self._bilgisayar.maglubiyet_kaydet(brans)
            self._moral_guncelle_seri(self._kullanici, self._bilgisayar)
            mesaj = f"Hükmen Galibiyet! {mesaj_sebebi}. (+{puan} puan)"
        else:
            self._bilgisayar.skor_ekle(puan)
            self._bilgisayar.galibiyet_kaydet(ozel_yetenek_ile=False)
            self._kullanici.maglubiyet_kaydet(brans)
            self._moral_guncelle_seri(self._bilgisayar, self._kullanici)
            mesaj = f"Hükmen Mağlubiyet! {mesaj_sebebi}. (Bilgisayar +{puan})"

        tur_kaydi = {
            "tur_no": self._mevcut_tur_no + 1,
            "brans": brans,
            "tip": "hukmen",
            "kazanan": kazanan,
            "kullanici_skor": self._kullanici.skor,
            "bilgisayar_skor": self._bilgisayar.skor,
        }
        self._istatistik.tur_kaydet(tur_kaydi)
        self._brans_indeks += 1
        self._mevcut_tur_no += 1

        return {
            "durum": f"hukmen_{kazanan}",
            "brans": brans,
            "mesaj": mesaj,
            "tur_kaydi": tur_kaydi,
        }

    def tur_oyna(
        self,
        kullanici_kart: Sporcu,
        bilgisayar_kart: Sporcu,
        legend_aktif: bool = False,
    ) -> dict:
        """
        Ana tur mantığı.
        Kullanıcı ve bilgisayar kartlarını alır, karşılaştırmayı yapar.
        Dönüş: kapsamlı tur sonucu dict.
        """
        brans = self.mevcut_brans()
        son_3 = self.son_3_tur_mu()
        tur_no = self._mevcut_tur_no + 1

        # Rastgele özellik seç
        ozellik_listesi = kullanici_kart.get_ozellik_listesi()
        secilen_ozellik = random.choice(ozellik_listesi)

        # Oyun durumu sözlüğü
        oyun_durumu_k = {
            "son_3_tur": son_3,
            "legend_aktif": legend_aktif and not self._legend_kullanildi_kullanici,
            "tur_no": tur_no,
        }
        oyun_durumu_b = {
            "son_3_tur": son_3,
            "legend_aktif": False,  # Bilgisayar Legend'ı kendiliğinden aktifleştirmez
            "tur_no": tur_no,
        }

        # Performans hesapla
        k_perf = kullanici_kart.performans_hesapla(secilen_ozellik, oyun_durumu_k)
        b_perf = bilgisayar_kart.performans_hesapla(secilen_ozellik, oyun_durumu_b)

        # Legend kullanıldıysa işaretle
        if kullanici_kart.ozel_yetenek.tur == "Legend" and kullanici_kart.ozel_yetenek.kullanildi:
            self._legend_kullanildi_kullanici = True

        # Defender etkisi: rakibin özel yetenek bonusunu yarıya düşür
        if kullanici_kart.ozel_yetenek.tur == "Defender":
            original = b_perf["ozel_yetenek_bonusu"]
            b_perf["ozel_yetenek_bonusu"] = original // 2
            b_perf["final_puan"] = max(0, b_perf["final_puan"] - (original - original // 2))

        if bilgisayar_kart.ozel_yetenek.tur == "Defender":
            original = k_perf["ozel_yetenek_bonusu"]
            k_perf["ozel_yetenek_bonusu"] = original // 2
            k_perf["final_puan"] = max(0, k_perf["final_puan"] - (original - original // 2))

        k_final = k_perf["final_puan"]
        b_final = b_perf["final_puan"]

        # Kazananı belirle (çoklu kriter)
        kazanan = self._kazanani_belirle(
            kullanici_kart, bilgisayar_kart,
            k_final, b_final,
            secilen_ozellik
        )

        # Puan hesapla
        k_ozel = k_perf["ozel_yetenek_bonusu"] > 0
        b_ozel = b_perf["ozel_yetenek_bonusu"] > 0

        k_puan_kazanildi = 0
        b_puan_kazanildi = 0

        if kazanan == "kullanici":
            k_puan_kazanildi = 15 if k_ozel else 10
            k_puan_kazanildi += self._ek_bonuslar_hesapla(
                self._kullanici, kullanici_kart, son_3, k_ozel
            )
            k_puan_kazanildi += self._seri_bonusu(self._kullanici)
            self._kullanici.skor_ekle(k_puan_kazanildi)
            self._kullanici.galibiyet_kaydet(ozel_yetenek_ile=k_ozel)
            self._bilgisayar.maglubiyet_kaydet(brans)
            kullanici_kart.kazanma_kaydet()
            bilgisayar_kart.kaybetme_kaydet()

        elif kazanan == "bilgisayar":
            b_puan_kazanildi = 15 if b_ozel else 10
            b_puan_kazanildi += self._seri_bonusu(self._bilgisayar)
            self._bilgisayar.skor_ekle(b_puan_kazanildi)
            self._bilgisayar.galibiyet_kaydet(ozel_yetenek_ile=b_ozel)
            self._kullanici.maglubiyet_kaydet(brans)
            bilgisayar_kart.kazanma_kaydet()
            kullanici_kart.kaybetme_kaydet()

        else:  # beraberlik
            self._kullanici.beraberlik_kaydet(brans)
            self._bilgisayar.beraberlik_kaydet(brans)
            kullanici_kart.beraberlik_kaydet()
            bilgisayar_kart.beraberlik_kaydet()

        # Moral güncellemesi
        self._moral_guncelle_seri(
            self._kullanici if kazanan == "kullanici" else self._bilgisayar,
            self._bilgisayar if kazanan == "kullanici" else self._kullanici,
            beraberlik=(kazanan == "beraberlik"),
            brans=brans,
        )

        # Captain etkisi
        if kullanici_kart.ozel_yetenek.tur == "Captain":
            self._kullanici.captain_moral_bonusu_uygula(brans, kullanici_kart.sporcu_takim)
        if bilgisayar_kart.ozel_yetenek.tur == "Captain":
            self._bilgisayar.captain_moral_bonusu_uygula(brans, bilgisayar_kart.sporcu_takim)

        # Enerji güncelle
        self._enerji_guncelle(kullanici_kart, kazanan == "kullanici", kazanan == "beraberlik", k_ozel)
        self._enerji_guncelle(bilgisayar_kart, kazanan == "bilgisayar", kazanan == "beraberlik", b_ozel)

        # Seviye kontrolü
        k_seviye_atladi = kullanici_kart.seviye_atla_kontrol()
        b_seviye_atladi = bilgisayar_kart.seviye_atla_kontrol()

        # Sonraki tura hazırla
        self._brans_indeks += 1
        self._mevcut_tur_no += 1

        # Oyun bitti mi?
        if (not self._kullanici.get_oynanabilir_kartlar() and
                not self._bilgisayar.get_oynanabilir_kartlar()):
            self._oyun_bitti = True

        # Sonuç kaydı
        tur_kaydi = {
            "tur_no": tur_no,
            "brans": brans,
            "tip": "normal",
            "secilen_ozellik": secilen_ozellik,
            "kullanici_kart": kullanici_kart.sporcu_adi,
            "bilgisayar_kart": bilgisayar_kart.sporcu_adi,
            "kullanici_final": k_final,
            "bilgisayar_final": b_final,
            "kazanan": kazanan,
            "kullanici_puan_kazanildi": k_puan_kazanildi,
            "bilgisayar_puan_kazanildi": b_puan_kazanildi,
            "kullanici_skor": self._kullanici.skor,
            "bilgisayar_skor": self._bilgisayar.skor,
            "k_seviye_atladi": k_seviye_atladi,
            "b_seviye_atladi": b_seviye_atladi,
        }
        self._istatistik.tur_kaydet(tur_kaydi)

        return {
            "tur_no": tur_no,
            "brans": brans,
            "secilen_ozellik": secilen_ozellik,
            "kullanici_kart": kullanici_kart,
            "bilgisayar_kart": bilgisayar_kart,
            "kullanici_performans": k_perf,
            "bilgisayar_performans": b_perf,
            "kazanan": kazanan,
            "kullanici_puan_kazanildi": k_puan_kazanildi,
            "bilgisayar_puan_kazanildi": b_puan_kazanildi,
            "kullanici_skor": self._kullanici.skor,
            "bilgisayar_skor": self._bilgisayar.skor,
            "k_seviye_atladi": k_seviye_atladi,
            "b_seviye_atladi": b_seviye_atladi,
            "oyun_bitti": self._oyun_bitti,
        }

    # --- Yardımcı metotlar ---

    def _kazanani_belirle(
        self,
        k_kart: Sporcu,
        b_kart: Sporcu,
        k_final: int,
        b_final: int,
        secilen_ozellik: str,
    ) -> str:
        """Çoklu kriter ile kazananı belirle (Kural 6)"""
        if k_final != b_final:
            return "kullanici" if k_final > b_final else "bilgisayar"

        # Yedek özellikler (branşın diğer özellikleri)
        tum_ozellikler = k_kart.get_ozellik_listesi()
        for oz in tum_ozellikler:
            if oz == secilen_ozellik:
                continue
            ko = k_kart.get_ozellikler().get(oz, 0)
            bo = b_kart.get_ozellikler().get(oz, 0)
            if ko != bo:
                return "kullanici" if ko > bo else "bilgisayar"

        # Özel yetenek bonusu
        koy = k_kart.ozel_yetenek_uygula({})
        boy = b_kart.ozel_yetenek_uygula({})
        if koy != boy:
            return "kullanici" if koy > boy else "bilgisayar"

        # Dayanıklılık
        if k_kart.dayaniklilik != b_kart.dayaniklilik:
            return "kullanici" if k_kart.dayaniklilik > b_kart.dayaniklilik else "bilgisayar"

        # Enerji
        if k_kart.enerji != b_kart.enerji:
            return "kullanici" if k_kart.enerji > b_kart.enerji else "bilgisayar"

        # Seviye
        if k_kart.seviye != b_kart.seviye:
            return "kullanici" if k_kart.seviye > b_kart.seviye else "bilgisayar"

        return "beraberlik"

    def _seri_bonusu(self, oyuncu: "Kullanici | Bilgisayar") -> int:
        """3 veya 5 galibiyet serisinde bonus puan"""
        seri = oyuncu.galibiyet_serisi
        bonus = 0
        if seri == 2:  # 3. galibiyetle birlikte +10
            bonus = 10
            oyuncu.seri_kaydet()
        elif seri == 4:  # 5. galibiyetle birlikte +20
            bonus = 20
            oyuncu.seri_kaydet()
        return bonus

    def _ek_bonuslar_hesapla(
        self,
        oyuncu: "Kullanici | Bilgisayar",
        kart: Sporcu,
        son_3_tur: bool,
        ozel_yetenek_ile: bool,
    ) -> int:
        """Ek puan bonusları: düşük enerji, seviye sonrası, clutch"""
        bonus = 0
        # Enerjisi 30 altında olan kartla kazanma
        if kart.enerji < 30:
            bonus += 5
        # Seviye atladıktan sonraki ilk galibiyet
        if kart.first_win_after_level_up:
            bonus += 5
            kart.first_win_after_level_up = False
        # Son 3 turda ClutchPlayer ile kazanma
        if son_3_tur and kart.ozel_yetenek.tur == "ClutchPlayer":
            bonus += 5
        return bonus

    def _enerji_guncelle(
        self, kart: Sporcu, kazandi: bool, beraberlik: bool, ozel_kullandi: bool
    ):
        is_veteran = kart.ozel_yetenek.tur == "Veteran"
        if beraberlik:
            kart.enerji_guncelle(-3, veteran_bonus=is_veteran)
        elif kazandi:
            kart.enerji_guncelle(-5, veteran_bonus=is_veteran)
        else:
            kart.enerji_guncelle(-10, veteran_bonus=is_veteran)
        if ozel_kullandi:
            kart.enerji_guncelle(-5, veteran_bonus=is_veteran)

    def _moral_guncelle_seri(
        self,
        kazanan_oyuncu,
        kaybeden_oyuncu,
        beraberlik: bool = False,
        brans: Brans = None,
    ):
        if beraberlik:
            return  # Beraberlikte moral değişmez

        seri = kazanan_oyuncu.galibiyet_serisi
        if seri == 2:
            kazanan_oyuncu.moral_guncelle(10)
            kazanan_oyuncu.kartlara_moral_uygula(10)
        elif seri >= 3:
            kazanan_oyuncu.moral_guncelle(15)
            kazanan_oyuncu.kartlara_moral_uygula(15)

        k_seri = kaybeden_oyuncu.kaybetme_serisi
        if k_seri >= 2:
            kaybeden_oyuncu.moral_guncelle(-10)
            kaybeden_oyuncu.kartlara_moral_uygula(-10)

        # Aynı branşta arka arkaya 2 mağlubiyet: -5 ek
        if brans and kaybeden_oyuncu.brans_ust_uste_kayip(brans) == 2:
            kaybeden_oyuncu.moral_guncelle(-5)
            kaybeden_oyuncu.kartlara_moral_uygula(-5)

    # --- Oyun sonu ---

    def kazanani_belirle(self) -> Tuple[str, str]:
        """
        Oyun sonu kazananı belirle (Kural 13).
        Dönüş: (kazanan_adi, aciklama)
        """
        k = self._kullanici
        b = self._bilgisayar

        kriterler = [
            (k.skor, b.skor, "toplam puan"),
            (k.toplam_galibiyet, b.toplam_galibiyet, "kazanılan tur sayısı"),
            (k.toplam_seri_sayisi, b.toplam_seri_sayisi, "galibiyet serisi sayısı"),
            (k.toplam_kalan_enerji(), b.toplam_kalan_enerji(), "kalan toplam enerji"),
            (k.max_seviyeli_kart_sayisi(), b.max_seviyeli_kart_sayisi(), "max seviyeli kart"),
            (k.ozel_yetenek_galibiyet, b.ozel_yetenek_galibiyet, "özel yetenekle galibiyet"),
            # Az beraberlik daha iyi (ters sıra)
            (b.toplam_beraberlik, k.toplam_beraberlik, "az beraberlik"),
        ]

        for k_val, b_val, aciklama in kriterler:
            if k_val > b_val:
                return (k.oyuncu_adi, f"Belirleyici kriter: {aciklama}")
            elif b_val > k_val:
                return (b.oyuncu_adi, f"Belirleyici kriter: {aciklama}")

        return ("Beraberlik", "Tüm kriterler eşit – oyun berabere!")

    def tam_rapor(self) -> dict:
        """GUI ve istatistik ekranı için kapsamlı oyun sonu raporu"""
        kazanan_adi, kriter = self.kazanani_belirle()
        return {
            "kazanan": kazanan_adi,
            "kriter": kriter,
            "kullanici": {
                "ad": self._kullanici.oyuncu_adi,
                "skor": self._kullanici.skor,
                "galibiyet": self._kullanici.toplam_galibiyet,
                "maglubiyet": self._kullanici.toplam_maglubiyet,
                "beraberlik": self._kullanici.toplam_beraberlik,
                "ozel_yetenek_galibiyet": self._kullanici.ozel_yetenek_galibiyet,
                "kalan_enerji": self._kullanici.toplam_kalan_enerji(),
                "max_seviye_kart": self._kullanici.max_seviyeli_kart_sayisi(),
                "seri_sayisi": self._kullanici.toplam_seri_sayisi,
                "moral": self._kullanici.moral,
            },
            "bilgisayar": {
                "ad": self._bilgisayar.oyuncu_adi,
                "skor": self._bilgisayar.skor,
                "galibiyet": self._bilgisayar.toplam_galibiyet,
                "maglubiyet": self._bilgisayar.toplam_maglubiyet,
                "beraberlik": self._bilgisayar.toplam_beraberlik,
                "ozel_yetenek_galibiyet": self._bilgisayar.ozel_yetenek_galibiyet,
                "kalan_enerji": self._bilgisayar.toplam_kalan_enerji(),
                "max_seviye_kart": self._bilgisayar.max_seviyeli_kart_sayisi(),
                "seri_sayisi": self._bilgisayar.toplam_seri_sayisi,
                "moral": self._bilgisayar.moral,
            },
            "istatistik": {
                "toplam_tur": self._istatistik.toplam_tur,
                "atlanan_tur": self._istatistik.atlanan_turlar,
                "tur_gecmisi": self._istatistik.tur_gecmisi,
            },
        }
