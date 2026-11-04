## Lampiran: prompt pembuka
**Mengisi template ini dengan AI (sebelum coding):**
```text
Isi template PRD ini untuk aplikasi: [deskripsi singkat + referensi + target deploy].
Aturan:
- Isi setiap bagian; jangan tinggalkan [...]. Jika informasi tidak ada, tulis sebagai pertanyaan terbuka di akhir dokumen, jangan dikarang.
- Untuk integrasi pihak ketiga, cari dokumentasi resminya dan salin endpoint, format auth, parameter expiry, API pembatalan, aturan pemanggilan ulang, dan semua status webhook. Cantumkan link sumbernya.
- Isi tabel cek target deploy (bagian 4), tabel siklus hidup, aturan idempotensi, dan balapan timer vs event (bagian 5).
- Gambarkan diagram arsitektur (bagian 4) dan sequence diagram untuk setiap alur yang melibatkan uang, stok/kuota, pihak ketiga, atau multi-tabel (bagian 6), dalam Mermaid yang valid.
- Untuk setiap fitur yang memberi nilai (voucher, reward, poin), tulis pemicu dan batas penyalahgunaannya.
- Pastikan setiap field yang dipakai fitur ada di request API, setiap endpoint jadi baris tabel API, setiap entitas admin punya endpoint lengkap, dan nilai uang/role selalu dihitung server.
- Di akhir, jalankan checklist bagian 12. Untuk SETIAP item yang dicentang, tulis buktinya (bagian/baris yang memenuhinya). Item tanpa bukti jangan dicentang.
- Setelah checklist, lakukan pengecekan silang dan laporkan temuan sebelum menyerahkan PRD:
  (1) Baca ulang semua constraint unique di bagian 5: apakah ada yang bertentangan dengan aturan bisnis atau mengunci limit yang bisa diatur?
  (2) Cocokkan kode status di setiap acceptance criteria dengan tabel API.
  (3) Cari setiap endpoint/halaman yang disebut di fitur tapi tidak ada sebagai baris di bagian 7 atau 8.
  (4) Untuk setiap aksi "kembalikan" (stok, kuota, saldo), telusuri semua jalur: apakah mungkin mengembalikan sesuatu yang tidak pernah dikurangi?
  (5) Untuk setiap batas waktu dan pembatalan, cek: apa yang dilihat user, dan apakah penyedia eksternal ikut tahu?
  (6) Untuk setiap kata "personal", "milik user", atau flag "perlu ...", cek ada kolom pemilik / kolom penyelesaiannya.
```

**Sesi pertama (perencanaan):**
```text
Baca docs/PRD.md. Jangan menulis kode dulu.
1. Sebutkan bagian yang ambigu atau kurang, lalu ajukan pertanyaan.
2. Usulkan struktur folder dan urutan pengerjaan per milestone.
```

**Sesi eksekusi:**
```text
Kerjakan M1 sesuai docs/PRD.md dan aturan di CLAUDE.md.
Tulis tes untuk setiap acceptance criteria, jalankan, dan pastikan lolos.
Update docs/PROGRESS.md di akhir.
```

**Saat ada bug:**
```text
Fitur F-01 gagal: [pesan error / langkah reproduksi].
Cari akar masalahnya dulu dan jelaskan, baru perbaiki. Tambahkan tes regresi.
```
