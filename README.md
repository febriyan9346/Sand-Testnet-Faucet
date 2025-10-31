# 🤖 Sand Testnet Faucet Bot

Bot otomatis untuk claim faucet Sand Testnet dengan fitur multi-wallet, proxy rotation, dan auto-loop 24 jam.

## ✨ Fitur

- ✅ Multi-wallet support (unlimited wallets)
- ✅ Auto solve Cloudflare Turnstile CAPTCHA menggunakan 2Captcha
- ✅ Proxy rotation untuk menghindari rate limit
- ✅ 3 Mode operasi: Sekali jalan, Loop 24 jam, Loop custom
- ✅ Countdown timer untuk next run
- ✅ Error handling yang robust
- ✅ Progress tracking dan logging

## 📋 Persyaratan

- Python 3.7+
- API Key dari [2Captcha](https://2captcha.com/?from=16513392)
- Wallet address (EVM compatible)
- Proxy list (opsional, tapi direkomendasikan)

## 🚀 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/febriyan9346/Sand-Testnet-Faucet.git
cd Sand-Testnet-Faucet
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup File Konfigurasi

Buat 3 file berikut di folder yang sama dengan `bot.py`:

#### `2captcha.txt`
Masukkan API key 2Captcha Anda (satu baris):
```
your_2captcha_api_key_here
```

#### `wallets.txt`
Masukkan wallet address (satu address per baris):
```
0x1234567890abcdef1234567890abcdef12345678
0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
0x9876543210fedcba9876543210fedcba98765432
```

#### `proxies.txt`
Masukkan proxy (satu proxy per baris):

Format yang didukung:
```
ip:port
ip:port:username:password
username:password@ip:port
http://ip:port
http://username:password@ip:port
socks5://ip:port
```

Contoh:
```
123.45.67.89:8080
98.76.54.32:3128:user:pass
user:pass@192.168.1.1:8888
```

## 📖 Cara Menggunakan

### Jalankan Bot

```bash
python bot.py
```

### Pilih Mode Operasi

Setelah menjalankan bot, Anda akan diminta memilih mode:

#### 1️⃣ Mode Sekali Jalan
- Bot akan memproses semua wallet sekali lalu berhenti
- Cocok untuk testing atau claim manual

#### 2️⃣ Mode Loop 24 Jam
- Bot akan berjalan otomatis setiap 24 jam
- Cocok untuk mendapatkan faucet harian secara konsisten

#### 3️⃣ Mode Loop Custom
- Anda bisa menentukan interval sendiri (dalam jam)
- Contoh: 12 jam, 6 jam, 0.5 jam (30 menit)

### Menghentikan Bot

Tekan `Ctrl+C` untuk menghentikan bot dengan aman.

## 💡 Tips Penggunaan

1. **Gunakan Proxy**: Sangat direkomendasikan untuk menghindari rate limit dan block IP
2. **Rotasi Proxy**: Bot akan menggunakan proxy secara bergiliran untuk setiap wallet
3. **Interval Optimal**: Gunakan interval 24 jam untuk hasil terbaik
4. **Monitor Balance**: Cek API Key 2Captcha Anda secara berkala
5. **Testing**: Coba mode "sekali jalan" dulu dengan 1-2 wallet untuk testing

## 📊 Format Output

```
[1/3] Memproses wallet: 0x12345678...
  🌐 Menggunakan proxy: 123.45.67.89:8080
  ↪️ Memulai proses penyelesaian CAPTCHA...
  ✔️ Task CAPTCHA dibuat dengan ID: 12345678
  ⏳ Menunggu hasil dari 2Captcha...
  ✅ CAPTCHA Berhasil diselesaikan!
  ↪️ Mengirim request faucet untuk alamat: 0x12345678...
  ✅ BERHASIL! Transaction Hash: 0xabcdef...
```

## ⚠️ Troubleshooting

### Error: File tidak ditemukan
- Pastikan file `2captcha.txt`, `wallets.txt`, dan `proxies.txt` ada di folder yang sama dengan `bot.py`

### Error: Proxy tidak valid
- Cek format proxy Anda, gunakan salah satu format yang didukung
- Test proxy secara manual di browser atau tools lain

### Error: CAPTCHA timeout
- API Key 2Captcha tidak valid atau balance habis
- Server 2Captcha sedang sibuk, coba lagi nanti

### Error: Request faucet gagal
- Wallet sudah claim dalam 24 jam terakhir
- Network error atau proxy bermasalah
- Coba gunakan proxy lain

## 🔧 Konfigurasi Advanced

Edit file `bot.py` untuk mengubah:

- **CAPTCHA_WEBSITE_URL**: URL website faucet
- **CAPTCHA_WEBSITE_KEY**: Turnstile site key
- **FAUCET_API_URL**: Endpoint API faucet
- **HEADERS**: Custom headers untuk request

## 📝 Struktur File

```
Sand-Testnet-Faucet/
├── bot.py              # Script utama
├── requirements.txt    # Dependencies Python
├── 2captcha.txt       # API key 2Captcha
├── wallets.txt        # Daftar wallet address
├── proxies.txt        # Daftar proxy (opsional)
└── README.md          # Dokumentasi
```

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository ini
2. Buat branch baru (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 Lisensi

Project ini menggunakan lisensi MIT. Lihat file `LICENSE` untuk detail.

## ⚡ Disclaimer

- Bot ini dibuat untuk tujuan edukasi dan testing
- Gunakan dengan bijak dan ikuti ToS dari Sand Testnet
- Tidak bertanggung jawab atas penyalahgunaan bot ini
- Pastikan Anda memiliki izin untuk menggunakan proxy yang Anda gunakan

## 🙏 Credits

- [2Captcha](https://2captcha.com/?from=16513392) - CAPTCHA solving service
- [Sand Testnet](https://sandchain-hub.caldera.xyz/) - Testnet faucet

## 📞 Support

Jika ada pertanyaan atau masalah:
- Buat Issue di GitHub
- Atau hubungi melalui Discord/Telegram (jika tersedia)

---

⭐ Jangan lupa beri star jika project ini bermanfaat!

**Made with ❤️ by Community**