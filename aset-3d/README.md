# 🧱 Aset 3D: Fire & Disaster Pack

Semua aset dimodelkan secara procedural di **Blender 5.2** (Cycles).

## Isi folder
| Folder / file | Keterangan |
|---|---|
| `blender/Fire_Disaster_Asset_Pack.blend` | File master: semua aset, material procedural (tanpa tekstur eksternal), efek api volumetrik, kamera preview. Setiap aset sudah ditandai **Asset** sehingga muncul di Asset Browser. |
| `glb/*.glb` | Versi siap-AR atau game: geometri digabung dan dioptimasi, tekstur PBR di-bake (Base Color, Roughness, Metallic, Normal, Emission). Titik efek disimpan sebagai node `FX_fire_*`, `FX_smoke_*`, `FX_embers_*`, `FX_heat_*`, sedangkan bagian bergerak sebagai `ROTOR_main`, `ROTOR_tail`, `SUN`, dan titik semburan `NODE_*`. |
| `blender-scripts/*.py` | Skrip pembuat aset (procedural). |

## Daftar aset
| GLB | Aset | Detail |
|---|---|---|
| `truck.glb` | Mobil pemadam kebakaran | Kabin ganda + interior, roda dual dengan tapak ban, rolling door, panel pompa, tangga, gulungan selang, lampu sirene, meriam air |
| `heli.glb` | Helikopter water bombing | Rotor utama dan rotor ekor terpisah (bisa berputar), *bambi bucket* |
| `person.glb` | Karakter penyembur api | Karakter orisinal dengan tangki punggung dan flamethrower |
| `weather.glb` | Cuaca ekstrem | Tanah retak, pohon meranggas, rumput kering, matahari |
| `house.glb` | Rumah kayu terbakar | Papan lap-siding, jendela pecah, atap sirap berlubang, teras, cerobong batu |
| `ruin.glb` | Reruntuhan rumah batu | Dinding bergerigi, balok hangus, tumpukan puing |
| `tree.glb`, `deadtree.glb` | Pohon terbakar, pohon mati | Batang procedural bercabang |
| `brush.glb` | Semak dan rumput terbakar | |
| `rocks.glb`, `log.glb`, `ground.glb` | Batu, kayu gelondong, tanah hangus berisi bara | |

## Memakai skrip procedural
Skrip di `blender-scripts/` dirancang untuk dijalankan dari Blender:
1. Buka Blender, masuk ke tab **Scripting**.
2. Jalankan perintah ini di Python Console (sesuaikan path):
   ```python
   import sys; sys.path.insert(0, r"C:\path\ke\aset-3d\blender-scripts")
   import build_truck   # membangun ulang mobil pemadam di scene aktif
   ```
3. Modul lainnya: `build_house`, `build_ruin`, `build_nature`, `build_heli`, `build_person`, `build_weather`. Untuk ekspor GLB siap-AR: `import ar_export; ar_export.export_asset("truck")`.
