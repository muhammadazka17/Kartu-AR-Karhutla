# 🛠 Build dari Source

Panduan untuk membuka proyek Unity dan membuat ulang APK.

## 1. Yang dibutuhkan
| Software | Versi |
|---|---|
| Unity Hub | terbaru |
| Unity Editor | **6000.6.6f1** + modul **Android Build Support** (centang juga *Android SDK & NDK Tools* dan *OpenJDK*) |
| Vuforia Engine | **11.4.4**, file `add-vuforia-package-11-4-4.unitypackage` dari [developer.vuforia.com → Downloads → SDK](https://developer.vuforia.com/downloads/sdk) (perlu login) |
| License key Vuforia | Gratis (Basic), buat di [developer.vuforia.com → Plan & Licenses](https://developer.vuforia.com) |

## 2. Clone repo
```bash
git clone https://github.com/<username>/Kartu-AR-Karhutla.git
```
Atau klik **Code → Download ZIP** lalu ekstrak.

## 3. Pasang paket Vuforia
Paket Vuforia (138 MB) tidak disertakan karena aturan lisensi PTC dan batas ukuran GitHub.

1. Di Unity Hub, pilih **Add → Add project from disk** lalu pilih folder `unity/FireDisasterAR`.
2. Buka proyeknya. Kalau muncul peringatan paket `com.ptc.vuforia.engine` tidak ditemukan, pilih **Continue / Ignore**.
3. Pilih menu **Assets → Import Package → Custom Package…**, pilih `add-vuforia-package-11-4-4.unitypackage`, lalu klik **Import**. Paket akan dipasang otomatis ke folder `Packages/`.
4. Tunggu proses impor dan kompilasi selesai.

## 4. Masukkan license key
Pilih salah satu cara:
- **Lewat Inspector:** buka **Window → Vuforia Configuration**, lalu tempel key ke kolom **App License Key**.
- **Lewat skrip setup:** buka `Assets/Editor/VuSetup.cs`, ganti `PASTE_YOUR_VUFORIA_LICENSE_KEY_HERE` dengan key-mu.

## 5. Setujui Developer Agreement
Pilih **Help → Vuforia Engine → Show Developer Agreement**, lalu klik **Accept**. Tanpa langkah ini, Vuforia tidak akan menyala di APK.

## 6. Build APK
**Cara A, lewat Editor**
1. Pilih **File → Build Profiles → Android**, lalu klik **Switch Platform**.
2. Pastikan urutan scene: `Assets/Scenes/KartuAR.unity` (pertama), lalu `Assets/Scenes/FireAR.unity`.
3. Klik **Build**, lalu pilih lokasi file `.apk`.

**Cara B, lewat command line** (Unity harus dalam keadaan tertutup)
```bat
"C:\Program Files\Unity\Hub\Editor\6000.6.6f1\Editor\Unity.exe" -batchmode -nographics ^
  -projectPath "path\ke\unity\FireDisasterAR" -buildTarget Android ^
  -executeMethod VuSetup.Build -logFile build.log
```
Hasilnya ada di `unity/FireDisasterAR/Builds/FireDisasterAR_Vuforia.apk`.

> `VuSetup.Run` membangun ulang kedua scene, mengatur Vuforia (key, 6 target, ARCore opsional), dan mengatur Player Settings. Jalankan ini kalau scene rusak atau ingin di-reset: ganti `-executeMethod VuSetup.Build` menjadi `-executeMethod VuSetup.Run`.

## 7. Struktur kode penting
| File | Fungsi |
|---|---|
| `Assets/Scripts/Karhutla/KarhutlaManager.cs` | Membuat 6 Image Target dari gambar kartu, mendeteksi kombinasi kartu, dan menjalankan sekuens Pemicu → Dampak → Mitigasi |
| `Assets/Scripts/Karhutla/CardScene.cs` | Konten tiap kartu: skala ke ukuran kartu, level api (menyala/padam), uap air |
| `Assets/Scripts/Karhutla/PemicuActor.cs` | Semburan api orang dan gelombang panas matahari ke kartu sasaran |
| `Assets/Scripts/Karhutla/MitigasiActor.cs` | Truk menyemprot (lintasan parabola) dan helikopter terbang lalu menjatuhkan air |
| `Assets/Scripts/Karhutla/Stream.cs` | Partikel semburan (air, api, panas) dari titik A ke titik B |
| `Assets/Scripts/FireFX.cs` | Membuat partikel api, asap, bara, panas, dan kabut dari titik `FX_*` di model GLB |
| `Assets/Scripts/VuPlacer.cs` | Mode Taruh Bebas (Ground Plane) dan pesan untuk HP yang tidak mendukung |
| `Assets/Editor/VuSetup.cs` | Setup otomatis scene, konfigurasi Vuforia, Player Settings, dan build |

## 8. Menambah kartu baru
1. Siapkan gambar kartu yang kaya detail (hindari area polos yang luas). Simpan di `Assets/Cards/`.
2. Buat prefab kartu di `Assets/Prefabs/Cards/` berisi komponen `CardScene` (isi `cardId`, `category`, `title`, `info`), anak objek `Content`, dan aktor (`PemicuActor` / `MitigasiActor`) jika perlu.
3. Tambahkan entri baru (id, gambar, prefab) di komponen **KarhutlaManager** pada scene `KartuAR`.
