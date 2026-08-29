"""Terminal Spanish tutor powered by Google's Gemini API."""

import os
import json
import random
from pathlib import Path

from dotenv import load_dotenv
from google import genai


ENV_FILE = Path(__file__).resolve().with_name(".env")
load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY is missing from {ENV_FILE}")

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-2.5-flash"
WORDS_FILE = Path(__file__).resolve().with_name("spanish_words.json")
MAX_BOX = 5


def load_words() -> list[dict[str, str | int]]:
    """Load vocabulary cards from the JSON file."""
    if not WORDS_FILE.exists():
        return []

    try:
        with WORDS_FILE.open(encoding="utf-8") as words_file:
            words = json.load(words_file)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Could not parse {WORDS_FILE}: {error}") from error

    if not isinstance(words, list):
        raise RuntimeError(f"Expected {WORDS_FILE} to contain a list of cards")

    for word in words:
        if (
            not isinstance(word, dict)
            or not isinstance(word.get("spanish"), str)
            or not isinstance(word.get("english"), str)
            or not isinstance(word.get("box"), int)
        ):
            raise RuntimeError(
                "Each vocabulary card must contain string 'spanish' and "
                "'english' values plus an integer 'box'"
            )
    return words


def save_words(words: list[dict[str, str | int]]) -> None:
    """Save vocabulary cards to the JSON file."""
    temporary_file = WORDS_FILE.with_suffix(".json.tmp")
    with temporary_file.open("w", encoding="utf-8") as words_file:
        json.dump(words, words_file, ensure_ascii=False, indent=2)
        words_file.write("\n")
    temporary_file.replace(WORDS_FILE)


def add_word(words: list[dict[str, str | int]]) -> None:
    """Prompt for and save a new vocabulary card."""
    spanish = input("Spanish word or phrase: ").strip()
    english = input("English meaning: ").strip()
    if not spanish or not english:
        print("Both Spanish and English are required.")
        return

    words.append({"spanish": spanish, "english": english, "box": 1})
    save_words(words)
    print(f"Saved '{spanish}'.")


def review_words(words: list[dict[str, str | int]]) -> None:
    """Run a flashcard review and update each card's review box."""
    if not words:
        print("No vocabulary cards found. Add a word first.")
        return

    cards = words.copy()
    random.shuffle(cards)
    for card in cards:
        print(f"\nSpanish: {card['spanish']}")
        input("Press Enter to reveal the answer...")
        print(f"English: {card['english']}")
        result = input("Did you get it right? [y/N]: ").strip().lower()
        if result == "y":
            card["box"] = min(int(card["box"]) + 1, MAX_BOX)
        else:
            card["box"] = 1

    save_words(words)
    print("Review complete. Progress saved.")


def main() -> None:
    """Start the tutor application."""
    words = load_words()
    print(f"Spanish tutor ready ({MODEL_NAME}).")
    while True:
        print("\n1. Add vocabulary\n2. Review flashcards\n3. Quit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_word(words)
        elif choice == "2":
            review_words(words)
        elif choice == "3":
            print("¡Hasta luego!")
            break
        else:
            print("Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()