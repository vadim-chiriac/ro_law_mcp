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
        self.id = uuid.uuid4()
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


class DocumentElementType(enum.Enum):
    """Class responsible for legal document elementy hierarchy order and helper methods"""

    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3
    SECTION = 4
    ARTICLE = 5
    
    def to_string(self) -> str:
        return self.to_keyword()

    def to_keyword(self) -> str:
        """Returns the string used in legal documents for this type of instance

        :return: The string representation.
        """
        if self == DocumentElementType.BOOK:
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
        if self == DocumentElementType.TOP:
            return [
                DocumentElementType.BOOK,
                DocumentElementType.TITLE,
                DocumentElementType.CHAPTER,
                DocumentElementType.SECTION,
                DocumentElementType.ARTICLE,
            ]
        elif self == DocumentElementType.BOOK:
            return [
                DocumentElementType.TITLE,
                DocumentElementType.CHAPTER,
                DocumentElementType.SECTION,
                DocumentElementType.ARTICLE,
            ]
        elif self == DocumentElementType.TITLE:
            return [
                DocumentElementType.CHAPTER,
                DocumentElementType.SECTION,
                DocumentElementType.ARTICLE,
            ]
        elif self == DocumentElementType.CHAPTER:
            return [DocumentElementType.SECTION, DocumentElementType.ARTICLE]
        elif self == DocumentElementType.SECTION:
            return [DocumentElementType.ARTICLE]
        elif self == DocumentElementType.ARTICLE:
            return []
        else:
            return []

    def get_possible_equal_or_greater_types(self) -> list["DocumentElementType"]:
        """Returns element types that are at the same hierarchical level or higher."""
        if self == DocumentElementType.TOP:
            return []
        elif self == DocumentElementType.BOOK:
            return [DocumentElementType.BOOK]
        elif self == DocumentElementType.TITLE:
            return [
                DocumentElementType.BOOK,
                DocumentElementType.TITLE,
            ]
        elif self == DocumentElementType.CHAPTER:
            return [
                DocumentElementType.BOOK,
                DocumentElementType.TITLE,
                DocumentElementType.CHAPTER,
            ]
        elif self == DocumentElementType.SECTION:
            return [
                DocumentElementType.BOOK,
                DocumentElementType.TITLE,
                DocumentElementType.CHAPTER,
                DocumentElementType.SECTION,
            ]
        elif self == DocumentElementType.ARTICLE:
            return [
                DocumentElementType.BOOK,
                DocumentElementType.TITLE,
                DocumentElementType.CHAPTER,
                DocumentElementType.SECTION,
                DocumentElementType.ARTICLE,
            ]
        else:
            return []
