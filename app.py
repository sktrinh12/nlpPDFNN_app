from werkzeug.utils import secure_filename
from functions import *
from math import ceil


@app.route('/')
def index():
    return render_template('insert_text_page.html', switch_tab_var='email')


@app.route("/test", methods=["GET", "POST"])
def test():
    poss_wp, poss_nscs = [
        "resemble tanke",
        "labored asfk",
        "fog pweoiqr",
        "ride 234jlkcv",
        "painstaking aspfoiu23",
        "vegetable aspoij2",
        "possessive aspoiuj",
        "wrist 98s0afup",
        "existence apsofij",
        "chance japsofiu",
        "behave p93845ji",
        "roomy aslifj;",
        "arrange i2jlksf",
        "company 2oi3u4hs",
        "broad 23iu4hjljas",
        "cars jaklsaf;",
        "box alksjfa;ks",
    ], ["N1238980",
        "C891324",
        "J9834508",
        "M812703489",
        "N7104382",
        "N7104382",
        "N7104382",
        "N7104382",
        "N7104382",
        "N7104382",
        "N7104382"]

    # length_nscs = len(poss_nscs)
    # rows = ceil(length_nscs / 5)
    # print(length_nscs,rows)

    return render_template("insert_text_page.html",
                           filename='test_file.file',
                           file_exists=False,
                           wp=poss_wp,
                           nscs=poss_nscs,
                           switch_tab_var='email')

@app.route("/return-file/<filename>")
def return_file(filename):
    full_path = os.path.join(cwd, 'static', 'uploads', filename)
    return send_file(full_path)

@app.route("/insert-text", methods=["GET", "POST"])
def insert_text():
    if request.method == "POST":
        email_link = request.form['url-input']
        if email_link:
            if email_link.startswith('https://') and \
                    re.search(r'\d+', email_link.split('/')[-2]) and \
                    email_link.endswith('/'):
                print(f"email link: {email_link}")
                # poss_wp = ["resemble tanke", "labored asfk","fog pweoiqr", "ride 234jlkcv"]
                # poss_nscs = ["N7104382", "N7104382", "N7104382", "N7104382"]
                return_tries, filename = bs_parse_email_dl_pdf(
                    email_link, app.config['PDF_UPLOADS'])
                if return_tries:
                    filepath = os.path.join(
                        app.config['PDF_UPLOADS'], f'{filename}.pdf')
                    msg = f"pdf file saved ... {filepath}"
                    print(msg)
                    file_exists = False
                    if os.path.exists(filepath):
                        file_exists = True
                    poss_wp, poss_nscs = tokenise_render_v2(filepath)
                    if poss_wp == False and poss_nscs == False:
                        msg = f"The PDF file seems corrupted. Not able to parse\
                            the file. Please download manually and use the\
                            'Upload file' link instead"
                        print(msg)
                        flash(msg, 'warning')
                        return render_template('insert_text_page.html',
                                               switch_tab_var='email')
                    print(poss_wp)
                    # length_nscs = len(poss_nscs)
                    # rows = ceil(length_nscs / 5)
                    # print(length_nscs, rows)
                    return render_template('insert_text_page.html',
                                           email_link=email_link,
                                           wp=poss_wp,
                                           nscs=poss_nscs,
                                           # rows=rows,
                                           # length_nscs=length_nscs,
                                           filename=filename,
                                           file_exists=file_exists,
                                           switch_tab_var='email')
                msg = f"That PDF file is not available in the Open Access subset\
                and it cannot be retrieved via the PMC OA Service. Not every\
                article within PMC is available through the OA Service,\
                generally due to copyright restrictions. Please download\
                manually and upload using the 'Upload file' tab"
                print(msg)
                flash(msg, 'warning')
            else:
                msg = f"The link's format appears to be invalid - {request.form['url-input']}"
                print(msg)
                flash(msg, 'warning')
        else:
            msg = 'Please enter an email link to the journal article'
            print(msg)
            flash(msg, 'warning')
    # has to render template and not redirect (nginx will crap itself)
    return render_template('insert_text_page.html', switch_tab_var='email')
    # return redirect('/')


@app.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        if request.files and "filesize" in request.cookies:
            print(f'filesize={request.cookies.get("filesize")}')
            if not allowed_filesize(request.cookies.get("filesize")):
                # based on filesize
                msg = f'File exceeded maximum size, ({int(request.cookies.get("filesize"))/1e6:0.2f}MB > 5MB)'
                print(msg)
                flash(msg, 'warning')

            pdf_file = request.files["pdf_up"]

            if pdf_file.filename == "":  # no file name
                msg = "Must select a file"
                print(msg)
                flash(msg, 'warning')

            if allowed_file(pdf_file.filename):  # file type
                filename = secure_filename(pdf_file.filename)
                filepath = os.path.join(app.config['PDF_UPLOADS'], filename)
                pdf_file.save(filepath)
                msg = f"pdf file saved ... {pdf_file}"
                print(msg)

                poss_wp, poss_nscs = tokenise_render_v2(filepath)
                print(poss_wp)
                # length_nscs = len(poss_nscs)
                # rows = ceil(length_nscs / 5)

                return render_template("upload_pdf.html",
                                       filename=filename,
                                       wp=poss_wp,
                                       nscs=poss_nscs)
                # length_nscs=length_nscs,
                # rows=rows)
            else:
                msg = 'That file is not acceptable, should be .txt or .pdf'
                if pdf_file.filename != "":  # hackish way to prevent double flash messasge
                    flash(msg, 'warning')
                    print(msg)

    return render_template('upload_pdf.html', switch_tab_var='file')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=True)
