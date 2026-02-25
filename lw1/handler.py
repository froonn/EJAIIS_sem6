# handler.py

from typing import Any
import fitz
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict

# Ensure necessary NLTK resources are downloaded for text processing
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('help/tagsets')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('omw-1.4')


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from all pages of a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text


def get_wordnet_pos(word):
    """Map POS tag to WordNet format for accurate lemmatization."""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def process_text(text: str) -> tuple[dict[str, int], dict[str, Counter[Any]]]:
    """
    Main text processing: tokenization, lemmatization, and frequency counting.
    Returns: (lexeme counts, lexeme-to-wordform connections, POS tag map).
    """
    lemmatizer = WordNetLemmatizer()

    # 1. Counters for lexemes and wordforms
    lexeme_counts = Counter()
    lexeme_to_forms = defaultdict(lambda: Counter())

    # Tokenization and filtering of non-alphabetic characters
    tokens = word_tokenize(text)
    words = [word.lower() for word in tokens if word.isalpha()]

    for word in words:
        pos_type = get_wordnet_pos(word)
        lemma = lemmatizer.lemmatize(word, pos_type)

        lexeme_counts[lemma] += 1
        lexeme_to_forms[lemma][word] += 1

    return dict(lexeme_counts), dict(lexeme_to_forms)



if __name__ == "__main__":
    full_text = extract_text_from_pdf("/home/froonn/Harry Potter And The Goblet Of Fire.pdf")

    dict1, dict2 = process_text(full_text)

    print("--- Словарь 1 (Лексемы и частота) ---")
    print(len(dict1))
    print(dict1)

    print("\n--- Словарь 2 (Лексема -> Словоформы и их частота) ---")
    print(len(dict2))

    for lemma, forms in dict2.items():
        print(f"Лексема '{lemma}':")
        for form, count in forms.items():
            print(f"  - {form}: {count}")
