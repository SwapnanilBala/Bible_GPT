from pathlib import Path
import json
import pandas as pd


INPUT_JSON = Path("Bible_English_Version.json")   # your file
OUTPUT_CSV = Path("bible_verses.csv")


def flatten_from_list(data: list[dict]) -> pd.DataFrame:
    """
    Handles JSON like:
    [
      {"book": "John", "chapter": 3, "verse": 16, "text": "For God so loved..."},
      ...
    ]
    or with slightly different key names.
    """
    df = pd.DataFrame(data)

    # Try to normalize possible column names
    rename_map = {
        "Book": "book",
        "book_name": "book",
        "bookName": "book",

        "Chapter": "chapter",
        "chapterNumber": "chapter",

        "Verse": "verse",
        "verseNumber": "verse",

        "Text": "text",
        "verseText": "text",
        "content": "text",
    }

    df = df.rename(
        columns={old: new for old, new in rename_map.items() if old in df.columns}
    )

    required = {"book", "chapter", "verse", "text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Could not find required fields in JSON list format. "
            f"Missing: {missing}. Columns seen: {list(df.columns)}"
        )

    # Keep only the required columns, ordered
    df = df[["book", "chapter", "verse", "text"]]
    return df


def flatten_from_nested(data: dict) -> pd.DataFrame:
    """
    Handles JSON like:
    {
      "Genesis": {
        "1": {
          "1": "In the beginning...",
          "2": "And the earth was..."
        },
        "2": { ... }
      },
      "Exodus": { ... }
    }
    """
    records = []

    for book, chapters in data.items():
        if not isinstance(chapters, dict):
            continue

        for chapter, verses in chapters.items():
            if not isinstance(verses, dict):
                continue

            for verse, text in verses.items():
                records.append(
                    {
                        "book": book,
                        "chapter": int(chapter),
                        "verse": int(verse),
                        "text": str(text),
                    }
                )

    if not records:
        raise ValueError("Nested JSON structure could not be flattened – no records found.")

    return pd.DataFrame(records)


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Could not find {INPUT_JSON!s} in project root.")

    with INPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Detect shape and flatten accordingly
    if isinstance(data, list):
        print("Detected list-of-dicts JSON format.")
        df = flatten_from_list(data)
    elif isinstance(data, dict):
        print("Detected nested-dict JSON format.")
        df = flatten_from_nested(data)
    else:
        raise TypeError(f"Unsupported JSON top-level type: {type(data)}")

    # Sort nicely: book, chapter, verse (chapter & verse as int if possible)
    for col in ("chapter", "verse"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df = df.sort_values(["book", "chapter", "verse"]).reset_index(drop=True)

    # Add an id column
    df.insert(0, "id", range(len(df)))

    # Save
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"Saved {len(df)} verses to {OUTPUT_CSV}")
    print("First few rows:")
    print(df.head())


if __name__ == "__main__":
    main()
