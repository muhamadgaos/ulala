import streamlit as st
import spacy
import re
from collections import Counter
from PyPDF2 import PdfReader
from docx import Document
from googletrans import Translator
import os

def read_file(filepath):
    """Membaca isi file berdasarkan ekstensinya."""
    ext = os.path.splitext(filepath.name)[1].lower()
    if ext == '.txt':
        return filepath.read().decode('utf-8')
    elif ext == '.pdf':
        reader = PdfReader(filepath)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text
    elif ext == '.docx':
        doc = Document(filepath)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    else:
        st.error("Format file tidak didukung. Gunakan .txt, .pdf, atau .docx")
        return None

def preprocess_text(text):
    """Menghapus tanda baca dan membuat teks menjadi huruf kecil."""
    text = re.sub(r'[^\w\s]', '', text)  # Hapus tanda baca
    text = text.lower()
    return text

def analyze_frequency(text):
    """Menghitung frekuensi kata dalam teks."""
    words = text.split()
    return Counter(words)

def analyze_pos(text):
    """Menganalisis kelas kata menggunakan spaCy untuk Bahasa Jerman."""
    nlp = spacy.load("de_core_news_sm")
    doc = nlp(text)
    pos_counts = Counter([token.pos_ for token in doc])
    return pos_counts

def expand_words_by_pos(text, pos_tags):
    """Menjabarkan kata berdasarkan kelas kata tertentu."""
    nlp = spacy.load("de_core_news_sm")
    doc = nlp(text)
    pos_words = {}
    for pos in pos_tags:
        pos_words[pos] = [token.text for token in doc if token.pos_ == pos]
    return pos_words

def translate_text(text, src_lang, dest_lang):
    """Menerjemahkan teks lengkap dari satu bahasa ke bahasa lain."""
    translator = Translator()
    try:
        translated = translator.translate(text, src=src_lang, dest=dest_lang)
        return translated.text
    except Exception as e:
        return f"Error: {e}"

# Streamlit App
st.title("Analisis Teks dengan Streamlit")

# Unggah file
uploaded_file = st.file_uploader("Unggah file (format: .txt, .pdf, .docx):", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    # Membaca file
    text = read_file(uploaded_file)
    if text:
        st.subheader("Teks Asli")
        st.text_area("Konten File:", text, height=200)

        # Preprocessing
        cleaned_text = preprocess_text(text)
        st.subheader("Teks Setelah Preprocessing")
        st.text_area("Konten Setelah Preprocessing:", cleaned_text, height=200)

        # Analisis frekuensi kata
        word_frequencies = analyze_frequency(cleaned_text)
        st.subheader("Frekuensi Kata")
        st.write(dict(word_frequencies.most_common(10)))

        # Analisis kelas kata
        pos_counts = analyze_pos(cleaned_text)
        st.subheader("Distribusi Kelas Kata")
        st.write(dict(pos_counts))

        # Jabarkan kata berdasarkan kelas kata
        pos_tags_to_expand = st.multiselect("Pilih Kelas Kata untuk Dijabarkan:", ['NOUN', 'VERB', 'ADJ'], default=['NOUN', 'VERB', 'ADJ'])
        if pos_tags_to_expand:
            expanded_words = expand_words_by_pos(cleaned_text, pos_tags_to_expand)
            st.subheader("Kata-kata Berdasarkan Kelas Kata")
            st.write(expanded_words)

        # Terjemahan teks
        st.subheader("Terjemahan Teks")
        src_lang = st.selectbox("Pilih Bahasa Asal:", ["de", "id", "en"], index=0)
        dest_lang = st.selectbox("Pilih Bahasa Tujuan:", ["id", "en", "de"], index=1)
        if st.button("Terjemahkan Teks"):
            translated_text = translate_text(text, src_lang, dest_lang)
            st.text_area("Teks Terjemahan:", translated_text, height=200)