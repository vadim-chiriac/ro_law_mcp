import json
import logging

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_search.document_model.document_model import (
    DocumentModel,
    DocumentModelArticle,
    DocumentModelBook,
    DocumentModelChapter,
    DocumentModelTitle,
)

ROMAN_NUMERALS = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
    "XVII",
    "XVIII",
    "XIX",
    "XX",
]

logger = logging.getLogger(__name__)


class DocumentModelBuilder:
    def __init__(self, document: LegislationDocument):
        self.document = document
        self.model = None

    def build_document_model(self) -> DocumentModel:
        self.model = DocumentModel()
        self._get_books(self.document.text, parent=None, pos_in_doc=0)
        if len(self.model.books) > 0:
            for i, book in enumerate(self.model.books):
                book_text, book_start_pos = self._get_element_text_range(
                    i, self.model.books
                )
                self._get_titles(book_text, parent=book, pos_in_doc=book_start_pos)
                if book.titles:
                    for j, title in enumerate(book.titles):
                        title_text, title_start_pos = self._get_element_text_range(
                            j, book.titles
                        )
                        self._get_chapters(title_text, parent=title, pos_in_doc=title_start_pos)
        else:
            self._get_titles(self.document.text, parent=None, pos_in_doc=0)
            if self.model.titles:
                for i, title in enumerate(self.model.titles):
                    title_text, title_start_pos = self._get_element_text_range(
                        i, self.model.titles
                    )
                    self._get_chapters(title_text, parent=title, pos_in_doc=title_start_pos)
            else:
                self._get_chapters(self.document.text, parent=None, pos_in_doc=0)

        self.model.log()
        pass

    def _build_document_structure(self):
        pass

    def _get_element_text_range(self, element_index: int, element_list):
        """Extract text range for a specific element from the document."""
        current_element = element_list[element_index]

        if element_index + 1 < len(element_list):
            next_element = element_list[element_index + 1]
            element_text = self.document.text[
                current_element.pos_in_doc : next_element.pos_in_doc
            ]
        else:
            element_text = self.document.text[current_element.pos_in_doc :]

        return element_text, current_element.pos_in_doc

    def _extract_element_and_recurse(
        self,
        doc_text: str,
        keyword: str,
        element_type: str,
        parent=None,
        pos_in_doc: int = 0,
    ):
        element_start = doc_text.find(keyword)
        if element_start == -1:
            return

        element_name_start = element_start + len(keyword)
        part_element_name_end = doc_text[element_name_start:].find("\n")
        full_element_name_end = element_name_start + part_element_name_end
        element_name_row = doc_text[element_name_start:full_element_name_end]

        element_pos_in_doc = pos_in_doc + element_name_start  # Position in full doc

        if self._validate_element(element_name_row, element_type):
            self._create_and_add_element(
                element_type, element_name_row.strip(), element_pos_in_doc, parent
            )

        # Continue searching from after the complete element to avoid infinite recursion
        next_search_start = full_element_name_end + 1  # Move past the newline
        if next_search_start >= len(doc_text):
            return  # No more text to search
        remaining_text = doc_text[next_search_start:]
        remaining_pos = pos_in_doc + next_search_start

        if element_type == "Title":
            self._get_titles(remaining_text, parent=parent, pos_in_doc=remaining_pos)
        elif element_type == "Book":
            self._get_books(remaining_text, parent=parent, pos_in_doc=remaining_pos)
        elif element_type == "Chapter":
            self._get_chapters(remaining_text, parent=parent, pos_in_doc=remaining_pos)
        elif element_type == "Article":
            self._get_articles(remaining_text, parent=parent, pos_in_doc=remaining_pos)

    def _create_and_add_element(
        self, element_type: str, element_name: str, pos_in_doc: int, parent=None
    ):
        """Create and add an element to its appropriate parent."""
        if element_type == "Chapter":
            chapter = DocumentModelChapter(name=element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(chapter)
            else:
                self.model.add_chapter(chapter)
        elif element_type == "Article":
            article = DocumentModelArticle(number=1, text="test", pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(article)
            else:
                self.model.add_article(article)
            # parts = element_name.split('.', 1)
            # if len(parts) >= 2:
            #     try:
            #         article_number = int(parts[0].strip())
            #         article_text = parts[1].strip() if len(parts) > 1 else ""
            #         article = DocumentModelArticle(number=article_number, text=article_text, pos_in_doc=pos_in_doc)
            #         if parent is not None:
            #             parent.add_child(article)
            #         else:
            #             self.model.add_article(article)
            #     except ValueError:
            #         pass
        elif element_type == "Title":
            title = DocumentModelTitle(element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(title)
            else:
                self.model.add_title(title)
        elif element_type == "Book":
            book = DocumentModelBook(name=element_name, pos_in_doc=pos_in_doc)
            self.model.add_book(book)

    def _get_titles(self, doc_text: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            doc_text, "Titlul", "Title", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_books(self, doc_text: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            doc_text, "Cartea", "Book", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_chapters(self, doc_text: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            doc_text, "Capitolul", "Chapter", parent=parent, pos_in_doc=pos_in_doc
        )
    
    def _get_articles(self, doc_text: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            doc_text, "Articolul", "Article", parent=parent, pos_in_doc=pos_in_doc
        )

    def _validate_element(self, element_name_row: str, element_type: str) -> bool:
        if element_type == "Book":
            return self._validate_book(element_name_row)
        if element_type == "Title":
            return self._validate_title(element_name_row)
        if element_type == "Chapter":
            return self._validate_chapter(element_name_row)
        if element_type == "Article":
            return self._validate_article(element_name_row)
        return True

    def _validate_book(self, book_name_row: str) -> bool:
        book_name_row = book_name_row.strip()
        # logger.info(f"Validating book: {book_name_row}")

        if book_name_row[0] != "a" and book_name_row[0] != "I":
            return False

        if len(book_name_row) > 200:
            return False

        return True

    def _validate_title(self, title_name_row: str) -> bool:
        if title_name_row.split()[0] not in ROMAN_NUMERALS:
            return False

        return True
    
    def _validate_chapter(self, chapter_name_row: str) -> bool:
        chapter_name_row = chapter_name_row.strip()
        
        words = chapter_name_row.split()
        if len(words) == 0:
            return False
            
        first_word = words[0]
        if first_word not in ROMAN_NUMERALS:
            return False
        
        if len(chapter_name_row) > 200:
            return False
            
        return True
    
    def _validate_article(self, article_name_row: str) -> bool:
        article_name_row = article_name_row.strip()
        
        parts = article_name_row.split()
        if len(parts) < 1:
            return False
            
        try:
            int(parts[0])
        except ValueError:
            return False
                    
        return True
