---
title: MD Viewer TY'ye Hoş Geldin
---

# MD Viewer TY'ye Hoş Geldin

MD Viewer TY, Markdown belgelerini **okumak için** tasarlanmış bir görüntüleyici. Düzenleyici değil, editör değil — sadece sen ve metin. Her şey tek bir amaca hizmet ediyor: okumayı kolaylaştırmak ve okumaya devam etme isteğini canlı tutmak.

Bu belgeyi okurken yukarıdaki çubuğa bir göz at: kaç dakikan kaldığını ve ne kadarını bitirdiğini orada görebilirsin.

## Okumayı kolaylaştıran ayrıntılar

İyi bir okuma deneyimi çoğu zaman fark edilmeyen kararlardan oluşur. MD Viewer TY'de bunların hepsi önceden düşünüldü:

- **Satır uzunluğu** yaklaşık 68 karakterle sınırlı. Göz satır sonundan bir sonrakinin başına kaybolmadan döner.
- **Satır aralığı** cömert tutuldu; paragraflar nefes alır.
- **Sitka Text** varsayılan yazı tipi. Microsoft'un ekranda okunabilirlik için özel olarak tasarladığı bir aile.
- Bölüm başlıkları **İçindekiler** panelinde, her bölümün tahmini okuma süresiyle birlikte listelenir.

> İyi tipografi görünmezdir. Okuyan onu fark etmez, sadece okumaya devam eder.

### Görünümü kendine göre ayarla

Sağ üstteki **Aa** düğmesi görünüm panelini açar. Dört tema var: *Kâğıt*, *Sepya*, *Gece* ve tamamen siyah *Mürekkep*. Yazı boyutunu, satır genişliğini ve satır aralığını da buradan değiştirebilirsin. Ayarların hatırlanır.

> [!TIP]
> Uzun okumalarda **Sepya** tema göz yorgunluğunu azaltır. Gece okuyorsan **Mürekkep** temasını dene.

## Odaklanmana yardım eden modlar

Bazen dikkat dağılır. MD Viewer TY'de üç yardımcı mod var; hepsini tek tuşla açıp kapatabilirsin.

### Odak modu — `F`

Ekranın ortasındaki paragraf dışındaki her şey soluklaşır. Gözün nereye bakacağını düşünmek zorunda kalmaz. Şu an deneyebilirsin: **F** tuşuna bas ve sayfayı yavaşça kaydır.

### Okuma cetveli — `R`

Fareyi takip eden yumuşak bir yatay şerit. Özellikle yoğun metinlerde hangi satırda olduğunu kaybetmeni engeller.

### Hızlı okuma — `B`

Her kelimenin ilk yarısı kalınlaşır. Göz kelimenin başını görünce geri kalanını tamamlar ve metin üzerinde daha hızlı kayar. Herkese uymayabilir; bir dene, beğenmezsen tekrar **B**'ye bas.

> [!NOTE]
> Bu üç mod birlikte de kullanılabilir, ama genellikle biri yeterlidir.

## Kaldığın yerden devam et

MD Viewer TY her belgede nerede kaldığını hatırlar. Bir belgeyi yarım bırakıp kapatsan bile, tekrar açtığında tam o noktaya döner. Başlangıç ekranındaki **son belgeler** listesi de her belgenin yüzde kaçını okuduğunu ve kaç dakikan kaldığını gösterir.

Küçük bir ilerleme çubuğu bile insana "bitireyim şunu" dedirtir.

## Teknik belgeler de güzel görünür

Kod blokları sözdizimi renklendirmesiyle gelir ve tek tıkla kopyalanabilir:

```python
from pathlib import Path

def kelime_say(dosya: Path) -> int:
    """Bir Markdown dosyasındaki kelimeleri sayar."""
    metin = dosya.read_text(encoding="utf-8")
    return len(metin.split())

print(kelime_say(Path("hosgeldin.md")))
```

Tablolar sade ve okunaklıdır:

| Kısayol | İşlev | Not |
|---|---|---|
| `Ctrl` + `O` | Dosya aç | Sürükle-bırak da çalışır |
| `Ctrl` + `F` | Belgede ara | Enter ile sonraki sonuç |
| `N` / `P` | Sonraki / önceki bölüm | Uzun belgelerde çok işe yarar |
| `T` | Temayı değiştir | Dört tema arasında döner |
| `Ctrl` + `+` / `−` | Yazı boyutu | `Ctrl` + `0` sıfırlar |

Yapılacaklar listeleri de desteklenir:

- [x] Belgeyi aç
- [x] Temayı seç
- [ ] Sonuna kadar oku

> [!WARNING]
> Belgeyi başka bir programda düzenlersen MD Viewer TY değişikliği algılar ve sayfayı kaldığın yerde kalarak yeniler.

---

## Son söz

MD Viewer TY, okuduğun her belgeye biraz daha özen göstermek için var. Yeni bir belge açmak için `Ctrl` + `O` tuşlarına bas ya da bir `.md` dosyasını pencereye sürükle.

İyi okumalar.
