import datetime
import io

import pytesseract
import re
import pandas as pd
from nltk.tokenize import word_tokenize
from PIL import Image
from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Secret key for sessions encryption
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/imagereader'

db = SQLAlchemy(app)

class data_ocr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    item_name = db.Column(db.String)
    item_price = db.Column(db.Float)

    def __init__(self, date, item_name, item_price):
        self.date = date
        self.item_name = item_name
        self.item_price = item_price

# mysql = MySQL(app)
# mysql.init_app(app)
#cursor = mysql.get_db().cursor()

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/scanner', methods=['GET', 'POST'])
def scan_file():
    if request.method == 'POST':
        dataset = pd.DataFrame(columns=['Product_code','Product_name','Price'])
        start_time = datetime.datetime.now()
        image_data = request.files['file'].read()

        scanned_text = pytesseract.image_to_string(Image.open(io.BytesIO(image_data)))

        print("Found data:", scanned_text)

        print("text line:", scanned_text.splitlines())
        for i, line in enumerate(scanned_text.splitlines()):
             if i < 8:
                  continue
             word_list = word_tokenize(line)

             if len(word_list) > 4 and any(i.isdigit() for i in re.sub(r'(?<=\d)[,\.]','',word_list[-2])):
                  item_words = word_list[1:-2]
                  item = ' '.join(item_words)
                  
                  product_code = word_list[0]
                  
                  price = word_list[-2]
                  if price[0] != 'Rp':
                       price = 'Rp' + price

                  insert = data_ocr(
                      date = start_time,
                      item_name=scanned_text,
                      item_price=0.0
                  )

                  db.session.add(insert)
                  dataset = dataset.append(pd.DataFrame([[product_code,item,price]],columns=dataset.columns))

        
        db.session.commit()
        session['data'] = {
            "text": scanned_text,
            "time": str((datetime.datetime.now() - start_time).total_seconds()),
            "dataset": dataset.values.tolist()
        }

        print("dataset list",dataset.values.tolist())

        return redirect(url_for('result'))


@app.route('/result')
def result():
    if "data" in session:
        data = session['data']
        return render_template(
            "result.html",
            title="Result",
            time=data["time"],
            text=data["text"],
            words=len(data["text"].split(" ")),
            dataset=data["dataset"]
        )
    else:
        return "Wrong request method."  

if __name__ == '__main__':
    # Setup Tesseract executable path
    pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'
    app.run(debug=True)
