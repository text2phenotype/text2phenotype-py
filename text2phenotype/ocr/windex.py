import re, string

SPACE = ' '
STAR  = '*'
CRLF  = '\n'
PUNCT_TO_SPLIT_ON = {',', ';', '#', '!'}
COLON = ':'

def is_punctuation_line(line:str)->bool:
    """
    https://stackoverflow.com/questions/21696649/filtering-out-strings-that-only-contains-digits-and-or-punctuation-python
    :param line line of text, result of string.splitlines()
    :return: bool True if line is just spaces and punctuation
    """
    for l in range(0, len(line)):
        if not (line[l] == SPACE or line[l] in string.punctuation):
            return False
    return True

def is_long_token(token:str, max_len=30)->bool:
    """
    https://en.wikipedia.org/wiki/Longest_word_in_English

    :param token: word no whitespaces
    :param max_len: int maximum length
    :return: bool True token is longer than max_len=30, longest LEGAL word in english (happens to be medical)
    """
    return len(token) > max_len

def is_too_few_uniq_chars_for_len(token:str)->bool:
    """
    https://www.funtrivia.com/askft/Question112622.html

    :param token: word no whitespaces
    :return: bool True if the number of characters is severely unlikely to compose a real word of any kind
    """
    if len(token) > 20: return cnt_uniq_char(token) < 8
    if len(token) > 17: return cnt_uniq_char(token) < 7
    if len(token) > 15: return cnt_uniq_char(token) < 6
    if len(token) > 13: return cnt_uniq_char(token) < 4
    if len(token) >  6: return cnt_uniq_char(token) < 3

    return False

def cnt_uniq_char(token:str)->int:
    """
    :param token: word no whitespace
    :return: int count of unique characters
    """
    return len(''.join(set(token)))

def replace_non_ascii(token:str, replace_with = SPACE):
    """
    https://stackoverflow.com/questions/20078816/replace-non-ascii-characters-with-a-single-space
    https://theasciicode.com.ar/ascii-printable-characters/capital-letter-l-uppercase-ascii-code-76.html
    http://defindit.com/ascii.html
    :param token:
    :param replace_with:
    :return:
    """
    return ''.join(t if ord(t) < 128 else replace_with for t in token)

def replace_alphanum(token:str, replace_with=SPACE)->str:
    """
    https://stackoverflow.com/questions/12985456/replace-all-non-alphanumeric-characters-in-a-string/12985459
    :param token: word no whitespace
    :param replace_with:
    :return: string without numbers and letters
    """
    return re.sub('[^0-9a-zA-Z]+', replace_with, token)

def replace_consecutive_non_ascii(token:str, replace_with=SPACE):
    """
    https://stackoverflow.com/questions/20078816/replace-non-ascii-characters-with-a-single-space
    :param token:
    :param replace_with:
    """
    return re.sub(r'[^\x00-\x7F]', replace_with, token)


def is_consecutive_char(token:str, max_repeat=5):
    if len(token) < max_repeat:
        return False

    first = token[0]
    repeats = 1

    for c in range(1, len(token)):
        if token[c] == first:
            repeats = repeats+1
        else:
            repeats = 1
            first = token[c]

        if repeats > max_repeat:
            return True
    return False

def spaces(count:int)->str:
    """
    :param count: number of SPACE
    :return: string of SPACE chars with length "count"
    """
    return SPACE*count

def clean(token:str)->str:
    """
    :param token: single word no whitespace
    :return: str text with bad text replaced with SPACE(s)
    """
    if is_long_token(token):
        return spaces(len(token))

    if is_too_few_uniq_chars_for_len(token):
        return spaces(len(token))

    return replace_non_ascii(token)

def clean_text(text:str)->str:
    """
    :param text: document text, can contain whitespace
    :return: str text with bad text replaced
    """
    out = list()
    for line in text.splitlines():
        #replace some punctuations with space
        for c in PUNCT_TO_SPLIT_ON:
            line = line.replace(c, ' ')
        for i in range(len(line)):
            if line[i] == COLON:
                line = line[:i + 1] + ' ' + line[i + 1:]
        if is_punctuation_line(line):
            out.append(spaces(len(line)))
        else:
            for token in line.split():
                out.append(clean(token))
        out.append(CRLF)

    if CRLF == text[len(text)-1]:
        pass # OK last char was originally CRLF
    else:
        out.pop() # remove last CRLF

    return SPACE.join(out)