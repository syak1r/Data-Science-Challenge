import re 
from flask import Flask, jsonify, request, send_file
import nltk
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder 
from flasgger import swag_from
import csv
import pandas as pd
import io
import os

app = Flask(__name__) 

with open('src/new_kamusalay.csv', encoding = 'latin-1', mode='r') as infile:
    reader = csv.reader(infile)
    ids = {rows[0]:rows[1] for rows in reader}

app.json_encoder = LazyJSONEncoder 
swagger_template = dict(
    info = {
        'title' : LazyString(lambda: 'API Documentation for Cleaning Text'),
        'version' : LazyString(lambda: '1.0.0'),
        'description' : LazyString(lambda: 'Dokumentasi API untuk kebutuhan Cleaning Text'),
    },
    host = LazyString(lambda: request.host)
    )
    
swagger_config = {
    'headers': [],
    'specs':[
        {
            'endpoint': 'docs',
            'route': '/docs.json',
        }
        ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/docs'
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

def casefolding(review):
    review = review.lower()
    return review

def tokenize(review):
    token = nltk.word_tokenize(review)
    return token

def filtering(review):
    # Remove angka termasuk angka yang berada dalam string
    # Remove non ASCII chars
    review = re.sub(r'[^\x00-\x7f]', r'', review)
    review = re.sub(r'(\\u[0-9A-Fa-f]+)', r'', review)
    review = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", review)
    review = re.sub(r'\\u\w\w\w\w', '', review)
    # Remove link web
    review = re.sub(r'http\S+', '', review)
    # Remove @username
    review = re.sub('@[^\s]+', '', review)
    # Remove #tagger
    review = re.sub(r'#([^\s]+)', '', review)
    # Remove simbol, angka dan karakter aneh
    review = re.sub(r"[.,:;+!\-_<^/=?\"'\(\)\d\*]", " ", review)
    return review

def replaceThreeOrMore(review):
    # Pattern to look for three or more repetitions of any character, including newlines (contoh goool -> gol).
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1", review)


def convertToSlangword(review):
    kamus_slangword = ids
    pattern = re.compile(r'\b( ' + '|'.join (kamus_slangword.keys())+r')\b') # Search pola kata (contoh kpn -> kapan)
    content = []
    for kata in review:
        filteredSlang = pattern.sub(lambda x: kamus_slangword[x.group()],kata) # Replace slangword berdasarkan pola review yg telah ditentukan
        content.append(filteredSlang.lower())
    review = content
    return review

def filter_text(text):
    content = []
    text_filter = casefolding(text)
    text_filter = filtering(text_filter)
    text_filter = replaceThreeOrMore(text_filter)
    text_filter = tokenize(text_filter)
    text_filter = convertToSlangword(text_filter) 
    text_filter = content.append(" ".join(text_filter))
    text_filter_2 = content
    return text_filter_2

@swag_from('docs/text_processing.yml', methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    text = request.form.get('data_text') 
    text = filter_text(text)
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah di proses",
        'data': text
    }
    
    response_data = jsonify(json_response)
    return response_data

@swag_from('docs/upload.yml', methods=['POST'])
@app.route('/text-processing_upload', methods=['POST'])
def text_processing_upload():
    if request.method == 'POST':
        file = request.files['file']
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        datasets = [df]
        for teks in datasets: 
            text_awal = teks['Tweet']
            teks = teks['Tweet'].apply(casefolding)
            teks = teks.apply(filtering)
            teks = teks.apply(replaceThreeOrMore)
            teks = teks.apply(tokenize)
            teks = teks.apply(convertToSlangword)
            teks = teks.apply(" ".join)

        review_dict = {'Tweet Awal': text_awal,'Tweet Bersih': teks}
        df = pd.DataFrame(review_dict, columns = ['Tweet Awal','Tweet Bersih'])
        df.to_csv('src/data-bersih.csv', sep= ',' , encoding='utf-8')
        json_response = {
            'status_code': 200,
            'description': "Data CSV berhasil dicleaning",
            'url_download': "http://127.0.0.1:5000/download_csv"
        }    
    response_data = jsonify(json_response)
    return response_data

@app.route('/download_csv')
def download_csv():

	path = "./src/data-bersih.csv"
	return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug = True) 