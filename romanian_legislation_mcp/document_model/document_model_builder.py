import json
import logging

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.document_model import (
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
        self._build_hierarchy(self.document.text, parent=None, pos_in_doc=0)
        self._add_changes()

    # Legal doc are organized by element hierarchy. Big legal docs have all hierarchy elements:
    # Book -> Title -> Chapter -> Article
    # Smaller docs can skip book, title or chapter, while simple docs have only articles.
    # Thus, we need to determine the structure of the document we are 
    def _build_hierarchy(self, text_content: str, parent=None, pos_in_doc: int = 0):
        """Build document hierarchy by trying each structural level in order."""
        if parent is None:
            self._get_books(text_content, parent=parent, pos_in_doc=pos_in_doc)
            if self._has_books(parent):
                books = self._get_children_books(parent)
                for i, book in enumerate(books):
                    book_text, book_start_pos = self._get_element_text_range(i, books)
                    self._build_hierarchy(book_text, parent=book, pos_in_doc=book_start_pos)
                return
                
            self._get_titles(text_content, parent=parent, pos_in_doc=pos_in_doc)
            if self._has_titles(parent):
                titles = self._get_children_titles(parent)
                for i, title in enumerate(titles):
                    title_text, title_start_pos = self._get_element_text_range(i, titles)
                    self._build_hierarchy(title_text, parent=title, pos_in_doc=title_start_pos)
                return
                
            self._get_chapters(text_content, parent=parent, pos_in_doc=pos_in_doc)
            if self._has_chapters(parent):
                chapters = self._get_children_chapters(parent)
                for i, chapter in enumerate(chapters):
                    chapter_text, chapter_start_pos = self._get_element_text_range(i, chapters)
                    self._build_hierarchy(chapter_text, parent=chapter, pos_in_doc=chapter_start_pos)
                return
                
            self._get_articles(text_content, parent=parent, pos_in_doc=pos_in_doc)
            
        elif hasattr(parent, 'titles'):  
            self._get_titles(text_content, parent=parent, pos_in_doc=pos_in_doc)
            if self._has_titles(parent):
                titles = self._get_children_titles(parent)
                for i, title in enumerate(titles):
                    title_text, title_start_pos = self._get_element_text_range(i, titles)
                    self._build_hierarchy(title_text, parent=title, pos_in_doc=title_start_pos)
            
        elif hasattr(parent, 'chapters'):
            self._get_chapters(text_content, parent=parent, pos_in_doc=pos_in_doc)
            if self._has_chapters(parent):
                chapters = self._get_children_chapters(parent)
                for i, chapter in enumerate(chapters):
                    chapter_text, chapter_start_pos = self._get_element_text_range(i, chapters)
                    self._build_hierarchy(chapter_text, parent=chapter, pos_in_doc=chapter_start_pos)
            else:
                self._get_articles(text_content, parent=parent, pos_in_doc=pos_in_doc)
                
        elif hasattr(parent, 'article_numbers'):  # Chapters have article_numbers
            self._get_articles(text_content, parent=parent, pos_in_doc=pos_in_doc)

    def _has_books(self, parent):
        return hasattr(parent, 'books') and parent.books is not None and len(parent.books) > 0 if parent else len(self.model.books) > 0
        
    def _has_titles(self, parent):
        return hasattr(parent, 'titles') and parent.titles is not None and len(parent.titles) > 0 if parent else len(self.model.titles) > 0
        
    def _has_chapters(self, parent):
        return hasattr(parent, 'chapters') and parent.chapters is not None and len(parent.chapters) > 0 if parent else len(self.model.chapters) > 0
        
    def _get_children_books(self, parent):
        return parent.books if parent else self.model.books
        
    def _get_children_titles(self, parent):
        return parent.titles if parent else self.model.titles
        
    def _get_children_chapters(self, parent):
        return parent.chapters if parent else self.model.chapters

    def _get_element_text_range(self, element_index: int, element_list):
        """Extract text range for a specific element from the document."""
        current_element = element_list[element_index]

        if element_index + 1 < len(element_list):
            next_element = element_list[element_index + 1]
            element_text = self.document.text[
                current_element.pos_in_doc : next_element.pos_in_doc
            ]
        else:
            # For the last element, find the next boundary (title, book, etc.)
            end_pos = self._find_next_hierarchy_boundary(current_element.pos_in_doc)
            element_text = self.document.text[current_element.pos_in_doc : end_pos]

        return element_text, current_element.pos_in_doc

    def _find_next_hierarchy_boundary(self, start_pos: int) -> int:
        """Find the next structural boundary (book, title, chapter) after start_pos."""
        text_after = self.document.text[start_pos:]
        
        # Look for the next occurrence of structural keywords
        boundaries = []
        keywords = ["Cartea", "Titlul", "Capitolul"]
        
        for keyword in keywords:
            pos = text_after.find(keyword, 1)  # Start from position 1 to skip current element
            if pos != -1:
                boundaries.append(start_pos + pos)
        
        if boundaries:
            return min(boundaries)
        else:
            return len(self.document.text)  # End of document if no boundaries found

    def _extract_element_and_recurse(
        self,
        parent_text: str,
        keyword: str,
        element_type: str,
        parent=None,
        pos_in_doc: int = 0,
    ):
        element_start = parent_text.find(keyword)
        if element_start == -1:
            return

        element_name_start = element_start + len(keyword)
        part_element_name_end = parent_text[element_name_start:].find("\n")
        if part_element_name_end == -1:
            full_element_name_end = len(parent_text)
        else:
            full_element_name_end = element_name_start + part_element_name_end
            
        # Not super consistent, for book/title/chapter, element_name_row is just the name,
        # for article it also includes (or only) content
        element_name_row = parent_text[element_name_start:full_element_name_end]

        element_pos_in_doc = pos_in_doc + element_name_start  # Position in full doc

        if self._validate_element(element_name_row, element_type):
            if element_type == "Article":
                article_full_content = self._extract_article_content(
                    parent_text, element_start, element_name_row.strip()
                )
                self._create_and_add_element(
                    element_type, article_full_content, element_pos_in_doc, parent
                )
            else:
                self._create_and_add_element(
                    element_type, element_name_row.strip(), element_pos_in_doc, parent
                )

        search_start = full_element_name_end + 1
        while search_start < len(parent_text):
            next_element_start = parent_text.find(keyword, search_start)
            if next_element_start == -1:
                break  

            next_element_name_start = next_element_start + len(keyword)
            next_part_element_name_end = parent_text[next_element_name_start:].find("\n")
            if next_part_element_name_end == -1:
                next_full_element_name_end = len(parent_text)
            else:
                next_full_element_name_end = next_element_name_start + next_part_element_name_end
                
            next_element_name_row = parent_text[next_element_name_start:next_full_element_name_end]
            next_element_pos_in_doc = pos_in_doc + next_element_name_start

            if self._validate_element(next_element_name_row, element_type):
                if element_type == "Article":
                    next_article_full_content = self._extract_article_content(
                        parent_text, next_element_start, next_element_name_row.strip()
                    )
                    self._create_and_add_element(
                        element_type, next_article_full_content, next_element_pos_in_doc, parent
                    )
                else:
                    self._create_and_add_element(
                        element_type, next_element_name_row.strip(), next_element_pos_in_doc, parent
                    )

            search_start = next_full_element_name_end + 1

    def _create_and_add_element(
        self, element_type: str, element_name: str, pos_in_doc: int, parent=None
    ):
        """Create and add an element to its appropriate parent."""

        if element_type == "Article":
            lines = element_name.split('\n', 1)
            header_line = lines[0].strip()
            article_body = lines[1].strip() if len(lines) > 1 else ""
            
            parts = header_line.split(None, 1)  
            if len(parts) >= 1:
                try:
                    article_number = int(parts[0])
                    article_title = parts[1].strip() if len(parts) > 1 else ""
                    
                    if article_body:
                        full_text = f"{article_title}\n{article_body}" if article_title else article_body
                    else:
                        full_text = article_title
                    
                    article = DocumentModelArticle(
                        number=article_number, 
                        text=full_text, 
                        pos_in_doc=pos_in_doc
                    )
                    if parent is not None:
                        parent.add_article_reference(article_number)
                        
                    self.model.add_article(article)
                except ValueError:
                    pass
        elif element_type == "Chapter":
            chapter = DocumentModelChapter(name=element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(chapter)
            else:
                self.model.add_chapter(chapter)
        elif element_type == "Title":
            title = DocumentModelTitle(element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(title)
            else:
                self.model.add_title(title)
        elif element_type == "Book":
            book = DocumentModelBook(name=element_name, pos_in_doc=pos_in_doc)
            self.model.add_book(book)

    def _get_titles(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Titlul", "Title", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_books(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Cartea", "Book", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_chapters(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Capitolul", "Chapter", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_articles(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Articolul", "Article", parent=parent, pos_in_doc=pos_in_doc
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

        if len(book_name_row) == 0:
            return False

        words = book_name_row.split()
        if len(words) == 0:
            return False
        
        first_word = words[0]
        # Books can be numbered with Roman numerals (like "I", "II", etc.) or with letters like "a", "b"
        if first_word not in ROMAN_NUMERALS and not (len(first_word) == 1 and first_word.isalpha()):
            return False

        if len(book_name_row) > 200:
            return False

        return True

    def _validate_title(self, title_name_row: str) -> bool:
        title_name_row = title_name_row.strip()
        
        words = title_name_row.split()
        if len(words) == 0:
            return False
            
        first_word = words[0]
        if first_word not in ROMAN_NUMERALS:
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

    def _extract_article_content(self, doc_text: str, article_start: int, article_header: str) -> str:
        """Extract the full content of an article including its text body."""
        article_start_in_text = article_start + len("Articolul")
        
        article_end = len(doc_text)  
        search_patterns = ["Articolul", "Capitolul", "Titlul", "Cartea", "Anexa"]
        
        for pattern in search_patterns:
            pos = doc_text.find(pattern, article_start_in_text)
            if pos != -1 and pos < article_end:
                article_end = pos
        
        article_content = doc_text[article_start:article_end].strip()
        
        lines = article_content.split('\n', 1)
        if len(lines) > 1:
            header_after_keyword = lines[0][len("Articolul"):].strip()
            article_body = lines[1].strip()
            return f"{header_after_keyword}\n{article_body}" if article_body else header_after_keyword
        else:
            return lines[0][len("Articolul"):].strip()

    def _add_changes(self):
        pass
        # articles = []
        # if self.model.
        # for change in self.document.changes:
        #     if (change.target == )