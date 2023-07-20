from enum import Enum
from typing import List, Dict, Tuple


class OCRCoordinate:
    def __init__(self, text: str, page: int, top: int, right: int, bottom: int,
                 left: int, phi_type: str=None, phi_score: str=None,
                 phi_token_id: int = None, hyphen: bool=False,
                 new_line: bool=False, spaces: int=0, order: int=None,
                 document_index_first: int=None, document_index_last: int=None,
                 page_index_first: int=None, page_index_last: int=None):
        self.text = text

        self.page = page

        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

        self.phi_type = phi_type
        self.phi_score = phi_score
        self.phi_token_id = phi_token_id

        self.hyphen = hyphen
        self.new_line = new_line
        self.spaces = spaces

        self.order = order

        self.document_index_first = document_index_first
        self.document_index_last = document_index_last

        self.page_index_first = page_index_first
        self.page_index_last = page_index_last

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

    @property
    def length(self):
        return len(self.text) + self.spaces + self.new_line

    def to_dict(self):
        data = {"text": self.text,
                "page": self.page,
                "top": self.top,
                "right": self.right,
                "bottom": self.bottom,
                "left": self.left,
                "phi_type": self.phi_type,
                "phi_score": self.phi_score,
                "phi_token_id": self.phi_token_id,
                "hyphen": self.hyphen,
                "new_line": self.new_line,
                "spaces": self.spaces,
                "order": self.order,
                "document_index_first": self.document_index_first,
                "document_index_last": self.document_index_last,
                "page_index_first": self.page_index_first,
                "page_index_last": self.page_index_last,
                }

        return data

    @property
    def height(self):
        return self.bottom - self.top

    def have_gap_with(self, next_word, min_gap=None):
        if self.height == 0:
            return False
        # Check if there is a gap between this and provided word
        if not min_gap:
            min_gap = 50 / self.height
        gap = self.get_gap_with(next_word) / self.height
        if self.spaces <= 1 and gap > min_gap:
            return True

    def get_gap_with(self, next_word):
        # Check if there is a space between this and provided word
        gap = next_word.left - self.right
        return gap


class OCRPageInfo:
    def __init__(self, text: str=None, coordinates: List=None,
                 png_path: str=None, page: int=None):
        self.page = page
        self.text = text or ''
        self.coordinates = coordinates or list()  # list of OCRCoordinate objects
        self.png_path = png_path

    @classmethod
    def from_dict(cls, data):
        result = cls()
        result.page = data.get('page')
        result.text = data.get('text', '')
        result.png_path = data.get('png_path')

        coords_list = data.get('coordinates', list())
        result.coordinates = [OCRCoordinate.from_dict(co) for co in coords_list]

        return result

    def to_dict(self):
        data = {"page": self.page,
                "text": self.text,
                "coordinates": [c.to_dict() for c in self.coordinates],
                "png_path": self.png_path}

        return data


class Row:

    Types = Enum('Types', 'column tabular regular', module=__name__)

    def __init__(self, range: Tuple[int, int]=None, words: List=[]):
        self.range = range
        self.words = words
        self._type = None

    @property
    def type(self):
        if self._type is None:
            words = sorted(self.words, key=lambda w: w.left)
            gaps_count = 0
            row_len = len(words)
            for i, word in enumerate(words):
                if i < row_len - 1:
                    if word.have_gap_with(words[i + 1]):
                        gaps_count += 1
            if gaps_count == 1:
                return self.Types.column
            elif gaps_count > 1:
                return self.Types.tabular
            else:
                return self.Types.regular

        return self._type


class BlocksList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.top = min(l.top for l in self)
        self.right = max(l.right for l in self)
        self.left = min(l.left for l in self)
        self.bottom = max(l.bottom for l in self)
        self.len = len(self)
        self.order = None

    @property
    def height(self):
        return self.bottom - self.top


class Box(object):
    def __init__(self, left, right, top, bottom):
        super(Box, self).__init__()
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def h_center(self):
        return (self.left + self.right) / 2
    

    def __repr__(self):
        return f'{self.left} {self.right} {self.top} {self.bottom}'
