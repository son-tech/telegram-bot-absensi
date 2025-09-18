import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import pytz
import os
from geopy.distance import geodesic

# Setel token bot Anda dari variabel lingkungan.
# Ini lebih aman daripada menaruh token langsung di dalam kode.
# Render akan membaca nilai ini dari Environment Variable yang sudah Anda buat.
TOKEN = os.environ.get("TOKEN")

KOORDINAT_KANTOR = (-2.969146, 102.990422)  
# Toleransi jarak dalam meter
TOLERANSI_JARAK = 100 

# Konfigurasi logging agar lebih mudah melacak aktivitas bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan selamat datang saat perintah /start dikirim."""
    user = update.effective_user
    await update.message.reply_html(
        f"Halo, **{user.full_name}**! 👋\n"
        f"Saya adalah Bot Absensi Dinas Pendidikan dan Kebudayaan Kabupaten Sarolangun.\n"
        f"Untuk absensi, silakan ketik perintah /absen."
    )

async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    nama_pegawai = user.full_name
    id_telegram = user.id
    
    # Tentukan zona waktu Indonesia Barat (WIB)
    zona_wib = pytz.timezone('Asia/Jakarta')
    
    # Ambil waktu absensi saat ini dalam zona waktu WIB
    waktu_absen = datetime.now(zona_wib)
    tanggal_absen = waktu_absen.strftime("%Y-%m-%d")
    jam_absen = waktu_absen.strftime("%H:%M:%S")

    # Path untuk file database absensi
    file_path = "data_absensi.txt"

    # Pastikan file database ada. Jika belum, buat file baru.
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("ID Telegram, Nama Pegawai, Tanggal, Jam\n")

    # Tambahkan data absensi ke file
    with open(file_path, 'a') as f:
        f.write(f"{id_telegram}, {nama_pegawai}, {tanggal_absen}, {jam_absen}\n")

    # Kirim konfirmasi kepada pengguna
    await update.message.reply_text(
        f"Terima kasih, {nama_pegawai}! Absensi Anda pada:\n"
        f"🗓 Tanggal: {tanggal_absen}\n"
        f"⏰ Pukul: {jam_absen}\n"
        f"Telah berhasil dicatat."
    )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menanggapi pesan yang tidak dikenal."""
    await update.message.reply_text("Maaf, perintah yang Anda masukkan tidak valid. Silakan gunakan /absen.")

def main() -> None:
    """Fungsi utama untuk menjalankan bot."""
    if not TOKEN:
        logging.error("Token API tidak ditemukan. Pastikan variabel lingkungan 'TOKEN' sudah diatur.")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Tambahkan handler untuk perintah /start dan /absen
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("absen", absen))
    
    # Tambahkan handler untuk pesan yang tidak dikenali
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown))
    
    # Jalankan bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
