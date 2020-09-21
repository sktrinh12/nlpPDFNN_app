import tensorflow as tf
from init import *
from collections import defaultdict # to get unique values in list
import re
from os import path
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from io import BytesIO

stop_words_list = stopwords.words('english')

REGEX_PATTERN = re.compile(r'\w{3,}[. ]|[ ]\w|^\d+|\w{1,}\d+') #rid of molecular formulas or starts with numbers

nsc_prefix_lst_short = [
    'V0', '0B', '0F', 'U5', '0W',
    'Q6', 'Q8', '0P', '0D', '0X',
    'U4', '0G', 'Q7', '0C', 'Z0',
    '0Y', '0M', '0E', '0V', '62',
    '0A', 'OK', 'OCD'
]


model_file = path.join(__file__.replace('functions.py', ''), 'models/taxon_model')
model = tf.keras.models.load_model(model_file)

def allowed_file(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".",1)[1]
    if ext.upper() in app.config['ALLOWED_FILE_EXT']:
        return True
    else:
        return False

def allowed_filesize(filesize):
    if int(filesize) <= app.config["MAX_FILESIZE"]:
        return True
    else:
        return False

# cleaning function for science words
def filter_nonchar(paragraph_list):
    """if any non-char is present or numeric and not a stop word and length > 3 and excludes ATGC nucleic acids strings"""
    return [s for s in paragraph_list if not re.search(r'[\W+\d+]', s) and \
            s not in stop_words_list and \
            len(s) > 3 and \
            re.search(r'[^ATCG]', s)]

def load_text(load_input): #just read raw text form or from pdf
    if load_input.endswith('.txt'): # just load from text
        with open(load_input, 'r') as f:
            text_body = f.readlines()
    else: # load body of text after pdfminer
        text_body = pdf_parse(load_input)
    read_output = '\n'.join(text_body).strip().replace('\n','')
    return read_output

def rm_file(filepath):
    if os.path.exists(filepath): #after reading in the text and saving to var, delete file to tidy
        os.remove(filepath)

def filter_text_pos(pdf_pt):
    '''
    filter text based on part of speech tag and neighbouring characteristics
    '''
    filtered_nnp = []
    for i,pt in enumerate(pdf_pt):
        # if noun type tag
        if pt[1] in ["NNP", "NN"]:
            try:
                # if the neighbour is also a noun-type tag
                if pdf_pt[i+1][1] in ["NNP", "NN"]:
                    # if the neighbouring word is lowercase or uppercase
                    if pdf_pt[i+1][0].islower() or pdf_pt[i+1][0].isupper():
                        # if the first letter of the first word is uppercase
                        if pt[0][0].isupper(): # if first letter is capitalised
                            # append the word pair
                            filtered_nnp.append(f'{pt[0]} {pdf_pt[i+1][0]}' )

            except IndexError:
                pass # last index doesn't have a neighbour
    return filtered_nnp

def rtn_possible_wp(pdf_pt):
    '''
       returns possible word pairs that the model deeemed as a taxonomy name;
       and the filtered text list with part of speech tagging
    '''
    possible_list = []
    for wp in filter_text_pos(pdf_pt):
        res = model.predict([wp])
        print(wp,res)
        if res > 0.4:
            possible_list.append(wp)
    if possible_list:
        return list(defaultdict.fromkeys(possible_list).keys())
    return ["Sorry, failed to find taxonomy-like names in the document"]


def tokenise_render_v2(filepath):
    text_body = load_text(filepath)
    if text_body:
        rm_file(filepath) #clean up file in static folder
    token_pdf = word_tokenize(text_body)
    filtered_pdf = filter_nonchar([w for w in token_pdf if not w in stop_words_list])
    pdf_pt = pos_tag(filtered_pdf)
    poss_wp = rtn_possible_wp(pdf_pt)
    # remove word pairs that have all uppercases
    new_poss_wp = []
    for wp in poss_wp:
        check_upper = []
        for w in wp.split(' '):
            if w.isupper():
                check_upper.append(True)
        if sum(check_upper) == 0:
            new_poss_wp.append(wp)
    poss_nscs = extract_nsc(text_body)
    return new_poss_wp, poss_nscs

def pdf_parse(filepath):
    manager = PDFResourceManager()
    retstr = BytesIO()
    layout = LAParams(all_texts=True)
    device = TextConverter(manager, retstr, laparams=layout)
    with open(filepath, 'rb') as pdf_file:
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(pdf_file, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()
        device.close()
        retstr.close()
    return text.decode('utf-8')

def nsc_exclude(ls_vouch_nsc):
    if isinstance(ls_vouch_nsc, list):
        res_list = []
        for n in ls_vouch_nsc:
            if 'C' in n and 'H' in n:
                pass
            else:
                res_list.append(n)
    else:
        res_list = ls_vouch_nsc
    return res_list

def rtn_regex_grp(string, text_body):
    try:
        return re.search(rf'{string}\w+',text_body).group(0)
    except AttributeError:
        return None

def extract_nsc(text_body):
    first_pass_regex_match = [rtn_regex_grp(p, text_body) for p in nsc_prefix_lst_short]
    second_pass_regex_match = re.findall(r'([J|C|N|Q|F|M|0]{1}[1-9]{2,}\w+)', text_body)
    cmb_regex_matches = list(set(second_pass_regex_match + [m for m in first_pass_regex_match if m]))
    try:
        vouch_nsc = [r for r in cmb_regex_matches if len(r) < 10 and len(r) > 4]
    except:
        vouch_nsc = ["Didn't find any NSCs"]
    print(f'NSCs: {vouch_nsc}')
    if len(cmb_regex_matches) > 1:
        vouch_nsc = nsc_exclude(vouch_nsc)
        if not vouch_nsc:
            # if after removing CH formulas and the list becomes empty
            vouch_nsc = ["Didn't find any NSCs"]
        vouch_nsc = list(defaultdict.fromkeys(vouch_nsc).keys())
    else:
        if not vouch_nsc:
            vouch_nsc = ["Didn't find any NSCs"]
    # filter the nscs by values that have all uppercase
    vouch_nsc = list(filter(lambda x: not any([c.islower() for c in x]), vouch_nsc))
    return vouch_nsc
