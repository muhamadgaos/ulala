import streamlit as st
import spacy
import re
from collections import Counter
from PyPDF2 import PdfReader
from docx import Document
from googletrans import Translator
import os
import language_tool_python

# Fungsi membaca file
def read_file(filepath):
    ext = os.path.splitext(filepath.name)[1].lower()
    if ext == '.txt':
        content = filepath.read().decode('utf-8')
        if not content.strip():
            st.error("File kosong. Harap unggah file dengan konten yang valid.")
            return None
        return content
    elif ext == '.pdf':
        reader = PdfReader(filepath)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        if not text.strip():
            st.error("File kosong. Harap unggah file PDF dengan konten yang valid.")
            return None
        return text
    elif ext == '.docx':
        doc = Document(filepath)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        if not text.strip():
            st.error("File kosong. Harap unggah file DOCX dengan konten yang valid.")
            return None
        return text
    else:
        st.error("Format file tidak didukung. Gunakan .txt, .pdf, atau .docx")
        return None

# Fungsi memisahkan teks menjadi kalimat menggunakan SpaCy
def split_into_sentences_spacy(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

# Fungsi analisis POS menggunakan SpaCy
def analyze_pos(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return Counter([token.pos_ for token in doc])

# Fungsi menghitung frekuensi kata
def word_frequency(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return Counter(words)

# Fungsi grammar checker untuk teks berbahasa Jerman
def check_grammar_german(sentences):
    tool = language_tool_python.LanguageTool('de-DE')
    corrections = {}
    for sentence in sentences:
        matches = tool.check(sentence)
        sentence_corrections = []
        for match in matches:
            sentence_corrections.append({
                "error": match.context,
                "message": match.message,
                "suggestions": match.replacements
            })
        corrections[sentence] = sentence_corrections
    return corrections

# Fungsi terjemahan teks menggunakan googletrans
def translate_text_per_sentence(sentences, src_lang, dest_lang):
    translator = Translator()
    translated_sentences = []
    for sentence in sentences:
        try:
            translated = translator.translate(sentence.strip(), src=src_lang, dest=dest_lang)
            translated_sentences.append(translated.text)
        except Exception as e:
            translated_sentences.append(f"Error: {e}")
    return translated_sentences

# Streamlit App
st.title("Bismillah BTI A")

# Unggah file
uploaded_file = st.file_uploader("Unggah file (format: .txt, .pdf, .docx):", type=["txt", "pdf", "docx"])

if uploaded_file:
    text = read_file(uploaded_file)
    if text:
        # Pisahkan teks menjadi kalimat
        sentences = split_into_sentences_spacy(text)

        # Tampilan korpus teks asli dalam textbox yang nyaman
        st.subheader("Teks Asli (Scroll untuk melihat seluruh teks)")
        formatted_text = "\n\n".join(sentences)  # Menyusun kalimat menjadi paragraf
        st.text_area("Teks Asli:", value=formatted_text, height=300, max_chars=None)

        # Analisis Distribusi Kelas Kata
        st.subheader("Distribusi Kelas Kata")
        pos_counts = analyze_pos(text)
        st.write(dict(pos_counts))

        # Frekuensi Kata dalam Tabel
        st.subheader("Frekuensi Kata")
        word_freq = word_frequency(text)
        word_freq_table = [{"Kata": word, "Frekuensi": freq} for word, freq in word_freq.most_common(10)]
        st.table(word_freq_table)  # Tampilkan sebagai tabel

        # Pencarian dan Paging Kalimat
        st.subheader("Pilih Kalimat untuk Diterjemahkan atau Diperiksa Tata Bahasa")
        search_keyword = st.text_input("Cari kalimat berdasarkan kata kunci:")

        if search_keyword:
            filtered_sentences = [s for s in sentences if search_keyword.lower() in s.lower()]
        else:
            filtered_sentences = sentences

        # Paging untuk menampilkan 10 kalimat per halaman
        BATCH_SIZE = 10
        total_sentences = len(filtered_sentences)
        total_pages = (total_sentences + BATCH_SIZE - 1) // BATCH_SIZE
        current_page = st.number_input("Pilih Halaman:", min_value=1, max_value=total_pages, value=1, step=1)

        start_idx = (current_page - 1) * BATCH_SIZE
        end_idx = start_idx + BATCH_SIZE
        displayed_sentences = filtered_sentences[start_idx:end_idx]

        st.write(f"Menampilkan kalimat {start_idx + 1} - {min(end_idx, total_sentences)} dari {total_sentences}:")

        selected_sentences = []
        for i, sentence in enumerate(displayed_sentences, start=start_idx + 1):
            if st.checkbox(f"Kalimat {i}: {sentence}", key=f"sentence_{i}"):
                selected_sentences.append(sentence)

        # Pemeriksaan Tata Bahasa untuk Kalimat yang Dipilih
        if selected_sentences:
            st.subheader("Pemeriksaan Tata Bahasa")
            if st.button("Periksa Tata Bahasa pada Kalimat yang Dipilih"):
                grammar_corrections = check_grammar_german(selected_sentences)
                if grammar_corrections:
                    for sentence, corrections in grammar_corrections.items():
                        st.write(f"**Kalimat:** {sentence}")
                        if corrections:
                            for correction in corrections:
                                st.write(f"- **Kesalahan:** {correction['error']}")
                                st.write(f"  **Pesan:** {correction['message']}")
                                st.write(f"  **Saran:** {', '.join(correction['suggestions']) if correction['suggestions'] else 'Tidak ada saran'}")
                        else:
                            st.success("Tidak ditemukan kesalahan tata bahasa.")
                else:
                    st.success("Tidak ditemukan kesalahan tata bahasa.")

            # Terjemahan Kalimat yang Dipilih
            st.subheader("Terjemahan Kalimat yang Dipilih")
            src_lang = st.selectbox("Pilih Bahasa Asal:", ["de", "id", "en"], index=0)
            dest_lang = st.selectbox("Pilih Bahasa Tujuan:", ["id", "en", "de"])

            if st.button("Terjemahkan Kalimat yang Dipilih"):
                st.subheader("Hasil Terjemahan per Kalimat:")
                translated_sentences = translate_text_per_sentence(selected_sentences, src_lang, dest_lang)
                for i, (original, translated) in enumerate(zip(selected_sentences, translated_sentences), start=1):
                    st.write(f"**Kalimat {i}:**")
                    st.write(f"- **Asli:** {original}")
                    st.write(f"- **Terjemahan:** {translated}")
        else:
            st.warning("Pilih minimal satu kalimat untuk diperiksa atau diterjemahkan.")
    else:
        st.error("Teks tidak ditemukan. Pastikan file Anda memiliki konten yang valid.")
else:
    st.info("Unggah file untuk memulai analisis.")
