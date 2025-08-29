from typing import Optional
from romanian_legislation_mcp.structured_document.element import DocumentElementType
from romanian_legislation_mcp.structured_document.mappings.mappings import (
    ROMAN_NUMERALS,
)

join_char = " "


class Extractor:
    def __init__(self):
        self.last_valid_art_no = None

    def validate_and_extract_header(
        self,
        header: dict,
        element_type: DocumentElementType,
        preceding_text: str,
    ) -> Optional[dict]:
        if header is None:
            return None

        header_string: str = header["text"]
        header_string.strip().removesuffix("")
        if len(header_string) == 0:
            return None

        if preceding_text is not None:
            preceding_text = preceding_text.strip()
            ref_keywords = [
                "se modifică și va avea următorul cuprins:",
                "cu următoarea denumire:",
                "următorul cuprins:",
                "se modifică și va avea următorul cuprins:",
            ]

            keyword_pos_list = [preceding_text.find(key) for key in ref_keywords]
            for pos in keyword_pos_list:
                if pos != -1:
                    return None

        valid_data = None
        if element_type == DocumentElementType.PART:
            valid_data = self._validate_part_header(header_string)
        elif element_type == DocumentElementType.BOOK:
            valid_data = self._validate_book_header(header_string)
        elif element_type == DocumentElementType.TITLE:
            valid_data = self._validate_title_header(header_string)
        elif element_type == DocumentElementType.CHAPTER:
            valid_data = self._validate_chapter_header(header_string)
        elif element_type == DocumentElementType.SECTION:
            valid_data = self._validate_section_header(header_string)
        elif element_type == DocumentElementType.ARTICLE:
            valid_data = self._validate_article(header_string)
        else:
            return None

        if valid_data is not None:
            title: str = valid_data.get("title", "")
            if title.startswith("-"):
                return None

            res = {**header, **valid_data}
            del res["text"]
            return res
        else:
            return None

    def _validate_part_header(self, header: str) -> Optional[dict]:
        if len(header) > 150:
            return None

        words = header.split()
        if len(words) == 0:
            return None

        first_word = words[0]
        if len(words) == 1:
            if first_word == "SPECIALĂ" or first_word == "GENERALĂ":
                return {"number": first_word, "title": first_word}

        try:
            if first_word in ROMAN_NUMERALS:
                number = first_word
                title = str.join(join_char, words[1:])
            elif len(first_word) == 1 and first_word.isalpha() and len(words) > 0:
                number = words[1]
                title = str.join(join_char, words[2:])
            else:
                return None

            return {"number": number, "title": title}
        except IndexError:
            return None

    def _validate_book_header(self, header: str) -> Optional[dict]:
        if len(header) > 250:
            return None

        words = header.split()
        if len(words) == 0:
            return None

        first_word = words[0]
        try:
            if first_word in ROMAN_NUMERALS:
                number = first_word
                title = str.join(join_char, words[1:])
            elif len(first_word) == 1 and first_word.isalpha() and len(words) > 0:
                number = words[1]
                title = str.join(join_char, words[2:])
            else:
                return None

            return {"number": number, "title": title}
        except IndexError:
            return None

    def _validate_title_header(self, header: str) -> Optional[dict]:
        if len(header) > 500:
            return None

        words = header.split()
        if len(words) == 0:
            return None

        try:
            if (
                words[0] == "PRELIMINAR"
                or words[0] in ROMAN_NUMERALS
                or self._is_additional_number(words[0]) is not None
            ):
                number = words[0]
                title = str.join(join_char, words[1:])
            else:
                return None

            return {"number": number, "title": title}
        except IndexError:
            return None

    def _validate_chapter_header(self, header: str) -> Optional[dict]:
        if len(header) > 250:
            return None

        words = header.split()
        if len(words) == 0:
            return None

        number = words[0]
        if number not in ROMAN_NUMERALS:
            return None

        try:
            title = str.join(join_char, words[1:])
        except IndexError:
            return None

        return {"number": number, "title": title}

    def _validate_section_header(self, header: str) -> Optional[dict]:
        if len(header) > 250:
            return None

        words = header.split()
        if len(words) == 0:
            return None

        if words[0] != "a" and words[0] != "1":
            return None

        try:
            if words[0] != "1":
                second_word = words[1]
                if not second_word.endswith("-a"):
                    return None
                number = second_word[:-2]
                title = str.join(join_char, words[2:])
            else:
                number = words[0]
                title = str.join(join_char, words[1:])
        except IndexError:
            return None

        try:
            if int(number) <= 0:
                return None
        except ValueError:
            return None

        return {"number": number, "title": title}

    def _validate_article(self, article_text: str) -> Optional[dict]:
        parts = article_text.split()
        if len(parts) == 0:
            return None

        art_no = self._extract_article_number(parts[0])
        if self._is_valid_article_no(art_no):
            title = self._try_extract_article_title(article_text)

            return {"number": art_no, "title": title if title else "N/A"}

        return None

    def _extract_article_number(self, first_word: str) -> str:
        """Extract number from article header (integer numbers)."""
        if first_word in ROMAN_NUMERALS:
            return first_word

        try:
            first_word = first_word.replace(".", "")
            num = int(first_word)
            if num > 0:
                return str(num)
        except ValueError:
            return "N/A"

        return "N/A"

    def _is_valid_article_no(self, art_no: str) -> bool:
        prev = self.last_valid_art_no
        if prev == None:
            return True

        if prev in ROMAN_NUMERALS:
            if art_no in ROMAN_NUMERALS:
                return self._compare_roman_numerals(prev, art_no)
            else:
                return False
        elif art_no in ROMAN_NUMERALS:
            return False
        else:
            try:
                return int(art_no) >= int(prev)
            except:
                return False

    def _compare_roman_numerals(self, first: str, second: str) -> bool:
        """
        Compare two Roman numerals and return True if second > first.
        Uses the index position in ROMAN_NUMERALS list for comparison.
        """
        try:
            first_index = ROMAN_NUMERALS.index(first)
            second_index = ROMAN_NUMERALS.index(second)
            return second_index > first_index
        except ValueError:
            return False

    def _try_extract_article_title(self, raw_text: str) -> Optional[str]:
        rows = raw_text.split("     ")

        try:
            if len(rows) < 2:
                return None

            possible_title = rows[1]
            if len(rows) == 2:
                alt_rows = rows[1].split("  ")
                possible_title = alt_rows[0]

            if possible_title.strip().startswith("("):
                return None

            if len(rows) > 2:
                if not rows[2].strip().startswith("("):
                    return None

            return possible_title
        except Exception:
            return None

    def _is_additional_number(self, number: str) -> Optional[dict]:
        split_char = "^"
        index = number.find(split_char)
        if index == -1:
            return None

        parts = number.split(split_char)
        try:
            base_number = parts[0]
            additional_number = int(parts[1])
            return {"base": base_number, "additional": str(additional_number)}
        except Exception:
            return None
