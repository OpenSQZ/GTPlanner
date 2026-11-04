# PRD: {{PRODUCT_NAME}}
{{DATE}} · Template PRD Full Stack untuk AI Coding (Starter Next JS)

## Cara pakai
PRD untuk AI bukan dokumen bisnis, tapi spesifikasi yang bisa dieksekusi: setiap kalimat harus bisa diubah jadi kode atau tes tanpa AI menebak.

- **Eksplisit, bukan implisit.** Tulis nama tabel, nama field, tipe data, dan nama route. Hal yang tidak ditulis akan dikarang AI.
- **Acceptance criteria = definisi selesai.** Format Given/When/Then supaya AI bisa langsung menulis tes.
- **Batasi scope.** Bagian "Out of scope" mencegah AI menambah fitur yang tidak diminta.
- **Pecah per milestone.** Minta AI mengerjakan satu milestone, verifikasi, lalu lanjut. Jangan "bikin semuanya" sekaligus.
- **Simpan sebagai file di repo.** Taruh di `docs/PRD.md`, dan aturan agent (bagian 11) di `CLAUDE.md` / `AGENTS.md` / `.cursorrules` agar selalu terbaca.
- **Gunakan ID.** Beri ID ke fitur (F-01) dan aturan bisnis (BR-01) supaya bisa dirujuk di prompt: "kerjakan F-03".

Hapus bagian yang tidak relevan; jangan biarkan placeholder [...] tersisa saat diberikan ke AI.

## 0. Setup proyek: template Starter Next JS (NgodingPakeAI)
Jalankan ini sebelum mengisi PRD. Salin blok di bawah sebagai prompt pertama ke AI agent di folder kosong; setelah aplikasi jalan, agent berhenti dan PRD ini dipakai untuk sesi berikutnya.

```text
Install dan jalankan template "Starter Next JS" (NgodingPakeAI) di komputer ini.
Folder yang sedang dibuka harus KOSONG (folder editor seperti .claude/.cursor boleh ada).
User mungkin belum pernah menjalankan proyek — jelaskan tiap langkah dengan bahasa sederhana.

Prasyarat: Node.js (cek `node -v`). CLI otomatis ter-download saat dijalankan
via npx — tidak perlu install manual. (Opsional biar lebih cepat: `npm i -g ngodingpakeai`.)

Langkah 1 — unduh source template (sekali saja):
npx ngodingpakeai@latest create --local --token {{NGODINGPAKEAI_TOKEN}} --api-url https://www.ngodingpakeai.com
Perintah ini mengunduh source dan membuat commit git pertama. Kalau folder ternyata tidak
kosong, CLI membuat subfolder dan memberitahumu — buka folder itu. Instalasi ini tidak
memerlukan proyek, workspace, atau plan NgodingPakeAI. JANGAN meminta nama proyek atau
Plan ID, dan jangan menjalankan `login`, `connect`, `bootstrap`, atau `sync`.
Token ini hanya untuk mengunduh template ini; kalau CLI menolak, berhenti dan lapor.

Langkah 2 — jalankan aplikasinya, dalam giliran yang sama:
Baca AGENTS.md dan skill setup bawaan template (mis. .agents/skills/starter-setup/SKILL.md),
lalu ikuti: install dependency, siapkan database lokal, nyalakan dev server, dan pastikan
URL-nya benar-benar merespons. Jangan minta user memilih database/provider, membuat password,
atau menyalin file env — template sudah menyiapkan semuanya. Kalau ada prasyarat yang butuh
tindakan user (mis. menyalakan Docker Desktop), sebutkan persis apa yang harus diklik.

Langkah 3 — lapor ke user:
- URL aplikasi lokal dan cara membuat akun pertama.
- Lokasi folder template dan hasil pengecekan aplikasi.
Setelah aplikasi berjalan, SELESAI. Jangan membuat PRD, mengambil task, atau menghubungkan
repo ke NgodingPakeAI kecuali user memintanya.
```

Setelah setup selesai, isi bagian 4 (tech stack) dengan apa yang tertulis di `AGENTS.md` template, bukan pilihan sendiri. PRD ini menambah fitur di atas template; jangan minta AI membangun ulang auth, layout, atau setup database yang sudah disediakan.

> **Penting:** bagian 0 berisi token. Hapus bagian ini dari salinan `docs/PRD.md` yang masuk repo, supaya token tidak ikut ter-commit ke git. (Tombol "Download untuk repo" di GTPlanner sudah otomatis menghapusnya.)

