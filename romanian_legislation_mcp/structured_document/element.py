from typing import Optional

import enum
import logging
import uuid

logger = logging.getLogger(__name__)


class DocumentElement:
    """Class representing a structural part of the text of a legal document"""

    def __init__(
        self,
        type_name: "DocumentElementType",
        number: str,
        title: str = "",
        start_pos: int = -1,
        end_pos: int = -1,
        parent: Optional["DocumentElement"] = None,
    ):
        """Initializes a new instance.

        :param type_name: The type of the document part
        :param number: The number of the document part as per the legal document text (can include non-numeric values)
        :param title: The title of the document part in the legal document text
        :param start_pos: Start position relative to parent text
        :param end_pos: End position relative to parent text
        :param parent: Parent document part, or None for the top level element
        """
        self.id = str(uuid.uuid4())
        self.type_name = type_name
        self.number = number
        self.title = title
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.parent = parent
        self.children: list[DocumentElement] = []

    def add_child(self, child: "DocumentElement"):
        """Adds a new `DocumentPart` child to this instance

        :param child: The document part to add.
        """

        child.set_parent(self)
        self.children.append(child)

    def set_parent(self, parent: "DocumentElement"):
        self.parent = parent

    def get_structure(self) -> dict:
        structure = {
            "type": self.type_name.name.lower(),
            "number": self.number,
            "title": self.title,
            "start": self.start_pos,
            "end": self.end_pos
        }

        article_children = [
            child
            for child in self.children
            if child.type_name == DocumentElementType.ARTICLE
        ]

        if article_children:
            numeric_articles = []
            other_articles = []

            for article in article_children:
                if article.number.isdigit():
                    numeric_articles.append(int(article.number))
                else:
                    other_articles.append(article.number)

            if numeric_articles:
                numeric_articles.sort()
                structure["article_range"] = self._format_numeric_range(
                    numeric_articles
                )

            if other_articles:
                structure["other_articles"] = other_articles

        non_article_children = [
            child
            for child in self.children
            if child.type_name != DocumentElementType.ARTICLE
        ]
        if non_article_children:
            structure["children"] = [
                child.get_structure() for child in non_article_children
            ]

        return structure

    def _format_numeric_range(self, numbers: list[int]) -> str:
        """Formats a list of numbers into readable ranges (e.g., '1-5, 7, 9-12')"""
        if not numbers:
            return ""

        ranges = []
        start = numbers[0]
        end = numbers[0]

        for i in range(1, len(numbers)):
            if numbers[i] == end + 1:
                end = numbers[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = numbers[i]

        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)


class DocumentElementType(enum.Enum):
    """Class responsible for legal document elementy hierarchy order and helper methods"""

    TOP = 0
    PART = 1
    BOOK = 2
    TITLE = 3
    CHAPTER = 4
    SECTION = 5
    ARTICLE = 6

    def get_hierarchy(self) -> list['DocumentElementType']:
        return [
            DocumentElementType.TOP,
            DocumentElementType.PART,
            DocumentElementType.BOOK,
            DocumentElementType.TITLE,
            DocumentElementType.CHAPTER,
            DocumentElementType.SECTION,
            DocumentElementType.ARTICLE,
        ]

    def to_string(self) -> str:
        return self.to_keyword()

    def to_keyword(self) -> str:
        """Returns the string used in legal documents for this type of instance

        :return: The string representation.
        """
        if self == DocumentElementType.PART:
            return "PARTEA"
        elif self == DocumentElementType.BOOK:
            return "Cartea"
        elif self == DocumentElementType.TITLE:
            return "Titlul"
        elif self == DocumentElementType.CHAPTER:
            return "Capitolul"
        elif self == DocumentElementType.SECTION:
            return "Secţiunea"
        elif self == DocumentElementType.ARTICLE:
            return "Articolul"
        else:
            return None

    def get_possible_child_types(self) -> list["DocumentElementType"]:
        """Returns all possible child element types in decreasing hierarchical order."""
        try:
            pos = self.get_hierarchy().index(self)
            return self.get_hierarchy()[pos + 1:]
        except:
            return []
        
    def get_possible_equal_or_greater_types(self) -> list["DocumentElementType"]:
        """Returns element types that are at the same hierarchical level or higher."""
        if self == DocumentElementType.TOP:
            return []
        else:
            try:
                pos = self.get_hierarchy().index(self)
                return self.get_hierarchy()[:pos + 1]
            except:
                return []

