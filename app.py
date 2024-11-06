import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Batas total ukuran file 200 MB

# Pastikan folder upload ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def ambil_nilai_dari_kata_kunci(file_content, keyword):
    pattern = rf"{keyword}\s*([\d,.]+)"
    match = re.search(pattern, file_content)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

def cek_keberadaan_non_tunai(file_content):
    return "NON TUNAI :" in file_content

@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        files = request.files.getlist("file")
        if len(files) == 0:
            return "Tidak ada file yang diunggah.", 400

        total_semua_file = 0
        file_results = []

        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Abaikan file jika mengandung "NON TUNAI :"
                if cek_keberadaan_non_tunai(content):
                    file_results.append({
                        "filename": filename,
                        "total_value": None,
                        "non_tunai_exists": True,
                        "ambil_tunai_value": None,
                        "final_value": None
                    })
                    continue  # Langsung ke file berikutnya

                # Mengambil nilai dari "TOTAL :"
                total_value = ambil_nilai_dari_kata_kunci(content, "TOTAL :")
                
                # Jika "AMBIL TUNAI :" ada, kurangi nilainya dari total
                ambil_tunai_value = ambil_nilai_dari_kata_kunci(content, "AMBIL TUNAI:")
                final_value = total_value - ambil_tunai_value if ambil_tunai_value else total_value
                
                # Menambahkan ke total keseluruhan hanya jika file valid
                if final_value is not None:
                    total_semua_file += final_value

                file_results.append({
                    "filename": filename,
                    "total_value": total_value,
                    "non_tunai_exists": False,
                    "ambil_tunai_value": ambil_tunai_value,
                    "final_value": final_value
                })

            except Exception as e:
                return f"Terjadi kesalahan saat membaca file {filename}: {e}", 500

        return render_template("results.html", file_results=file_results, total_semua_file=total_semua_file)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
