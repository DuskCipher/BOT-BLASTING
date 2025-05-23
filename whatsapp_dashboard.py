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
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
from streamlit_option_menu import option_menu

st.set_page_config(page_title="WA Sender", layout="wide")

# --- Inisialisasi session_state jika belum ada ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "appkey" not in st.session_state:
    st.session_state.appkey = ""
if "authkey" not in st.session_state:
    st.session_state.authkey = ""
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame()
if "manual_data" not in st.session_state:
    st.session_state.manual_data = []
if "data_excel" not in st.session_state:
    st.session_state.data_excel = pd.DataFrame()

# --- Fungsi Kirim Pesan (didefinisikan di atas agar tidak error) ---
def send_text_message(number, message, appkey, authkey):
    url = "https://app.wapanels.com/api/create-message"
    payload = {'appkey': appkey, 'authkey': authkey, 'to': number, 'message': message}
    try:
        response = requests.post(url, data=payload)
        return ("✅ Berhasil", response.text) if response.status_code == 200 else ("❌ Gagal", response.text)
    except Exception as e:
        return "❌ Error", str(e)

def send_image_message(number, caption, image_url, appkey, authkey):
    url = "https://app.wapanels.com/api/create-message"
    payload = {'appkey': appkey, 'authkey': authkey, 'to': number, 'message': caption, 'file': image_url}
    try:
        response = requests.post(url, data=payload)
        return ("✅ Berhasil", response.text) if response.status_code == 200 else ("❌ Gagal", response.text)
    except Exception as e:
        return "❌ Error", str(e)

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name='ddkqrgb2v',
    api_key='956855212351643',
    api_secret='RbhZ9ct4I4dH_WX7_1Qb339acDw'
)

# --- Halaman Login Modern ---
if not st.session_state.logged_in:
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='color:#FFA500;'>🔐 Login ke Dashboard</h1>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        appkey_input = st.text_input("🗝️ App Key", type="password", placeholder="Masukkan App Key")
        authkey_input = st.text_input("🔐 Auth Key", type="password", placeholder="Masukkan Auth Key")
        login_submit = st.form_submit_button("🚀 Masuk")
        if login_submit:
            if appkey_input and authkey_input:
                st.session_state.appkey = appkey_input
                st.session_state.authkey = authkey_input
                st.session_state.logged_in = True
                st.toast("Selamat datang kembali, Admin 👋")
                st.success("Login berhasil! Memuat dashboard...")
                st.rerun()
            else:
                st.error("❌ Mohon masukkan App Key dan Auth Key dengan benar.")

    st.markdown("""
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- Menu Bar Modern dengan Logout ---
with st.sidebar:
    menu = option_menu(
        "Dashboard Panel",
        ["Pengaturan & Input", "Kirim Pesan", "Analisis Pengiriman", "Terminal", "🔒 Logout"],
        icons=["gear", "send", "bar-chart", "terminal", "box-arrow-right"],
        menu_icon="chat-dots",
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#1E1E1E"},
            "icon": {"color": "#FFA500", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#333333",
                "color": "#CCCCCC",
            },
            "nav-link-selected": {
                "background-color": "#FFA500",
                "color": "black",
                "font-weight": "bold"
            },
        }
    )

    if menu == "🔒 Logout":
        st.session_state.logged_in = False
        st.session_state.appkey = ""
        st.session_state.authkey = ""
        st.success("✅ Logout berhasil! Sampai jumpa.")
        st.rerun()

st.title("📱 Dashboard Blasting Bengkel Version 0.2 Beta")
st.markdown("Versi interaktif menggunakan API WA Panel dengan Excel, input manual, dan dukungan gambar.")

# --- Konten Menu --
if menu == "Pengaturan & Input":
    st.subheader("📝 Pengaturan Pesan")
    st.session_state.message_template = st.text_area("✏️ Template Pesan (gunakan {nama})", "Halo {nama}, ini adalah pesan testing dari WA API via Python.")
    st.session_state.delay_input = st.number_input("⏱️ Jeda antar pesan (detik)", min_value=1, value=5)

    st.subheader("🖼️ Upload Gambar (Opsional)")
    st.session_state.image_file = st.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"])
    st.session_state.caption = st.text_area("📎 Caption untuk Gambar (gunakan {nama})", "Hai {nama}, ini gambar untukmu.")

    st.subheader("📤 Upload File Excel")
    uploaded_file = st.file_uploader("Unggah file Excel (.xlsx) berisi kolom: Nama, Nomor", type=["xlsx"])
    if uploaded_file:
        st.session_state.data_excel = pd.read_excel(uploaded_file)

    st.subheader("📥 Tambah Nomor Manual")
    with st.form("manual_form"):
        nama_manual = st.text_input("Nama")
        nomor_manual = st.text_input("Nomor (format: 62xxx)")
        if st.form_submit_button("➕ Tambahkan") and nama_manual and nomor_manual:
            st.session_state.manual_data.append({"Nama": nama_manual, "Nomor": nomor_manual})
            st.success("✅ Ditambahkan")

    if st.session_state.manual_data:
        df_manual = pd.DataFrame(st.session_state.manual_data)
        st.dataframe(df_manual)
        csv_manual = df_manual.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Manual CSV", csv_manual, "data_manual.csv", "text/csv")

elif menu == "Kirim Pesan":
    data_excel = st.session_state.get("data_excel", pd.DataFrame())
    df_all = pd.concat([data_excel, pd.DataFrame(st.session_state.manual_data)], ignore_index=True)
    
    if not df_all.empty:
        st.warning("⚠️ Jangan berpindah tab selama proses pengiriman berlangsung. Tetap di halaman ini sampai semua pesan selesai dikirim!")
        st.subheader("🚀 Kirim Pesan Otomatis")
        if st.button("📨 Mulai Kirim Pesan"):
            with st.spinner("Mengirim pesan..."):
                log = []
                image_url = None
                image_file = st.session_state.get("image_file")

                if image_file:
                    upload_result = cloudinary.uploader.upload(image_file, folder="whatsapp_uploads")
                    image_url = upload_result.get("secure_url")

                progress_bar = st.progress(0, text="Memulai pengiriman...")
                total = len(df_all)

                for idx, row in df_all.iterrows():
                    nama, nomor = row["Nama"], row["Nomor"]
                    msg = st.session_state.message_template.replace("{nama}", nama)
                    cap = st.session_state.caption.replace("{nama}", nama)

                    if image_file and image_url:
                        status, _ = send_image_message(nomor, cap, image_url, st.session_state.appkey, st.session_state.authkey)
                        pesan = cap
                    else:
                        status, _ = send_text_message(nomor, msg, st.session_state.appkey, st.session_state.authkey)
                        pesan = msg

                    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Tampilkan status langsung dalam style warna
                    icon = "✅" if "✅" in status else "❌"
                    warna_status = "#22c55e" if "✅" in status else "#ef4444"
                    warna_waktu = "#9ca3af"

                    st.markdown(
                        f"""
                        <div style="
                            background: #262626;
                            border-left: 5px solid {warna_status};
                            padding: 10px 15px;
                            margin: 8px 0;
                            border-radius: 10px;
                            font-family: 'Segoe UI', sans-serif;
                            color: white;
                            box-shadow: 0 0 5px rgba(0,0,0,0.2);
                        ">
                            <div style="color: {warna_waktu}; font-size: 13px;">🕒 {waktu}</div>
                            <div style="margin-top: 5px;">
                                <span style="color: {warna_status}; font-weight: bold; font-size: 15px;">{icon} {status.split()[-1]}</span>
                                <span style="color: #e5e7eb; font-size: 15px;"> ke <strong>{nama}</strong> (<code>{nomor}</code>)</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    log.append({
                        "Waktu": waktu,
                        "Nama": nama,
                        "Nomor": nomor,
                        "Pesan": pesan,
                        "Status": "✅ Berhasil" if "✅" in status else "❌ Gagal"
                    })

                    progress_bar.progress((idx + 1) / total, text=f"{int((idx + 1) / total * 100)}% selesai")
                    time.sleep(st.session_state.delay_input)

                st.session_state.log_df = pd.DataFrame(log)
                st.success("✅ Semua pesan telah dikirim!")

                # Tampilkan log sebagai tabel
                st.subheader("📋 Log Pengiriman")
                styled_log = st.session_state.log_df.style.applymap(
                    lambda x: "color: green;" if x == "✅ Berhasil" else "color: red;", subset=["Status"]
                )
                st.dataframe(styled_log, use_container_width=True)

                # Tombol download
                csv_log = st.session_state.log_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Log CSV", data=csv_log, file_name="log_pengiriman.csv", mime="text/csv")
    else:
        st.warning("⚠️ Data kosong. Silakan upload file Excel atau masukkan nomor manual terlebih dahulu.")

elif menu == "Analisis Pengiriman":
    log_df = st.session_state.log_df

    if log_df.empty:
        st.warning("⚠️ Belum ada data pengiriman untuk dianalisis.")
    else:
        st.subheader("📊 Ringkasan Statistik Pengiriman")

        berhasil = sum(log_df['Status'].str.contains("✅"))
        gagal = sum(log_df['Status'].str.contains("❌"))
        total = len(log_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("📨 Total Pesan", total)
        col2.metric("✅ Berhasil", berhasil, delta_color="normal")
        col3.metric("❌ Gagal", gagal, delta_color="inverse")

        st.divider()

        st.subheader("📊 Grafik Bar: Jumlah Berhasil vs Gagal")
        fig_bar = go.Figure(data=[
            go.Bar(
                x=["Berhasil", "Gagal"],
                y=[berhasil, gagal],
                marker_color=["#22c55e", "#ef4444"],
                text=[berhasil, gagal],
                textposition="auto"
            )
        ])
        fig_bar.update_layout(plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="white")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("🥧 Diagram Pie")
        pie_fig = px.pie(
            names=["Berhasil", "Gagal"],
            values=[berhasil, gagal],
            color_discrete_sequence=["#22c55e", "#ef4444"],
            hole=0.4
        )
        pie_fig.update_layout(paper_bgcolor="#111111", font_color="white")
        st.plotly_chart(pie_fig, use_container_width=True)

        st.subheader("⏱️ Timeline Pengiriman")
        log_df['Waktu'] = pd.to_datetime(log_df['Waktu'])
        fig_time = px.scatter(
            log_df,
            x="Waktu",
            y="Status",
            color="Status",
            hover_data=["Nama", "Nomor"],
            color_discrete_map={
                "✅ Berhasil": "#22c55e",
                "❌ Gagal": "#ef4444"
            }
        )
        fig_time.update_layout(paper_bgcolor="#111111", font_color="white")
        st.plotly_chart(fig_time, use_container_width=True)

        st.subheader("📁 Unduh Data Log")
        col_csv, col_pdf = st.columns(2)

        with col_csv:
            csv = log_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", data=csv, file_name="log_pengiriman.csv", mime="text/csv", use_container_width=True)

        with col_pdf:
            if st.button("📄 Generate PDF Laporan", use_container_width=True):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Laporan Pengiriman WA", ln=True, align='C')
                pdf.ln(10)
                for idx, row in log_df.iterrows():
                    pdf.multi_cell(0, 10, txt=f"[{row['Waktu']}] {row['Status']} - {row['Nama']} ({row['Nomor']})", align='L')
                pdf_output = "laporan_pengiriman.pdf"
                pdf.output(pdf_output)
                with open(pdf_output, "rb") as f:
                    st.download_button("⬇️ Download PDF", data=f.read(), file_name=pdf_output, mime="application/pdf", use_container_width=True)

elif menu == "Terminal":
    st.subheader("🖥️ Terminal Interaktif (Deteksi Otomatis OS + Script dosen.sh)")
    current_os = platform.system()
    st.info(f"🧠 Sistem Operasi terdeteksi: **{current_os}**")
    terminal_cmd = st.text_input("Ketik perintah terminal")
    if st.button("▶️ Jalankan") and terminal_cmd:
        try:
            if current_os == "Windows":
                result = subprocess.run(terminal_cmd, shell=True, capture_output=True, text=True, timeout=20)
            else:
                result = subprocess.run(["bash", "-c", terminal_cmd], capture_output=True, text=True, timeout=20)
            st.code(result.stdout or "(tidak ada output)", language="bash")
            if result.stderr:
                st.error(result.stderr)
        except subprocess.TimeoutExpired:
            st.error("⏱️ Timeout")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    st.divider()
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
        st.warning("⚠️ File `dosen.sh` tidak ditemukan.")
