from zipfile import ZipFile
import re
from xml.etree import ElementTree
from unicodedata import normalize


def xps_to_text(file_path: str) -> str:
    xps_file = ZipFile(file_path)
    files_to_open = [file_info for file_info in xps_file.infolist()
                     if not file_info.is_dir() and
                     (re.match(r"Documents\/\d+\/Pages\/\d+\.fpage\/\[\d+\]\.piece", file_info.filename) or
                     re.match(r"Documents\/\d+\/Pages\/\d+\.fpage$", file_info.filename))]
    normalized_unicode_strings = []
    for file_info in files_to_open:
        with xps_file.open(file_info.filename) as opened_file:
            file_xml = ElementTree.parse(source=opened_file)
            for node in file_xml.findall(".//*[@UnicodeString]"):
                normalized_unicode_strings.append(normalize("NFKD", node.attrib["UnicodeString"]))

    return "\n".join(normalized_unicode_strings)
