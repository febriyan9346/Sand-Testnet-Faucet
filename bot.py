import requests
import time
import os
from datetime import datetime, timedelta

# --- PENGATURAN DEBUG ---
# Ubah menjadi True jika Anda ingin melihat log debug dan SEMUA pesan error
SHOW_DEBUG = False
# -------------------------

# Coba impor colorama untuk output berwarna
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("Modul 'colorama' tidak ditemukan. Menjalankan tanpa warna.")
    print("Silakan install dengan: pip install colorama")
    # Buat class dummy agar skrip tidak error jika colorama tidak ada
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()

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
        print(f"{Fore.RED}❌ Error: File '{filename}' tidak ditemukan.")
        return None
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print(f"{Fore.RED}❌ Error: File '{filename}' kosong.")
            return None
        return lines

def format_proxy(proxy_string):
    """Mengubah format proxy menjadi dictionary yang dimengerti library requests."""
    if not proxy_string:
        return None
    
    proxy_string = proxy_string.strip()
    
    if proxy_string.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
        proxy_url = proxy_string
    else:
        proxy_url = f'http://{proxy_string}'
    
    try:
        if '://' in proxy_url:
            protocol, rest = proxy_url.split('://', 1)
            if not rest:
                raise ValueError("Invalid proxy format")
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        if SHOW_DEBUG:
            print(f"  {Fore.YELLOW}⚠️ Warning: Format proxy tidak valid '{proxy_string}': {e}")
        return None

def solve_captcha(api_key, proxy_dict):
    """Fungsi gabungan untuk menyelesaikan CAPTCHA dan mengembalikan token."""
    print(f"  {Fore.CYAN}↪️ Memulai proses penyelesaian CAPTCHA...")
    
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
    
    if SHOW_DEBUG:
        print(f"  {Style.DIM + Fore.MAGENTA}🔍 DEBUG: Mengirim request ke 2Captcha...")
        print(f"  {Style.DIM + Fore.MAGENTA}🔍 DEBUG: API Key: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        response = requests.post(
            create_task_url, 
            json=payload, 
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if SHOW_DEBUG:
            print(f"  {Style.DIM + Fore.MAGENTA}🔍 DEBUG: Response dari createTask: {data}")
        
        if data.get("errorId") == 0:
            task_id = data.get("taskId")
            if SHOW_DEBUG: # Task ID hanya tampil di mode DEBUG agar lebih bersih
                print(f"  {Fore.GREEN}✔️ Task CAPTCHA dibuat dengan ID: {Style.BRIGHT}{task_id}")
        else:
            if SHOW_DEBUG:
                print(f"  {Fore.RED}❌ Error saat membuat task: {data.get('errorCode')} - {data.get('errorDescription')}")
            return None
            
    except requests.exceptions.RequestException as e:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ Terjadi kesalahan koneksi saat membuat task: {e}")
        return None

    # 2. Get Result
    get_result_url = "https://api.2captcha.com/getTaskResult"
    payload = {"clientKey": api_key, "taskId": task_id}
    max_attempts = 24  # 2 menit maksimal (24 x 5 detik)
    attempts = 0
    
    print(f"  {Fore.YELLOW}⏳ Menunggu hasil dari 2Captcha (max {max_attempts * 5} detik)...")
    
    while attempts < max_attempts:
        try:
            time.sleep(5)
            attempts += 1
            
            if SHOW_DEBUG:
                print(f"  {Style.DIM + Fore.CYAN}🔄 Attempt {attempts}/{max_attempts}: Checking result...")
            
            response = requests.post(
                get_result_url, 
                json=payload, 
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if SHOW_DEBUG:
                print(f"  {Style.DIM + Fore.MAGENTA}🔍 DEBUG: Response attempt {attempts}: {data}")
            
            if data.get("errorId") == 0:
                if data.get("status") == "ready":
                    token = data.get("solution", {}).get("token")
                    print(f"  {Fore.GREEN + Style.BRIGHT}✅ CAPTCHA Berhasil diselesaikan!")
                    if SHOW_DEBUG:
                        print(f"  {Style.DIM + Fore.MAGENTA}🔍 DEBUG: Token length: {len(token) if token else 0}")
                    return token
                elif data.get("status") == "processing":
                    if SHOW_DEBUG:
                        print(f"  {Fore.YELLOW}⏳ Status: processing... ({attempts}/{max_attempts})")
                    continue
                else:
                    if SHOW_DEBUG:
                        print(f"  {Fore.RED}❌ Status task tidak diketahui: {data.get('status')}")
                    return None
            else:
                if SHOW_DEBUG:
                    print(f"  {Fore.RED}❌ Error saat mengambil hasil: {data.get('errorCode')} - {data.get('errorDescription')}")
                return None
                
        except requests.exceptions.Timeout:
            if SHOW_DEBUG:
                print(f"  {Fore.YELLOW}⚠️ Timeout saat mengambil hasil, mencoba lagi...")
            continue
        except requests.exceptions.RequestException as e:
            if SHOW_DEBUG:
                print(f"  {Fore.RED}❌ Terjadi kesalahan koneksi saat mengambil hasil: {e}")
            return None
    
    if SHOW_DEBUG:
        print(f"  {Fore.RED}❌ Timeout: CAPTCHA tidak selesai setelah {max_attempts * 5} detik")
    return None

def request_faucet_funds(address, captcha_token, proxy_dict):
    """Mengirim request ke API faucet. Mengembalikan True jika berhasil, False jika gagal."""
    payload = {
        "json": {
            "rollupSubdomain": "sandbox-testnet",
            "recipientAddress": address,
            "turnstileToken": captcha_token,
            "tokenRollupAddress": None
        },
        "meta": {
            "values": { "tokenRollupAddress": ["undefined"] }
        }
    }
    final_payload = {"0": payload}

    print(f"  {Fore.CYAN}↪️ Mengirim request faucet untuk alamat: {Style.BRIGHT}{address[:10]}...{address[-4:]}")
    
    try:
        response = requests.post(
            FAUCET_API_URL, 
            headers=HEADERS, 
            json=final_payload, 
            proxies=proxy_dict, 
            timeout=45
        )
        response.raise_for_status()
        
        response_data = response.json()
        tx_hash = response_data[0].get("result", {}).get("data", {}).get("json", {}).get("transactionHash")
        
        if tx_hash:
            print(f"  {Fore.GREEN + Style.BRIGHT}✅ BERHASIL! Transaction Hash: {Fore.YELLOW}{tx_hash}")
            return True  # <-- PERBAIKAN LOGIKA
        else:
            if SHOW_DEBUG:
                print(f"  {Fore.RED}❌ GAGAL! Respons tidak dikenali. Respons dari server:")
                print(f"     {Style.DIM}{response_data}")
            
    except requests.exceptions.HTTPError as e:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ GAGAL! HTTP Error: {e.response.status_code}")
            try:
                error_data = e.response.json()
                message = error_data[0]['error']['json']['message']
                print(f"     {Fore.RED}Pesan: {message}")
            except Exception:
                print(f"     {Fore.RED}Respons: {e.response.text[:150]}...")
    
    except requests.exceptions.ProxyError as e:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ GAGAL! Error Proxy: {e}")
    except requests.exceptions.Timeout:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ GAGAL! Request timeout (proxy mungkin terlalu lambat)")
    except requests.exceptions.RequestException as e:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ GAGAL! Terjadi kesalahan koneksi: {e}")
    except ValueError:
        if SHOW_DEBUG:
            print("  {Fore.RED}❌ GAGAL! Tidak bisa mem-parse respons JSON dari server.")
    except Exception as e:
        if SHOW_DEBUG:
            print(f"  {Fore.RED}❌ GAGAL! Error tidak terduga: {e}")

    return False  # <-- PERBAIKAN LOGIKA

def process_all_wallets(api_key, wallets, proxies):
    """Memproses semua wallet sekali jalan."""
    success_count = 0
    failed_count = 0
    
    for i, wallet_address in enumerate(wallets):
        # Pembatas antar wallet
        print(f"\n{Fore.CYAN}{'='*25}[ {i+1}/{len(wallets)} ]{'='*25}")
        print(f"💎 {Style.BRIGHT}Memproses wallet: {Fore.YELLOW}{wallet_address}")
        
        # Memilih dan memformat proxy secara bergiliran
        proxy_dict = None
        if proxies:
            selected_proxy = proxies[i % len(proxies)]
            proxy_dict = format_proxy(selected_proxy)
            
            if proxy_dict:
                display_proxy = selected_proxy.split('@')[-1] if '@' in selected_proxy else selected_proxy
                print(f"  {Fore.BLUE}🌐 Menggunakan proxy untuk faucet request: {Style.BRIGHT}{display_proxy}")
                if SHOW_DEBUG:
                    print(f"  {Style.DIM}💡 Note: 2Captcha API TIDAK menggunakan proxy")

        # 1. Selesaikan Captcha (TANPA PROXY)
        token = solve_captcha(api_key, None)
        
        # 2. Jika dapat token, request faucet (DENGAN PROXY)
        if token:
            # --- PERBAIKAN LOGIKA ---
            # Panggil fungsi DAN simpan hasilnya (True/False)
            is_success = request_faucet_funds(wallet_address, token, proxy_dict)
            
            # Hanya tambah success jika DIBERI TAHU berhasil
            if is_success:
                success_count += 1
            else:
                failed_count += 1
            # --- AKHIR PERBAIKAN ---
        else:
            # Gagal captcha sudah pasti gagal
            if SHOW_DEBUG:
                print(f"  {Fore.RED}❌ Melewati request faucet karena gagal mendapatkan token CAPTCHA.")
            failed_count += 1
        
        if i < len(wallets) - 1:
            print(f"\n{Fore.YELLOW}💤 Jeda 10 detik sebelum lanjut ke wallet berikutnya...")
            time.sleep(10)
    
    return success_count, failed_count


def calculate_next_run_time(interval_hours=24):
    """Menghitung waktu run berikutnya."""
    next_run = datetime.now() + timedelta(hours=interval_hours)
    return next_run


def format_time_remaining(seconds):
    """Format sisa waktu menjadi format yang mudah dibaca."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}j {minutes}m {secs}d"


if __name__ == "__main__":
    
    # Baca konfigurasi
    api_key_list = read_file_lines("2captcha.txt")
    wallets = read_file_lines("wallets.txt")
    proxies = read_file_lines("proxies.txt")

    if not api_key_list or not wallets:
        print(f"\n{Fore.RED}❌ Pastikan file '2captcha.txt' dan 'wallets.txt' ada dan tidak kosong.")
        exit()
    
    API_KEY = api_key_list[0]
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
    print(f"🔍 {Style.BRIGHT}VALIDASI KONFIGURASI")
    print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
    print(f"{Fore.GREEN}✅ API Key 2Captcha: {Style.BRIGHT}{API_KEY[:10]}...{API_KEY[-5:]}")
    print(f"{Fore.GREEN}✅ Total Wallet: {Style.BRIGHT}{len(wallets)}")
    print(f"{Fore.GREEN}✅ Total Proxy: {Style.BRIGHT}{len(proxies) if proxies else 0}")
    
    if not proxies:
        print(f"\n{Fore.YELLOW}⚠️  Peringatan: File 'proxies.txt' tidak ditemukan atau kosong.")
        try:
            use_proxy = input(f"{Fore.YELLOW}Lanjutkan TANPA PROXY? (y/n): {Style.RESET_ALL}").lower()
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}❌ Bot dibatalkan.")
            exit()
        if use_proxy != 'y':
            print(f"{Fore.RED}❌ Bot dibatalkan.")
            exit()
    
    # Tanya mode operasi
    print(f"\n{Fore.CYAN + Style.BRIGHT}{'='*60}")
    print(f"🤖 {Style.BRIGHT}BOT FAUCET AUTO LOOP")
    print(f"{Fore.CYAN + Style.BRIGHT}{'='*60}")
    print("\nPilih mode operasi:")
    print(f"{Style.BRIGHT}1. {Style.RESET_ALL}Sekali jalan (run 1x lalu berhenti)")
    print(f"{Style.BRIGHT}2. {Style.RESET_ALL}Loop 24 jam (otomatis repeat setiap 24 jam)") # <-- PERBAIKAN TYPO
    print(f"{Style.BRIGHT}3. {Style.RESET_ALL}Loop custom (tentukan interval sendiri)")     # <-- PERBAIKAN TYPO
    
    try:
        mode = input(f"\n{Style.BRIGHT}Pilih mode (1/2/3): {Style.RESET_ALL}").strip()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}❌ Bot dibatalkan.")
        exit()
    
    if mode == "1":
        print(f"\n{Fore.GREEN + Style.BRIGHT}🚀 Bot Faucet Dimulai! Total wallet: {len(wallets)}")
        print(f"{Fore.GREEN}{'-' * 50}")
        
        success, failed = process_all_wallets(API_KEY, wallets, proxies)
        
        print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
        print(f"🎉 {Style.BRIGHT}Semua wallet telah selesai diproses!")
        print(f"{Fore.GREEN}✅ Berhasil: {Style.BRIGHT}{success}{Style.RESET_ALL} | {Fore.RED}❌ Gagal: {Style.BRIGHT}{failed}")
        print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
        
    elif mode == "2":
        interval_hours = 24
        run_count = 0
        
        print(f"\n{Fore.CYAN + Style.BRIGHT}🔄 Mode Loop 24 Jam Aktif!")
        print(f"Bot akan berjalan setiap {interval_hours} jam secara otomatis.")
        print("Tekan Ctrl+C untuk menghentikan bot.\n")
        
        try:
            while True:
                run_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
                print(f"🚀 {Style.BRIGHT}RUN #{run_count} - {now}")
                print(f"📊 {Style.BRIGHT}Total wallet: {len(wallets)}")
                print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
                
                success, failed = process_all_wallets(API_KEY, wallets, proxies)
                
                print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
                print(f"✅ {Style.BRIGHT}Run #{run_count} selesai!")
                print(f"{Fore.GREEN}✅ Berhasil: {Style.BRIGHT}{success}{Style.RESET_ALL} | {Fore.RED}❌ Gagal: {Style.BRIGHT}{failed}")
                print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
                
                next_run = calculate_next_run_time(interval_hours)
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                wait_seconds = interval_hours * 3600
                
                print(f"\n{Fore.CYAN}⏰ Next run dijadwalkan pada: {Style.BRIGHT}{next_run_str}")
                print(f"{Fore.CYAN}💤 Menunggu {interval_hours} jam ({wait_seconds} detik)...")
                
                try:
                    for remaining in range(wait_seconds, 0, -60):
                        time_str = format_time_remaining(remaining)
                        print(f"\r{Fore.YELLOW}⏳ Sisa waktu: {Style.BRIGHT}{time_str}{Style.RESET_ALL}   ", end='', flush=True)
                        time.sleep(60)
                    print(f"\r{Fore.GREEN}✅ Waktu tunggu selesai!              ")
                except KeyboardInterrupt:
                    raise
                    
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}⚠️  Bot dihentikan oleh user (Ctrl+C)")
            print(f"📊 Total run yang telah dilakukan: {run_count}")
            print(f"{Fore.CYAN}👋 Terima kasih telah menggunakan bot!")
            
    elif mode == "3":
        try:
            interval_hours_input = input(f"{Style.BRIGHT}Masukkan interval dalam JAM (misal: 12, 6, 0.5): {Style.RESET_ALL}")
            interval_hours = float(interval_hours_input)
            if interval_hours <= 0:
                print(f"{Fore.RED}❌ Interval harus lebih dari 0!")
                exit()
        except ValueError:
            print(f"{Fore.RED}❌ Input tidak valid!")
            exit()
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}❌ Bot dibatalkan.")
            exit()
        
        run_count = 0
        
        print(f"\n{Fore.CYAN + Style.BRIGHT}🔄 Mode Loop Custom Aktif!")
        print(f"Bot akan berjalan setiap {interval_hours} jam secara otomatis.")
        print("Tekan Ctrl+C untuk menghentikan bot.\n")
        
        try:
            while True:
                run_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
                print(f"🚀 {Style.BRIGHT}RUN #{run_count} - {now}")
                print(f"📊 {Style.BRIGHT}Total wallet: {len(wallets)}")
                print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
                
                success, failed = process_all_wallets(API_KEY, wallets, proxies)
                
                print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}")
                print(f"✅ {Style.BRIGHT}Run #{run_count} selesai!")
                print(f"{Fore.GREEN}✅ Berhasil: {Style.BRIGHT}{success}{Style.RESET_ALL} | {Fore.RED}❌ Gagal: {Style.BRIGHT}{failed}")
                print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}")
                
                next_run = calculate_next_run_time(interval_hours)
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                wait_seconds = int(interval_hours * 3600)
                
                print(f"\n{Fore.CYAN}⏰ Next run dijadwalkan pada: {Style.BRIGHT}{next_run_str}")
                print(f"💤 Menunggu {interval_hours} jam ({wait_seconds} detik)...")
                
                try:
                    update_interval = 60 if wait_seconds > 120 else 10
                    for remaining in range(wait_seconds, 0, -update_interval):
                        time_str = format_time_remaining(remaining)
                        print(f"\r{Fore.YELLOW}⏳ Sisa waktu: {Style.BRIGHT}{time_str}{Style.RESET_ALL}   ", end='', flush=True)
                        time.sleep(update_interval)
                    print(f"\r{Fore.GREEN}✅ Waktu tunggu selesai!              ")
                except KeyboardInterrupt:
                    raise
                    
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}⚠️  Bot dihentikan oleh user (Ctrl+C)")
            print(f"📊 Total run yang telah dilakukan: {run_count}")
            print(f"{Fore.CYAN}👋 Terima kasih telah menggunakan bot!")
    
    else:
        print(f"{Fore.RED}❌ Pilihan tidak valid!")
        exit()
