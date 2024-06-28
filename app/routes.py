from app import app
from flask import render_template, send_file, request
from app.model import Product, Opinion, Scraper

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    setattr(Product, "product_id", request.form.get("product_id"))
    return Product.extract()
@app.route('/products')
def products():
    return Scraper.products()

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/product/<product_id>')
def product(product_id):
    return Opinion.opinion(product_id)

@app.route('/download_json/<product_id>')
def download_json(product_id):
    return send_file(f"data/opinions/{product_id}.json", 'text/json', as_attachment=True)

@app.route('/download_csv/<product_id>')
def download_csv(product_id):
    return Product.csv(product_id)

@app.route('/download_xlsx/<product_id>')
def download_xlsx(product_id):
    return Product.xlsx(product_id)

@app.route("/charts/<product_id>")
def charts(product_id):
    return render_template("charts.html", product_id=product_id)