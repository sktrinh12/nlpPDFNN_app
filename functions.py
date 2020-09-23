import tensorflow as tf
from init import *
from collections import defaultdict  # to get unique values in list
import re
from datetime import datetime, timedelta
import bs4 as bs
import requests
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError
from io import BytesIO

stop_words_list = stopwords.words('english')

# rid of molecular formulas or starts with numbers
REGEX_PATTERN = re.compile(r'\w{3,}[. ]|[ ]\w|^\d+|\w{1,}\d+')

nsc_prefix_lst_short = [
    'V0', '0B', '0F', 'U5', '0W',
    'Q6', 'Q8', '0P', '0D', '0X',
    'U4', '0G', 'Q7', '0C', 'Z0',
    '0Y', '0M', '0E', '0V', '62',
    '0A', 'OK', 'OCD'
]

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

model_file = os.path.join(__file__.replace(
    'functions.py', ''), 'models/taxon_model')
model = tf.keras.models.load_model(model_file)


def allowed_file(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
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
    return [s for s in paragraph_list if not re.search(r'[\W+\d+]', s) and
            s not in stop_words_list and
            len(s) > 3 and
            re.search(r'[^ATCG]', s)]


def remove_nonascii(pdf_title):
    """remove non-ascii characters from request object for html parsing of pdf article title"""
    title = ""
    for l in pdf_title:
        num = ord(l)
        if (num >= 0):
            if (num <= 127):
                title += l
    return title


def download_file(pdf_title, download_url, file_path):
    """helper function to download pdf file if web-scraped successfully or use
    of OA API thru PubMed"""
    try:
        response = requests.get(download_url, headers=hdr)
        fp = os.path.join(file_path, f'{pdf_title}.pdf')
        with open(fp, 'wb') as f:
            f.write(response.content)
        print("Completed")
    except requests.exceptions.RequestException as e:
        # except urllib.error.HTTPError as e:
        print(f'error downloading the file - {e}')


def get_doi_links(soup):
    """find a tags from doi links if OA API doesn't work, use this web-scrape method"""
    dlink_lst = set()
    try:
        for u in soup.find_all('a'):
            try:
                if 'doi' in u['href']:
                    dlink_lst.add(u['href'])
                    print('DOI href: {0}'.format(u.get('href')))
            except KeyError:
                pass
    except (ConnectionResetError, Exception):
        dlink_lst.add(soup.find_all(
            'a', {"data-ga-action": "DOI"}).get('href'))
        print(f'first try, dlink: {list(dlink_lst)[0]}')
    return list(dlink_lst)


def pubmed_api(pmid):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={0}'.format(
        pmid)
    src = requests.get(url, headers=hdr).content
    # src = urllib.request.urlopen(url)
    sp = bs.BeautifulSoup(src, 'lxml')
    for tag_name in ['pmc', 'pmcid']:
        # get the numbers fo the PMC tag label i.e. PMC7449178
        pmc = sp.find('item', {'name': tag_name})
        if pmc:
            break
        else:
            continue
    if pmc:
        return re.search(r'\d+', pmc.text).group(0)
    else:
        return pmc


def pubmed_getpdf_filename(pmc):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={0}'.format(
        pmc)
    src = requests.get(url, headers=hdr).content
    # src = urllib.request.urlopen(url)
    sp = bs.BeautifulSoup(src, 'lxml')
    # find all self-uri tags and get the pdf attribute
    tag_types = ['self-uri', 'media']
    pdf_filename = None
    for tt in tag_types:
        try:
            pdf_filename = [x['xlink:href'] for x in sp.find_all(tt)
                            if x['xlink:href'].endswith('.pdf')][0]
            break
        except IndexError:
            pass
    return pdf_filename


def bs_parse_email_dl_pdf(url, file_path):
    '''use beautiful soup 4 to parse url link contents to download PDF file;
    return True/False if able/un-able to download'''
    source = requests.get(url, headers=hdr).content
    # source = urllib.request.urlopen(url).read()
    soup = bs.BeautifulSoup(source, 'lxml')
    pdf_title = soup.title.text
    # remove nonascii chars for pdf file name
    new_pdf_title = remove_nonascii(pdf_title)
    # try to use pubmed api to get pmc -> pdf file name -> download file
    successful_try = False
    # get the pmid number from the url
    pmid = url.split('/')[-2]
    # get the pmc number from pubmed eutils api
    pmc = pubmed_api(pmid)
    # if pmc exists in response; get pdf file name
    print(f'PMC: {pmc}')
    if pmc:
        pdf_fn = pubmed_getpdf_filename(pmc)
        print(f'PDF filename: {pdf_fn}')
        if pdf_fn:
            successful_try = True
            dlink = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{0}/pdf/{1}'.format(
                pmc, pdf_fn)
    else:
        try:
            # try scrape last; first get doi links
            dlink_lst = get_doi_links(soup)
            # create another soup object to parse; default to first element in list
            doi_src = requests.get(dlink_lst[0], headers=hdr).content
            # doi_src = urllib.request.urlopen(dlink_lst[0])
            doi_soup = bs.BeautifulSoup(doi_src, 'lxml')
            # find the meta tag with specific name
            doi_link = doi_soup.find('meta', {"name": 'citation_pdf_url'})
            # download the pdf file to specific file path
            print(doi_link)
            dlink = doi_link['content']
            successful_try = True
            print(f'dlink (scrape): {dlink}')
        except (requests.exceptions.RequestException, TypeError) as e:
            # except (ConnectionResetError, urllib.error.HTTPError):
            print('>>> could not scrape and not within the OpenAccess API: \n{0}\n{1}\n{2}'.format(
                url, pdf_title, e))

    if successful_try:
        download_file(new_pdf_title, dlink, file_path)
        print(f'Downloaded file: {pdf_title} ({dlink})')
    return (successful_try, pdf_title)


def load_text(load_input):  # just read raw text form or from pdf
    """read pdf file or text file from source"""
    if load_input.endswith('.txt'):  # just load from text
        with open(load_input, 'r') as f:
            text_body = f.readlines()
    else:  # load body of text after pdfminer
        try:
            text_body = pdf_parse(load_input)
        except PDFSyntaxError as e:
            text_body = "None"
    read_output = '\n'.join(text_body).strip().replace('\n', '')
    return read_output


def rm_files():
    '''after reading in the text and saving to uploads dir, then parsing the pdf
file; loop thru directory and if a file is older by one hour, delete file to
tidy'''
    parent_path = os.path.join(cwd, 'static', 'uploads')
    for fi in os.listdir(parent_path):
        file_path = os.path.join(parent_path, fi)
        stat = os.stat(file_path)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if datetime.now() - mtime > timedelta(hours=1):
            os.remove(file_path)

def filter_text_pos(pdf_pt):
    '''
    filter text based on part of speech tag and neighbouring characteristics
    '''
    filtered_nnp = []
    for i, pt in enumerate(pdf_pt):
        # if noun type tag
        if pt[1] in ["NNP", "NN"]:
            try:
                # if the neighbour is also a noun-type tag
                if pdf_pt[i+1][1] in ["NNP", "NN"]:
                    # if the neighbouring word is lowercase or uppercase
                    if pdf_pt[i+1][0].islower() or pdf_pt[i+1][0].isupper():
                        # if the first letter of the first word is uppercase
                        if pt[0][0].isupper():  # if first letter is capitalised
                            # append the word pair
                            filtered_nnp.append(f'{pt[0]} {pdf_pt[i+1][0]}')

            except IndexError:
                pass  # last index doesn't have a neighbour
    return filtered_nnp


def rtn_possible_wp(pdf_pt):
    '''
       returns possible word pairs that the model deeemed as a taxonomy name;
       and the filtered text list with part of speech tagging
    '''
    possible_list = []
    for wp in filter_text_pos(pdf_pt):
        res = model.predict([wp])
        print(wp, res)
        if res > 0.4:
            possible_list.append(wp)
    if possible_list:
        return list(defaultdict.fromkeys(possible_list).keys())
    return ["Sorry, failed to find taxonomy-like names in the document"]


def tokenise_render_v2(filepath):
    """tokenize the body of text from pdf file then remove file in static
    folder, then loop thru to check for taxonomy names"""
    text_body = load_text(filepath)
    rm_files()  # clean up files in static folder
    if len(text_body) < 20: # if the pdf file is corrupt/un-readable; set to 'None'
        return False, False
    token_pdf = word_tokenize(text_body)
    filtered_pdf = filter_nonchar(
        [w for w in token_pdf if not w in stop_words_list])
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
        return re.search(rf'{string}\w+', text_body).group(0)
    except AttributeError:
        return None


def extract_nsc(text_body):
    first_pass_regex_match = [rtn_regex_grp(
        p, text_body) for p in nsc_prefix_lst_short]
    second_pass_regex_match = re.findall(
        r'([J|C|N|Q|F|M|0]{1}[1-9]{2,}\w+)', text_body)
    cmb_regex_matches = list(
        set(second_pass_regex_match + [m for m in first_pass_regex_match if m]))
    try:
        vouch_nsc = [r for r in cmb_regex_matches if len(
            r) < 10 and len(r) > 4]
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
    vouch_nsc = list(filter(lambda x: not any(
        [c.islower() for c in x]), vouch_nsc))
    return vouch_nsc
