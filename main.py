import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import wordnet
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import simpledialog
import difflib
from fpdf import FPDF
import datetime

# Download necessary NLTK data
nltk.download('wordnet')
nltk.download('punkt')


# Functions for the search algorithm
def normalize_terms(search_terms):
    tokens = nltk.word_tokenize(search_terms)
    tokens = [token.lower() for token in tokens]
    stemmer = PorterStemmer()
    normalized_tokens = [stemmer.stem(token) for token in tokens]
    return normalized_tokens


def get_synonyms(term):
    synonyms = set()
    for syn in wordnet.synsets(term):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return synonyms


def expand_terms(tokens):
    expanded_terms = set(tokens)
    for token in tokens:
        expanded_terms.update(get_synonyms(token))
    return expanded_terms


from collections import defaultdict


def create_inverted_index(documents):
    inverted_index = defaultdict(list)
    for doc_id, content in documents.items():
        tokens = normalize_terms(content)
        for token in tokens:
            inverted_index[token].append(doc_id)
    return inverted_index


def search_documents(search_terms, inverted_index, documents):
    tokens = normalize_terms(search_terms)
    expanded_terms = expand_terms(tokens)
    results = set()
    for term in expanded_terms:
        if term in inverted_index:
            results.update(inverted_index[term])
        else:
            # Find close matches if the exact term is not found
            for word in inverted_index.keys():
                if difflib.get_close_matches(term, [word]):
                    results.update(inverted_index[word])
    return results


def rank_and_highlight(results, search_terms, documents, scores):
    search_terms = normalize_terms(search_terms)
    ranked_results = []
    for doc_id in results:
        content = documents[doc_id]
        score = scores.get(doc_id, 0) + sum(content.lower().count(term) for term in search_terms)
        ranked_results.append((score, doc_id, content))
    ranked_results.sort(reverse=True, key=lambda x: x[0])
    highlighted_results = [(doc_id, highlight_terms(content, search_terms), score) for score, doc_id, content in
                           ranked_results]
    return highlighted_results


def highlight_terms(content, search_terms):
    highlighted_content = ""
    for word in content.split():
        if any(term in word.lower() for term in search_terms):
            highlighted_content += f" * {word} * "
        else:
            highlighted_content += f" {word}"
    return highlighted_content


def display_highlighted_text(content, text_widget, search_terms):
    text_widget.tag_configure('highlight', foreground='red')
    text_widget.insert(tk.END, content)
    for term in search_terms:
        start_idx = '1.0'
        while True:
            start_idx = text_widget.search(term, start_idx, tk.END, nocase=1)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(term)}c"
            text_widget.tag_add('highlight', start_idx, end_idx)
            start_idx = end_idx


def increment_score(doc_id):
    scores[doc_id] = scores.get(doc_id, 0) + 1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selection_history.append((doc_id, documents[doc_id], timestamp))


def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Search Choices History", ln=True, align='C')
    pdf.ln(10)
    for doc_id, content, timestamp in selection_history:
        pdf.set_text_color(0, 0, 0)  # Black
        pdf.set_font("Arial", size=18, style='B')  # Bold, size 18
        pdf.multi_cell(200, 10, txt=f"Document ID: {doc_id} (Score: {scores[doc_id]})")
        pdf.set_text_color(255, 0, 0)  # Red
        pdf.set_font("Arial", size=12)  # Normal, size 12
        pdf.multi_cell(200, 10, txt=f"Selected at: {timestamp}")
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)  # Black
        pdf.set_font("Arial", size=12)  # Normal, size 12
        pdf.multi_cell(200, 10, txt=content)
        pdf.ln(5)
    pdf.output("search_choices_history.pdf")
    messagebox.showinfo("PDF Generated", "PDF file has been generated and saved as 'search_choices_history.pdf'.")


# Dummy data
documents = {
    1: "This is a test document about risk management.",
    2: "Another document discussing risk and compliance.",
    3: "This document is focused on software requirements specifications.",
    4: "Electrical system safety reports are important.",
    5: "Mechanical systems need proper safety evaluations.",
    6: "Software design requires careful planning and execution.",
    7: "Risk analysis should be an integral part of system design.",
    8: "Electrical hazards must be identified and mitigated.",
    9: "Mechanical designs need to comply with safety standards.",
    10: "Comprehensive testing ensures system reliability.",
    11: "Safety evaluations should be conducted regularly.",
    12: "Compliance with regulations is mandatory for medical devices.",
    13: "Risk management involves identifying, assessing, and controlling risks.",
    14: "Software testing includes unit tests, integration tests, and system tests.",
    15: "Documentation is crucial for traceability and compliance.",
    16: "Mechanical components should be tested for durability and safety.",
    17: "Electrical systems should have fail-safes in place.",
    18: "Software updates must be managed carefully to avoid introducing new risks.",
    19: "Risk mitigation strategies include redundancy and diversification.",
    20: "Compliance audits help ensure adherence to safety standards."
}

scores = defaultdict(int)
selection_history = []
inverted_index = create_inverted_index(documents)


# GUI
def perform_search(event=None):
    search_terms = search_entry.get()
    if not search_terms:
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "No results found.")
        return

    results = search_documents(search_terms, inverted_index, documents)
    highlighted_results = rank_and_highlight(results, search_terms, documents, scores)

    results_text.delete(1.0, tk.END)
    if not highlighted_results:
        results_text.insert(tk.END, "No results found.")
    else:
        for doc_id, content, score in highlighted_results:
            results_text.insert(tk.END, f"Document ID: {doc_id} (Score: {score})\n")
            display_highlighted_text(content, results_text, normalize_terms(search_terms))
            results_text.insert(tk.END, "\n")
            # Add a button to increment the score
            increment_button = tk.Button(results_text, text="Select",
                                         command=lambda doc_id=doc_id: increment_score(doc_id))
            results_text.window_create(tk.END, window=increment_button)
            results_text.insert(tk.END, "\n\n")


# Create main window
root = tk.Tk()
root.title("Risk Management System Search")

# Create and place widgets
tk.Label(root, text="Enter search terms:").pack(pady=5)
search_entry = tk.Entry(root, width=50)
search_entry.pack(pady=5)
search_entry.bind('<KeyRelease>', perform_search)  # Bind the KeyRelease event to the search function

results_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
results_text.pack(pady=5)

generate_pdf_button = tk.Button(root, text="Generate PDF", command=generate_pdf)
generate_pdf_button.pack(pady=10)

# Run the application
root.mainloop()
