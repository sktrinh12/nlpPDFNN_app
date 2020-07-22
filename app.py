from werkzeug.utils import secure_filename
from functions import *

title = 'NLP PDF journal article keyword extraction'

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html', the_title=title)

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
                        ], ["N1238980", "C891324", "J9834508", "M812703489", "N7104382"]

    pdf_file = ''
    if pdf_file == "": #no file name
        msg = "Must select a file"
        print(msg)
        flash(msg, 'warning')
        # return redirect('/', code=302)

    return render_template("upload_pdf.html", \
            filename='test_file.file', \
            poss_wp=poss_wp, \
            nscs=poss_nscs, \
            the_title='title')

@app.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        if request.files and "filesize" in request.cookies:
            print(f'filesize={request.cookies.get("filesize")}')
            check_file_size = allowed_filesize(request.cookies.get("filesize"))
            if not check_file_size:
                #based on filesize
                msg = f'File exceeded maximum size, ({int(request.cookies.get("filesize"))/1e6:0.2f}MB > 5MB)'
                print(msg)
                flash(msg, 'warning')
                # return redirect('/', code=302)

            pdf_file = request.files["pdf_up"]

            if pdf_file.filename == "": #no file name
                msg = "Must select a file"
                print(msg)
                flash(msg, 'warning')
                # return redirect('/', code=302)

            if allowed_file(pdf_file.filename) : #file type
                filename = secure_filename(pdf_file.filename)
                filepath = os.path.join(app.config['PDF_UPLOADS'], filename)
                pdf_file.save(filepath)
                msg = f"pdf file saved ... {pdf_file}"
                print(msg)

                poss_wp, poss_nscs = tokenise_render_v2(filepath)

                return render_template("upload_pdf.html", \
                        filename=filename, \
                        poss_wp=poss_wp, \
                        nscs=poss_nscs, \
                        the_title=title)
            else:
                msg = 'That file is not acceptable, should be .txt or .pdf'
                if pdf_file.filename != "" and check_file_size: # hackish way to prevent double flash messasge
                    flash(msg, 'warning')
                    print(msg)
                # return redirect('/', code=302)
        return render_template('index.html',the_title=title)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050)
