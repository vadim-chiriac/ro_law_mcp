from typing import Optional

import enum
import logging
import uuid

logger = logging.getLogger(__name__)


class DocumentPart:
    """Class representing a structural part of the text of a legal document"""

    def __init__(
        self,
        type_name: "DocumentPartType",
        number: str = "0",
        title: str = "",
        start_pos: int = -1,
        end_pos: int = -1,
        parent: Optional["DocumentPart"] = None,
    ):
        """Initializes a new instance.

        :param type_name: The type of the document part
        :param number: The number of the document part as per the legal document text (can include non-numeric values)
        :param title: The title of the document part in the legal document text
        :param start_pos: Start position relative to parent text
        :param end_pos: End position relative to parent text
        :param parent: Parent document part, or None for the top level element
        """
        self.id = uuid.uuid4()
        self.type_name = type_name
        self.number = number
        self.title = title
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.parent = parent
        self.children: list[DocumentPart] = []

    def add_child(self, child: "DocumentPart"):
        """Adds a new `DocumentPart` child to this instance

        :param child: The document part to add.
        """

        child.set_parent(self)
        self.children.append(child)

    def set_parent(self, parent: "DocumentPart"):
        self.parent = parent

    def set_number(self, number: str):
        self.number = number


class DocumentPartType(enum.Enum):
    """Class responsible for legal document elementy hierarchy order and helper methods"""

    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3
    SECTION = 4
    ARTICLE = 5

    def to_keyword(self) -> str:
        """Returns the string used in legal documents for this type of instance

        :return: The string representation.
        """
        if self == DocumentPartType.BOOK:
            return "Cartea"
        elif self == DocumentPartType.TITLE:
            return "Titlul"
        elif self == DocumentPartType.CHAPTER:
            return "Capitolul"
        elif self == DocumentPartType.SECTION:
            return "Secţiunea"
        elif self == DocumentPartType.ARTICLE:
            return "Articolul"
        else:
            return None

    def get_possible_child_types(self) -> list["DocumentPartType"]:
        """Returns all possible child element types in decreasing hierarchical order."""
        if self == DocumentPartType.TOP:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.BOOK:
            return [
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.TITLE:
            return [
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.CHAPTER:
            return [DocumentPartType.SECTION, DocumentPartType.ARTICLE]
        elif self == DocumentPartType.SECTION:
            return [DocumentPartType.ARTICLE]
        elif self == DocumentPartType.ARTICLE:
            return []
        else:
            return []

    def get_possible_equal_or_greater_types(self) -> list["DocumentPartType"]:
        """Returns element types that are at the same hierarchical level or higher."""
        if self == DocumentPartType.TOP:
            return []
        elif self == DocumentPartType.BOOK:
            return [DocumentPartType.BOOK]
        elif self == DocumentPartType.TITLE:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
            ]
        elif self == DocumentPartType.CHAPTER:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
            ]
        elif self == DocumentPartType.SECTION:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
            ]
        elif self == DocumentPartType.ARTICLE:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        else:
            return []
