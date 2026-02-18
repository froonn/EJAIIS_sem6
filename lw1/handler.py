from typing import Any

import fitz

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def get_wordnet_pos(word):
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def process_text(text: str) -> tuple[dict[str, int], dict[str, Counter[Any]]]:

    handler = WordNetLemmatizer().lemmatize

    # 1. Lexeme dict: {lexeme: general_quantity}
    lexeme_counts = Counter()

    # 2. Dict of connections: {lexeme: {word_form: frequency}}
    lexeme_to_forms = defaultdict(lambda: Counter())

    for word in word_tokenize(text):
        word = word.lower()
        lemma = handler(word, get_wordnet_pos(word))

        lexeme_counts[lemma] += 1
        lexeme_to_forms[lemma][word] += 1

    return dict(lexeme_counts), dict(lexeme_to_forms)

def process_pdf(filepath):
    return process_text(extract_text_from_pdf(filepath))


if __name__ == "__main__":
    full_text = extract_text_from_pdf("/home/froonn/Harry Potter And The Goblet Of Fire.pdf")

    dict1, dict2 = process_text(full_text)

    # Вывод результатов
    print("--- Словарь 1 (Лексемы и частота) ---")
    print(len(dict1))
    print(dict1)

    print("\n--- Словарь 2 (Лексема -> Словоформы и их частота) ---")
    print(len(dict2))

    for lemma, forms in dict2.items():
        print(f"Лексема '{lemma}':")
        for form, count in forms.items():
            print(f"  - {form}: {count}")

