import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import os
import pytz
from geopy.distance import geodesic

# Setel token bot Anda dari variabel lingkungan.
TOKEN = os.environ.get("TOKEN")

# Konfigurasi logging agar lebih mudah melacak aktivitas bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Koordinat Kantor Dinas Pendidikan dan Kebudayaan Kabupaten Sarolangun
KOORDINAT_KANTOR = (-2.969146, 102.990422)  
# Toleransi jarak dalam meter
TOLERANSI_JARAK = 100 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan selamat datang saat perintah /start dikirim."""
    user = update.effective_user
    await update.message.reply_html(
        f"Halo, **{user.full_name}**! 👋\n"
        f"Saya adalah Bot Absensi Dinas Pendidikan dan Kebudayaan Kabupaten Sarolangun.\n"
        f"Untuk absensi, silakan ketik perintah /absen."
    )

async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani perintah /absen dan meminta lokasi."""
    await update.message.reply_text(
        "Silakan kirimkan lokasi Anda saat ini. Pastikan Anda berada di sekitar kantor.\n\n"
        "Alamat Kantor: Komplek Perkantoran Pemda Gunung Kembang, Sarolangun, Jambi."
    )

async def proses_lokasi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menerima dan memvalidasi lokasi yang dikirim pengguna."""
    user = update.effective_user
    nama_pegawai = user.full_name
    id_telegram = user.id

    # Ambil koordinat dari pesan pengguna
    lokasi_pegawai = (update.message.location.latitude, update.message.location.longitude)

    # Hitung jarak antara lokasi pegawai dan kantor
    jarak_ke_kantor = geodesic(lokasi_pegawai, KOORDINAT_KANTOR).meters

    if jarak_ke_kantor <= TOLERANSI_JARAK:
        # Jika lokasi valid, catat absensi
        from datetime import datetime
        
        zona_wib = pytz.timezone('Asia/Jakarta')
        waktu_absen = datetime.now(zona_wib)
        tanggal_absen = waktu_absen.strftime("%Y-%m-%d")
        jam_absen = waktu_absen.strftime("%H:%M:%S")

        # Path untuk file database absensi
        file_path = "data_absensi.txt"
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("ID Telegram, Nama Pegawai, Tanggal, Jam, Jarak (m)\n")
        
        with open(file_path, 'a') as f:
            f.write(f"{id_telegram}, {nama_pegawai}, {tanggal_absen}, {jam_absen}, {jarak_ke_kantor:.2f}\n")

        await update.message.reply_text(
            f"Terima kasih, {nama_pegawai}! Absensi Anda berhasil dicatat.\n"
            f"Jarak Anda dari kantor adalah {jarak_ke_kantor:.2f} meter."
        )
    else:
        # Jika lokasi tidak valid, kirim pesan penolakan
        await update.message.reply_text(
            f"Maaf, absensi gagal. Jarak Anda dari kantor terlalu jauh ({jarak_ke_kantor:.2f} meter).\n"
            "Silakan coba lagi setelah berada di lokasi yang ditentukan."
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
    
    # Tambahkan handler untuk pesan lokasi
    application.add_handler(MessageHandler(filters.LOCATION & (~filters.COMMAND), proses_lokasi))

    # Tambahkan handler untuk pesan yang tidak dikenali
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
