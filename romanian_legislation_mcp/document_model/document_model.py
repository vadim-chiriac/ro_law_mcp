from dataclasses import dataclass
import enum

class DocumentElementName(enum.Enum):
    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3

class DocumentPart:
    name: DocumentElementName
    children: list['DocumentPart']
    article_numbers: list[int]
    start_pos: int
    end_pos: int
    
    def __init__(self, name: DocumentElementName, start_pos, end_pos):
        self.name = name
        self.children = []
        self.article_numbers = []
        self.start_pos = start_pos
        self.end_pos = end_pos
    
    def has_articles(self):
        return len(self.article_numbers) > 0
    

class DocumentModel:
    def __init__(self):
        self.children: list[DocumentPart] = []