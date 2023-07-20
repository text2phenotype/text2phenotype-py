import os
import subprocess

from lxml.html import parse

from text2phenotype.common.log import operations_logger


def pdf2png(pdf_file, png_file=None, density='300', quality='100'):
    """
    Convert PDF to PNG file for OCR image processing
    :param pdf_file: fillepath to PDF input
    :param png_file: filepath to PNG output. If not provided, default is
    pdf_file+'.png'
    :return:
    """
    if png_file is None:
        png_file = f'{pdf_file}.png'
    operations_logger.debug(f'...converting.... {pdf_file}')
    subprocess.run(['convert', '-adjoin', '-background', 'White',
                    '-density', str(density), pdf_file, '-quality',
                    str(quality), '-append', png_file])
    return png_file


def png2txt(png_file, txt_file=None):
    """
    Convert png file to txt file.
    :param png_file: filepath to PNG input.
    :param txt_file: filepath to TXT output. If not provided, default is
    png_file+'.txt'
    :return:
    """
    txt_file = f'{png_file}.txt'
    operations_logger.debug(f'...extracting.... {png_file}')
    subprocess.run(['tesseract', png_file, png_file, '-psm', '3'])

    return txt_file

def create_hocr(img_path):
    cmd2 = ['tesseract', img_path, img_path, 'hocr']
    operations_logger.debug(f'creating hocr file with this command: {" ".join(cmd2)}')
    out2 = subprocess.run(cmd2)


def get_phi_coords(img_path, phi_words):
    operations_logger.debug(f'getting phi coords for this image: {img_path}')
    create_hocr(img_path)
    # open HOCR XHTML file; get all OCR words as list "ocr_words".
    root = parse(f'{img_path}.hocr')

    # clean-up intermediate *.hocr file
    if os.path.exists(f'{img_path}.hocr'):
        os.remove(f'{img_path}.hocr')

    body = root.find('body')
    ocr_words = body.findall('.//span[@class="ocrx_word"]')

    i = 0
    word_dict = {}
    for ocr_word in ocr_words:
        node = ocr_word.text_content()
        if node is not None:
            # checking for an exact match (case-insensitive) leaves too many
            # phi words unredacted
            # if node.lower() not in [w.lower() for w in phi_words]:
                # continue

            # checking if a phi word is included in an ocr'd word catches more
            # phi words, but also some non-phi words (like gastrointestinal
            # because it contains the name Tina)
            is_phi = False
            for w in phi_words:
                # if w.lower() in node.lower():
                if w in node or node in w:  # changed to inexact match for demos
                    is_phi = True
            if not is_phi:
                continue

            coordinates = ocr_word.get("title")
            coordinates = coordinates.split(" ")
            # remove word "bbox" from attribute value.
            coordinates.pop(0)
            word = {}
            word["text"] = node
            word["left"] = coordinates[0]
            word["top"] = coordinates[1]
            word["right"] = coordinates[2]
            word["bottom"] = coordinates[3][0:-1]
            word_dict[i] = word
        i += 1
    return word_dict
