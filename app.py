from flask import Flask, request, jsonify, render_template
import os
import re
import pdfplumber

app = Flask(__name__)

# Fungsi untuk memproses file dan menghitung nilai berdasarkan aturan
def proses_file(file):
    total_value = 0
    ambil_tunai_value = 0
    non_tunai_found = False
    total_found = False

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            # Cari "NON TUNAI :" dan abaikan file jika ditemukan
            if "NON TUNAI :" in text:
                non_tunai_found = True
                break

            # Cari "TOTAL :" dan ambil nilai setelahnya
            total_match = re.search(r'TOTAL :\s*([\d.,]+)', text)
            if total_match:
                total_value += float(total_match.group(1).replace(",", "").replace(".", ""))
                total_found = True

            # Cari "AMBIL TUNAI :" dan ambil nilai setelahnya
            ambil_tunai_match = re.search(r'AMBIL TUNAI :\s*([\d.,]+)', text)
            if ambil_tunai_match:
                ambil_tunai_value += float(ambil_tunai_match.group(1).replace(",", "").replace(".", ""))

    # Abaikan file dari perhitungan jika ditemukan "NON TUNAI :"
    if non_tunai_found:
        return None

    # Hitung hasil akhir dengan mengurangkan nilai "AMBIL TUNAI :" dari "TOTAL :"
    if total_found:
        final_value = total_value - ambil_tunai_value
        return final_value
    return None

# Route untuk halaman upload
@app.route("/")
def index():
    return render_template("upload.html")

# Route untuk meng-handle upload dan proses file
@app.route("/upload", methods=["POST"])
def upload_files():
    files = request.files.getlist("files[]")
    if len(files) > 1000:
        return jsonify({"error": "Maksimum 1000 file diperbolehkan"}), 400

    total_sum = 0
    processed_files_count = 0

    for file in files:
        result = proses_file(file)
        if result is not None:
            total_sum += result
            processed_files_count += 1

    return jsonify({
        "total_files_processed": processed_files_count,
        "final_total_sum": total_sum
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
