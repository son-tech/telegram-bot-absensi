import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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
KOORDINAT_KANTOR = (-2.313252, 102.747310)
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
    """Menangani perintah /absen dan menampilkan tombol untuk mendapatkan lokasi."""
    # Membuat tombol "Dapatkan Lokasi"
    keyboard = [[KeyboardButton("Dapatkan Lokasi", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Silakan tekan tombol di bawah untuk membagikan lokasi Anda saat ini.",
        reply_markup=reply_markup
    )

async def proses_lokasi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menerima lokasi, memvalidasi, dan menampilkan tombol Absen."""
    user = update.effective_user

    # Hapus tombol "Dapatkan Lokasi" dari tampilan
    await update.message.reply_text(
        "Mengecek lokasi Anda...",
        reply_markup=ReplyKeyboardRemove()
    )

    lokasi_pegawai = (update.message.location.latitude, update.message.location.longitude)

    # Simpan lokasi dan ID pengguna di context.user_data
    context.user_data['lokasi'] = lokasi_pegawai
    context.user_data['id'] = user.id

    jarak_ke_kantor = geodesic(lokasi_pegawai, KOORDINAT_KANTOR).meters

    if jarak_ke_kantor <= TOLERANSI_JARAK:
        # Tampilkan tombol Absen
        await update.message.reply_text(
            f"Lokasi Anda diterima. Jarak Anda dari kantor: {jarak_ke_kantor:.2f} meter.\n\n"
            "Sekarang, silakan tekan tombol **Absen** untuk mengonfirmasi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Absen", callback_data='absen_sekarang')]])
        )
    else:
        await update.message.reply_text(
            f"Maaf, absensi gagal. Jarak Anda dari kantor terlalu jauh ({jarak_ke_kantor:.2f} meter).\n"
            "Silakan coba lagi setelah berada di lokasi yang ditentukan."
        )

async def absen_sekarang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani absensi final setelah tombol Absen ditekan."""
    query = update.callback_query
    await query.answer()

    # Ambil data lokasi dan ID dari user_data
    lokasi_pegawai = context.user_data.get('lokasi')
    id_telegram = context.user_data.get('id')

    if not lokasi_pegawai or not id_telegram:
        await query.edit_message_text("Maaf, data lokasi tidak ditemukan. Silakan mulai ulang absensi dengan /absen.")
        return

    # Lakukan pencatatan absensi
    user = update.effective_user
    nama_pegawai = user.full_name

    zona_wib = pytz.timezone('Asia/Jakarta')
    waktu_absen = datetime.now(zona_wib)
    tanggal_absen = waktu_absen.strftime("%Y-%m-%d")
    jam_absen = waktu_absen.strftime("%H:%M:%S")

    jarak_ke_kantor = geodesic(lokasi_pegawai, KOORDINAT_KANTOR).meters

    file_path = "data_absensi.txt"
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("ID Telegram, Nama Pegawai, Tanggal, Jam, Jarak (m)\n")

    with open(file_path, 'a') as f:
        f.write(f"{id_telegram}, {nama_pegawai}, {tanggal_absen}, {jam_absen}, {jarak_ke_kantor:.2f}\n")

    await query.edit_message_text(
        f"Terima kasih, {nama_pegawai}! Absensi Anda berhasil dicatat.\n"
        f"Jarak Anda dari kantor adalah {jarak_ke_kantor:.2f} meter."
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

    # Tambahkan handler untuk pesan lokasi dan batasi agar tidak memproses lokasi yang disertai teks
    application.add_handler(MessageHandler(filters.LOCATION & (~filters.TEXT), proses_lokasi))

    # Tambahkan handler untuk Callback Query dari tombol "Absen"
    application.add_handler(CallbackQueryHandler(absen_sekarang, pattern='^absen_sekarang$'))

    # Tambahkan handler untuk pesan yang tidak dikenali
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
