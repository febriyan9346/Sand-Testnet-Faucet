import requests
import time
import os

# --- PENGATURAN UTAMA ---
CAPTCHA_WEBSITE_URL = "https://sandchain-hub.caldera.xyz/"
CAPTCHA_WEBSITE_KEY = "0x4AAAAAAASRorjU_k9HAdVc"
FAUCET_API_URL = "https://sandchain-hub.caldera.xyz/api/trpc/faucet.requestFaucetFunds?batch=1"
# -------------------------

# --- HEADERS UNTUK FAUCET API ---
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://sandchain-hub.caldera.xyz",
    "priority": "u=1, i",
    "referer": "https://sandchain-hub.caldera.xyz/",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}
# ---------------------------------

def read_file_lines(filename):
    """Membaca semua baris dari file dan mengembalikannya sebagai list."""
    if not os.path.exists(filename):
        print(f"❌ Error: File '{filename}' tidak ditemukan.")
        return None
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print(f"❌ Error: File '{filename}' kosong.")
            return None
        return lines

def format_proxy(proxy_string):
    """Mengubah format proxy menjadi dictionary yang dimengerti library requests."""
    if not proxy_string:
        return None
    
    # Hapus whitespace yang mungkin ada
    proxy_string = proxy_string.strip()
    
    # Jika sudah ada protocol, gunakan langsung
    if proxy_string.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
        proxy_url = proxy_string
    else:
        # Tambahkan http:// jika belum ada
        proxy_url = f'http://{proxy_string}'
    
    # Validasi format proxy
    try:
        # Test parsing URL
        if '://' in proxy_url:
            protocol, rest = proxy_url.split('://', 1)
            if not rest:
                raise ValueError("Invalid proxy format")
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        print(f"  ⚠️ Warning: Format proxy tidak valid '{proxy_string}': {e}")
        return None

def solve_captcha(api_key, proxy_dict):
    """Fungsi gabungan untuk menyelesaikan CAPTCHA dan mengembalikan token."""
    print("  ↪️ Memulai proses penyelesaian CAPTCHA...")
    
    # 1. Create Task
    create_task_url = "https://api.2captcha.com/createTask"
    payload = {
        "clientKey": api_key,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": CAPTCHA_WEBSITE_URL,
            "websiteKey": CAPTCHA_WEBSITE_KEY
        }
    }
    
    try:
        # Menggunakan proxy jika tersedia
        response = requests.post(
            create_task_url, 
            json=payload, 
            proxies=proxy_dict, 
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("errorId") == 0:
            task_id = data.get("taskId")
            print(f"  ✔️ Task CAPTCHA dibuat dengan ID: {task_id}")
        else:
            print(f"  ❌ Error saat membuat task: {data.get('errorCode')} - {data.get('errorDescription')}")
            return None
            
    except requests.exceptions.ProxyError as e:
        print(f"  ❌ Error Proxy saat membuat task: {e}")
        print(f"  💡 Tip: Periksa format proxy Anda (harus: ip:port atau user:pass@ip:port)")
        return None
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout saat membuat task (mungkin proxy lambat atau tidak merespon)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ GAGAL! Terjadi kesalahan koneksi: {e}")
    except ValueError:
        print("  ❌ GAGAL! Tidak bisa mem-parse respons JSON dari server.")
    except Exception as e:
        print(f"  ❌ GAGAL! Error tidak terduga: {e}")


def test_proxy(proxy_dict):
    """Test apakah proxy berfungsi dengan baik."""
    if not proxy_dict:
        return True  # Tidak ada proxy, skip test
    
    print("  🔍 Testing proxy connection...")
    try:
        response = requests.get(
            "https://api.ipify.org?format=json", 
            proxies=proxy_dict, 
            timeout=10
        )
        if response.status_code == 200:
            ip = response.json().get('ip', 'unknown')
            print(f"  ✅ Proxy berfungsi! IP: {ip}")
            return True
        else:
            print(f"  ⚠️ Proxy merespon dengan status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Proxy test gagal: {e}")
        return False


def process_all_wallets(api_key, wallets, proxies):
    """Memproses semua wallet sekali jalan."""
    success_count = 0
    failed_count = 0
    
    for i, wallet_address in enumerate(wallets):
        print(f"\n[{i+1}/{len(wallets)}] Memproses wallet: {wallet_address}")
        
        # Memilih dan memformat proxy secara bergiliran
        proxy_dict = None
        if proxies:
            selected_proxy = proxies[i % len(proxies)]
            proxy_dict = format_proxy(selected_proxy)
            
            if proxy_dict:
                # Tampilkan proxy yang digunakan (sembunyikan credential jika ada)
                display_proxy = selected_proxy.split('@')[-1] if '@' in selected_proxy else selected_proxy
                print(f"  🌐 Menggunakan proxy: {display_proxy}")
            else:
                print("  ⚠️ Format proxy tidak valid, melanjutkan tanpa proxy...")

        # 1. Selesaikan Captcha
        token = solve_captcha(api_key, proxy_dict)
        
        # 2. Jika dapat token, request faucet
        if token:
            result = request_faucet_funds(wallet_address, token, proxy_dict)
            success_count += 1
        else:
            print("  ❌ Melewati request faucet karena gagal mendapatkan token CAPTCHA.")
            failed_count += 1
        
        if i < len(wallets) - 1:
            print("\n💤 Jeda 10 detik sebelum lanjut ke wallet berikutnya...")
            time.sleep(10)
    
    return success_count, failed_count


def calculate_next_run_time(interval_hours=24):
    """Menghitung waktu run berikutnya."""
    from datetime import datetime, timedelta
    next_run = datetime.now() + timedelta(hours=interval_hours)
    return next_run


def format_time_remaining(seconds):
    """Format sisa waktu menjadi format yang mudah dibaca."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}j {minutes}m {secs}d"


if __name__ == "__main__":
    from datetime import datetime
    
    # Baca konfigurasi
    api_key_list = read_file_lines("2captcha.txt")
    wallets = read_file_lines("wallets.txt")
    proxies = read_file_lines("proxies.txt")

    if not api_key_list or not wallets:
        print("\n❌ Pastikan file '2captcha.txt' dan 'wallets.txt' ada dan tidak kosong.")
        exit()
    
    API_KEY = api_key_list[0]
    
    if not proxies:
        print("⚠️  Peringatan: File 'proxies.txt' tidak ditemukan atau kosong.")
        use_proxy = input("Lanjutkan TANPA PROXY? (y/n): ").lower()
        if use_proxy != 'y':
            print("❌ Bot dibatalkan.")
            exit()
    
    # Tanya mode operasi
    print("\n" + "="*60)
    print("🤖 BOT FAUCET AUTO LOOP")
    print("="*60)
    print("\nPilih mode operasi:")
    print("1. Sekali jalan (run 1x lalu berhenti)")
    print("2. Loop 24 jam (otomatis repeat setiap 24 jam)")
    print("3. Loop custom (tentukan interval sendiri)")
    
    mode = input("\nPilih mode (1/2/3): ").strip()
    
    if mode == "1":
        # Mode sekali jalan
        print(f"\n🚀 Bot Faucet Dimulai! Total wallet: {len(wallets)}")
        print("-" * 50)
        
        success, failed = process_all_wallets(API_KEY, wallets, proxies)
        
        print("\n" + "="*60)
        print("🎉 Semua wallet telah selesai diproses!")
        print(f"✅ Berhasil: {success} | ❌ Gagal: {failed}")
        print("="*60)
        
    elif mode == "2":
        # Mode loop 24 jam
        interval_hours = 24
        run_count = 0
        
        print(f"\n🔄 Mode Loop 24 Jam Aktif!")
        print(f"Bot akan berjalan setiap {interval_hours} jam secara otomatis.")
        print("Tekan Ctrl+C untuk menghentikan bot.\n")
        
        try:
            while True:
                run_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print("\n" + "="*60)
                print(f"🚀 RUN #{run_count} - {now}")
                print(f"📊 Total wallet: {len(wallets)}")
                print("="*60)
                
                success, failed = process_all_wallets(API_KEY, wallets, proxies)
                
                print("\n" + "="*60)
                print(f"✅ Run #{run_count} selesai!")
                print(f"✅ Berhasil: {success} | ❌ Gagal: {failed}")
                print("="*60)
                
                # Hitung waktu next run
                next_run = calculate_next_run_time(interval_hours)
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                wait_seconds = interval_hours * 3600
                
                print(f"\n⏰ Next run dijadwalkan pada: {next_run_str}")
                print(f"💤 Menunggu {interval_hours} jam ({wait_seconds} detik)...")
                print("   (Tekan Ctrl+C untuk menghentikan)")
                
                # Countdown timer
                try:
                    for remaining in range(wait_seconds, 0, -60):
                        time_str = format_time_remaining(remaining)
                        print(f"\r⏳ Sisa waktu: {time_str}   ", end='', flush=True)
                        time.sleep(60)
                    print("\r✅ Waktu tunggu selesai!              ")
                except KeyboardInterrupt:
                    raise
                    
        except KeyboardInterrupt:
            print("\n\n⚠️  Bot dihentikan oleh user (Ctrl+C)")
            print(f"📊 Total run yang telah dilakukan: {run_count}")
            print("👋 Terima kasih telah menggunakan bot!")
            
    elif mode == "3":
        # Mode loop custom
        try:
            interval_hours = float(input("Masukkan interval dalam JAM (misal: 12, 6, 0.5): "))
            if interval_hours <= 0:
                print("❌ Interval harus lebih dari 0!")
                exit()
        except ValueError:
            print("❌ Input tidak valid!")
            exit()
        
        run_count = 0
        
        print(f"\n🔄 Mode Loop Custom Aktif!")
        print(f"Bot akan berjalan setiap {interval_hours} jam secara otomatis.")
        print("Tekan Ctrl+C untuk menghentikan bot.\n")
        
        try:
            while True:
                run_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print("\n" + "="*60)
                print(f"🚀 RUN #{run_count} - {now}")
                print(f"📊 Total wallet: {len(wallets)}")
                print("="*60)
                
                success, failed = process_all_wallets(API_KEY, wallets, proxies)
                
                print("\n" + "="*60)
                print(f"✅ Run #{run_count} selesai!")
                print(f"✅ Berhasil: {success} | ❌ Gagal: {failed}")
                print("="*60)
                
                # Hitung waktu next run
                next_run = calculate_next_run_time(interval_hours)
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                wait_seconds = int(interval_hours * 3600)
                
                print(f"\n⏰ Next run dijadwalkan pada: {next_run_str}")
                print(f"💤 Menunggu {interval_hours} jam ({wait_seconds} detik)...")
                print("   (Tekan Ctrl+C untuk menghentikan)")
                
                # Countdown timer
                try:
                    update_interval = 60 if wait_seconds > 120 else 10
                    for remaining in range(wait_seconds, 0, -update_interval):
                        time_str = format_time_remaining(remaining)
                        print(f"\r⏳ Sisa waktu: {time_str}   ", end='', flush=True)
                        time.sleep(update_interval)
                    print("\r✅ Waktu tunggu selesai!              ")
                except KeyboardInterrupt:
                    raise
                    
        except KeyboardInterrupt:
            print("\n\n⚠️  Bot dihentikan oleh user (Ctrl+C)")
            print(f"📊 Total run yang telah dilakukan: {run_count}")
            print("👋 Terima kasih telah menggunakan bot!")
    
    else:
        print("❌ Pilihan tidak valid!")
        exit()
