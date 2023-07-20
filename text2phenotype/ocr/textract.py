import os
from typing import Union, List, Tuple, Any

from text2phenotype.common.log import operations_logger
from text2phenotype.common import common
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY
from text2phenotype.ocr.trp import Document, Page, Line, Cell, Table


def load_textract_response(json_file_path):
    """Get json'd response from textract json path"""
    return common.read_json(json_file_path)


def textract_doc(response: Union[dict, list]) -> Document:
    """
    Thin wrapper around trp.Document, converting textract json to parsable Document object
    :param response: output .json from textract job
    :returns: trp.Document
    """
    return Document(response)


def textract_json_to_txt(response: Union[dict, list], lines_only: bool = False) -> str:
    """
    Format the json blocks and tables as a raw text output
    This will output the tables in linear order across cells then rows

    :param response: output .json from textract job
        Generally a list of hierarchical blocks from a document
    :param lines_only: boolean, if true, only use lines (not table formatting) for raw text output
        This will write text out in linear line by line across a page, without formatting
        for a given cell structure in a table
    :returns: str for the content on the target page
    """
    doc = textract_doc(response)
    text_out = ""
    for page_num, page in enumerate(doc.pages):
        page_text = page.text if lines_only else parse_page_text(page)
        text_out += page_text
        if page_num < len(doc.pages) - 1:
            # don't add page break on last page
            text_out += OCR_PAGE_SPLITTING_KEY[0]

    return text_out


def parse_page_text(page: Page) -> str:
    """
    Filter out the duplicate content in a page, and write to string
    Words may appear twice in a page, either as a child of a line, or a child of a cell.
    Drop the lines that contain the same content as a cell, and insert the table
    into the expected page position

    TODO: this does NOT currently deal with nested tables well!
    We don't have good examples of nested tables to test with...

    :param page: A Page from a trp Document
    :return: the raw text for the page, including tables written by cell order, rather than line order
    """
    objects = {
        "lines": [],
        "tables": [],
        "keyvalues": [],
    }
    for item in page.content:
        if hasattr(item, "block"):
            if item.block["BlockType"] == "LINE":
                objects["lines"].append(item)
            elif item.block["BlockType"] == "TABLE":
                objects["tables"].append(item)
        else:
            # is a keyvalue, which we wont use here (already in line or table)
            objects["keyvalues"].append(item)

    # remove Lines that are already in Tables
    not_table_lines = _collect_not_table_lines(line_list=objects["lines"], table_list=objects["tables"])

    # get the top and left coordinates to see the rough order of position, and sort
    # don't add any key_value_sets, those already exist as Lines
    object_positions = [
        (
            item,
            item.geometry.boundingBox.top,
            item.geometry.boundingBox.left,
            item.geometry.boundingBox.height,
        )
        for item in not_table_lines
    ] + [
        (
            item,
            item.geometry.boundingBox.top,
            item.geometry.boundingBox.left,
            item.geometry.boundingBox.height,
        )
        for item in objects["tables"]
    ]
    # a Line often has a height of 0.009 to 0.012, so round 'top' to 0.xxxx
    round_top_digits = 3  # round the "top" boundingBox position
    # make rounding more coarse if lines are taller, reduces positional noise
    line_height_threshold = 0.012
    object_positions_sorted = sorted(
        object_positions,
        key=_get_position_sort_key,
    )

    # concatenate all of the text
    text_out = ""
    for item, top, left, height in object_positions_sorted:
        if isinstance(item, Table):
            text_out += table_to_text(item, delimiter="\t")
        else:
            text_out += item.text + "\n"

    return text_out


def _get_position_sort_key(x: Tuple[Any, float, float, float], round_top_digits=3):
    """
    Return rounded top position and left position, for use in layout sorting
    :param x: expects a tuple with (item, top, left, height)
    :returns: Tuple(rounded_top, left)
    """
    # make rounding more coarse if lines are taller, reduces positional noise
    line_height_threshold = 0.012
    round_to = round_top_digits if x[3] < line_height_threshold else round_top_digits - 1
    return round(x[1], round_to), x[2]


def _collect_not_table_lines(line_list: List[Line], table_list: List[Table]) -> List[Line]:
    """
    Given a list of page lines and page tables, remove any lines that are already represented in a table

    :param line_list: list of trp.Line objects from a Page
    :param table_list: list of trp.Table objects from a Page
    :returns: list of Lines that are NOT represented in a table
    """
    # get the ids for all "Words" that are in a table Cell in a flat set
    cell_word_ids = []
    for table in table_list:
        for row in table.rows:
            for cell in row.cells:
                cell_word_ids.extend(get_child_ids(cell))
    cell_word_ids = set(cell_word_ids)
    # get a list of all lines that arent in a table Cell
    not_table_lines = []
    table_lines = []
    for line in line_list:
        line_children_in_table = set(get_child_ids(line)).intersection(cell_word_ids)
        if not line_children_in_table:
            not_table_lines.append(line)
        else:
            # collecting these for debugging purposes
            # a Line may not have ALL of the words in a cell, so one or more matching word is excluded
            table_lines.append(line)
    if table_lines:
        operations_logger.debug(f"Found {len(table_lines)} duplicate lines in tables; filtering them out")
    return not_table_lines


def get_child_ids(item: Union[Line, Cell]):
    """
    Get the child IDs from the item content
    """
    ids = []
    if hasattr(item, "content"):
        # is a Cell
        ids = [child.id for child in item.content]
    elif hasattr(item, "words"):
        # is a Line
        ids = [child.id for child in item.words]
    else:
        raise ValueError("Dunno how you got here, check the item type?")
    return ids


def tables_to_csv(doc: Document, filename: str):
    """
    Given a document, write out all identified tables to a CSV with the given filename
    :param doc: trp.Document, a parsed textract response
    :param filename: target path and filename to write the output CSV file
    """
    output_rows = []
    for p, page in enumerate(doc.pages):
        for t, table in enumerate(page.tables):
            # csv.writer deals with the unequal lengths of inner (row) lists, so this works
            output_rows.append([f"PAGE {p}", f"TABLE {t}"])
            for r, row in enumerate(table.rows):
                row_out = []
                for c, cell in enumerate(row.cells):
                    row_out.append(cell.text)
                output_rows.append(row_out)
            if t < len(page.tables) - 1 and p < len(doc.pages) - 1:
                output_rows.append([])  # empty row between tables and pages

    common.write_csv(output_rows, filename)
    return filename


def table_to_text(table: Table, delimiter: str = "\t") -> str:
    """
    Parse a Textract Table to a text string
    :param table: the table object
    :param delimiter: what string or character to use as a cell delimiter, default is TAB '\t'
    :returns: str
    """
    output_text = ""
    for r, row in enumerate(table.rows):
        for c, cell in enumerate(row.cells):
            output_text += cell.text
            if c < len(row.cells) - 1:
                output_text += delimiter
        output_text += "\n"
    return output_text


def convert_textract_json_files(input_dir, output_dir, lines_only=False):
    """
    Iterate through all .json files in input_dir and write as raw text to output_dir
    """
    json_files = common.get_file_list(input_dir, file_type=".json", recurse=True)
    os.makedirs(output_dir, exist_ok=True)
    for i, json_file_path in enumerate(json_files):
        text_fn, _ = os.path.splitext(os.path.basename(json_file_path))
        response = load_textract_response(json_file_path)
        operations_logger.info(f"[{i+1}/{len(json_files)}] Parsing {json_file_path}")
        out_text = textract_json_to_txt(response, lines_only=lines_only)
        out_text_path = os.path.join(output_dir, text_fn + ".txt")
        common.write_text(out_text, out_text_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(usage="Convert Textract JSON to TXT")
    parser.add_argument("input_dir", type=str, help="path to the input directory")
    parser.add_argument("output_dir", type=str, help="path to the output directory")
    parser.add_argument("--lines-only", action="store_true")
    args = parser.parse_args()

    convert_textract_json_files(args.input_dir, args.output_dir, lines_only=args.lines_only)

