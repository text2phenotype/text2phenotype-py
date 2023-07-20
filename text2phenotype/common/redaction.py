import os
import subprocess

from typing import List

from text2phenotype.common.log import operations_logger
from text2phenotype.ocr.data_structures import OCRPageInfo, OCRCoordinate




def create_redacted_img(img_path: str, phi_coords: List,
                        output_path: str=None, left_buffer: int=10,
                        right_buffer: int=5) -> None:
    operations_logger.debug(f'creating redacted image from: {img_path}')
    if output_path is None:
        output_path = f'{os.path.splitext(img_path)[0]}.redacted.png'

    cmd3 = ['convert', img_path, '-fill', 'black', '-pointsize', '12']
    for word in phi_coords:
        cmd_parts = ['-draw', f'rectangle {word.left - left_buffer},{word.top},'
                              f'{word.right + right_buffer},{word.bottom}']
        cmd3.extend(cmd_parts)
    cmd3.append(output_path)

    operations_logger.debug(" ".join(cmd3))
    out3 = subprocess.run(cmd3, check=True)


def create_redacted_pdf(ocr_responses: List[OCRPageInfo],
                        ocr_coords: List[OCRCoordinate],
                        working_dir: str) -> str:
    png_out_dir = os.path.join(working_dir, 'redacted', 'png')
    os.makedirs(png_out_dir, exist_ok=True)

    pdf_out_dir = os.path.join(working_dir, 'redacted', 'pdf')
    os.makedirs(pdf_out_dir, exist_ok=True)

    redact_coords = dict()
    for coord in ocr_coords:
        if coord.phi_type is not None:
            co_list = redact_coords.setdefault(coord.page, [])
            co_list.append(coord)

    # iterate over pages
    for page in ocr_responses:
        png_fnam, _ = os.path.splitext(os.path.basename(page.png_path))
        redacted_fnam = f'{png_fnam}_redacted'
        redacted_filepath = f"{png_out_dir}/{redacted_fnam}.png"
        create_redacted_img(page.png_path, redact_coords.get(page.page, []),
                            redacted_filepath)
        cmd = ['convert', redacted_filepath,
               os.path.join(pdf_out_dir, f'{redacted_fnam}.pdf')]
        subprocess.run(cmd, check=True)

    # now concatenate all pdfs
    redacted_filepath = os.path.join(working_dir, 'redacted.pdf')
    cmd = ["pdfunite", os.path.join(pdf_out_dir, '*'), redacted_filepath]
    p = subprocess.Popen(' '.join(cmd), shell=True)
    output, err = p.communicate()

    return redacted_filepath
