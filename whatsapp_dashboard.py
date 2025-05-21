import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import subprocess
import platform
from pathlib import Path
import cloudinary
import cloudinary.uploader

st.set_page_config(page_title="WA Sender", layout="centered")

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name='ddkqrgb2v',
    api_key='956855212351643',
    api_secret='RbhZ9ct4I4dH_WX7_1Qb339acDw'
)

# --- Judul ---
st.title("\U0001F4F2 Dashboard Blasting Bengkel Version 0.1")
st.markdown("Versi interaktif menggunakan API WA Panel dengan Excel, input manual, dan dukungan gambar.")

# --- Sidebar Settings ---
st.sidebar.image("https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEifCMgTSVQ5XOVA3899Yr4Ae1sA3puuYLe95e0iMVW0QpImq0_LiT1zDEnlgRuhrscLXx_sRJtmVYCaEpT6PhcRvSiSUIoEQZcNUySvcLcnrE3S_F3WT-NV8j6POv34VgPKkVheW-WXUGG78m-d05Zn_uL7jeKw0z8BnQefIQ5oqrxDpUVU_DII7jOq/s1600/LOGO.png", width=180)
st.sidebar.header("\U0001F512 Pengaturan API & Pesan")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "appkey" not in st.session_state:
    st.session_state.appkey = ""
if "authkey" not in st.session_state:
    st.session_state.authkey = ""

if st.session_state.logged_in:
    st.sidebar.success("\U0001F512 Terhubung ke API WA Panel")
    st.sidebar.markdown(f"**App Key:** `{st.session_state.appkey[:4]}***`")
    if st.sidebar.button("\U0001F512 Logout"):
        st.session_state.logged_in = False
        st.session_state.appkey = ""
        st.session_state.authkey = ""
        st.rerun()
else:
    with st.sidebar.form("login_form"):
        appkey_input = st.text_input("App Key", type="password")
        authkey_input = st.text_input("Auth Key", type="password")
        login_submit = st.form_submit_button("\U0001F513 Login")
        if login_submit:
            if appkey_input and authkey_input:
                st.session_state.appkey = appkey_input
                st.session_state.authkey = authkey_input
                st.session_state.logged_in = True
                st.success("✅ Berhasil login ke API.")
                st.rerun()
            else:
                st.warning("App Key dan Auth Key wajib diisi.")

appkey = st.session_state.get("appkey", "")
authkey = st.session_state.get("authkey", "")

message_template = st.sidebar.text_area("✏️ Template Pesan (gunakan {nama})", "Halo {nama}, ini adalah pesan testing dari WA API via Python.")
delay_input = st.sidebar.number_input("⏱️ Jeda antar pesan (detik)", min_value=1, value=5)

# --- Upload Gambar (opsional) ---
st.sidebar.header("🖼️ Pengaturan Gambar (Opsional)")
image_file = st.sidebar.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"])
caption = st.sidebar.text_area("📎 Caption untuk Gambar (gunakan {nama})", "Hai {nama}, ini gambar untukmu.")

# --- Upload Excel ---
st.subheader("📤 Upload File Excel (opsional)")
uploaded_file = st.file_uploader("Unggah file Excel (.xlsx) berisi kolom: Nama, Nomor", type=["xlsx"])
data_excel = pd.DataFrame()

if uploaded_file:
    data_excel = pd.read_excel(uploaded_file)
    if "Nama" not in data_excel.columns or "Nomor" not in data_excel.columns:
        st.error("❌ Kolom wajib: 'Nama', 'Nomor'")
        data_excel = pd.DataFrame()

# --- Input Manual ---
st.subheader("📥 Tambah Nomor Manual")

if "manual_data" not in st.session_state:
    st.session_state.manual_data = []

with st.form("manual_form"):
    col1, col2 = st.columns(2)
    with col1:
        nama_manual = st.text_input("Nama")
    with col2:
        nomor_manual = st.text_input("Nomor (format: 62xxx)")
    submitted = st.form_submit_button("➕ Tambahkan ke Daftar")
    if submitted:
        if nama_manual and nomor_manual:
            st.session_state.manual_data.append({"Nama": nama_manual, "Nomor": nomor_manual})
            st.success(f"✅ Ditambahkan: {nama_manual} ({nomor_manual})")
        else:
            st.warning("Nama dan nomor tidak boleh kosong!")

if st.session_state.manual_data:
    st.write("📋 Data Manual:")
    for i, entry in enumerate(st.session_state.manual_data):
        col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
        with col1:
            new_nama = st.text_input(f"Nama_{i}", value=entry["Nama"], label_visibility="collapsed")
        with col2:
            new_nomor = st.text_input(f"Nomor_{i}", value=entry["Nomor"], label_visibility="collapsed")
        with col3:
            if st.button("💾", key=f"simpan_{i}"):
                st.session_state.manual_data[i]["Nama"] = new_nama
                st.session_state.manual_data[i]["Nomor"] = new_nomor
                st.success(f"✅ Data {new_nama} diperbarui")
        with col4:
            if st.button("❌", key=f"hapus_{i}"):
                st.session_state.manual_data.pop(i)
                st.rerun()

    df_manual = pd.DataFrame(st.session_state.manual_data)
    st.dataframe(df_manual)

    col_reset, col_download = st.columns([1, 3])
    with col_reset:
        if st.button("🔄 Reset Semua Data Manual"):
            st.session_state.manual_data = []
            st.success("✅ Semua data manual telah dihapus")
            st.rerun()
    with col_download:
        if not df_manual.empty:
            csv_manual = df_manual.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Data Manual (CSV)", data=csv_manual, file_name="data_manual.csv", mime="text/csv")
else:
    df_manual = pd.DataFrame()

# Gabungkan data Excel dan Manual
df_all = pd.concat([data_excel, df_manual], ignore_index=True)

# --- Fungsi Kirim Pesan ---
def send_text_message(number, message, appkey, authkey):
    url = "https://app.wapanels.com/api/create-message"
    payload = {
        'appkey': appkey,
        'authkey': authkey,
        'to': number,
        'message': message
    }
    try:
        response = requests.post(url, data=payload)
        return ("✅ Berhasil", response.text) if response.status_code == 200 else ("❌ Gagal", response.text)
    except Exception as e:
        return "❌ Error", str(e)

def send_image_message(number, caption, image_url, appkey, authkey):
    try:
        url = "https://app.wapanels.com/api/create-message"
        payload = {
            'appkey': appkey,
            'authkey': authkey,
            'to': number,
            'message': caption,
            'file': image_url
        }

        response = requests.post(url, data=payload)
        return ("✅ Berhasil", response.text) if response.status_code == 200 else ("❌ Gagal", response.text)

    except Exception as e:
        return "❌ Error", str(e)

# --- Tombol Kirim Pesan ---
if not df_all.empty and st.session_state.logged_in and st.sidebar.button("🚀 Mulai Kirim Pesan"):
    if not appkey or not authkey:
        st.error("❗ App Key dan Auth Key wajib diisi")
    else:
        st.success("Mengirim pesan... Harap tunggu")
        log = []
        terminal_output = st.empty()

        image_url = None
        if image_file:
            with st.spinner("⏫ Mengunggah ke Cloudinary..."):
                result = cloudinary.uploader.upload(image_file, folder="whatsapp_uploads")
                image_url = result.get("secure_url")

        for idx, row in df_all.iterrows():
            nama = str(row['Nama'])
            nomor = str(row['Nomor'])
            personalized_message = message_template.replace("{nama}", nama)
            personalized_caption = caption.replace("{nama}", nama)

            if image_file and image_url:
                status, response_text = send_image_message(nomor, personalized_caption, image_url, appkey, authkey)
                pesan_terkirim = personalized_caption
            else:
                status, response_text = send_text_message(nomor, personalized_message, appkey, authkey)
                pesan_terkirim = personalized_message

            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.append({
                "Waktu": waktu,
                "Nama": nama,
                "Nomor": nomor,
                "Pesan": pesan_terkirim,
                "Status": status,
                "Respon": response_text
            })

            terminal_text = "\n".join(
                [f"[{entry['Waktu']}] {entry['Status']} - {entry['Nama']} ({entry['Nomor']})"
                 for entry in log]
            )
            terminal_output.code(terminal_text, language="bash")
            time.sleep(delay_input)

        log_df = pd.DataFrame(log)
        st.subheader("📊 Log Pengiriman")
        st.dataframe(log_df)
        csv = log_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Log CSV", data=csv, file_name="log_pengiriman.csv", mime="text/csv")

# --- Terminal Interaktif + Eksekusi dosen.sh ---
st.markdown("---")
st.subheader("🖥️ Terminal Interaktif (Deteksi Otomatis OS + Script dosen.sh)")

with st.expander("💻 Terminal & Script Eksternal"):
    current_os = platform.system()
    st.info(f"🧠 Sistem Operasi terdeteksi: **{current_os}**")

    terminal_cmd = st.text_input("Ketik perintah terminal", placeholder="contoh: echo hello, ping google.com")
    run_terminal = st.button("▶️ Jalankan Perintah Terminal")

    if run_terminal and terminal_cmd.strip():
        try:
            if current_os == "Windows":
                result = subprocess.run(terminal_cmd, shell=True, capture_output=True, text=True, timeout=20)
            else:
                result = subprocess.run(["bash", "-c", terminal_cmd], capture_output=True, text=True, timeout=20)

            st.code(result.stdout or "(tidak ada output)", language="bash")
            if result.stderr:
                st.error(result.stderr)
        except subprocess.TimeoutExpired:
            st.error("⏱️ Timeout: Perintah terlalu lama dijalankan.")
        except Exception as e:
            st.error(f"❌ Error menjalankan perintah: {str(e)}")

    st.divider()

    # Jalankan script dosen.sh jika ada
    script_path = Path("dosen.sh")
    if script_path.exists():
        st.success("✅ Script `dosen.sh` ditemukan.")
        if st.button("🐚 Jalankan Script dosen.sh"):
            try:
                result = subprocess.run(["bash", str(script_path)], capture_output=True, text=True, timeout=60)
                st.code(result.stdout or "(tidak ada output)", language="bash")
                if result.stderr:
                    st.error(result.stderr)
            except Exception as e:
                st.error(f"❌ Gagal menjalankan script: {str(e)}")
    else:
        st.warning("⚠️ File `dosen.sh` tidak ditemukan. Pastikan berada di direktori yang sama.")
