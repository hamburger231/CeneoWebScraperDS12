from app import app
from flask import render_template, send_file, request, redirect, url_for
from app.model import Product, Opinion, Scraper

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product = Product(product_id)
        if product.extract_opinions():
            return redirect(url_for('product', product_id=product_id))
        return render_template("extract.html", error="Product has no opinions or does not exist")
    return render_template("extract.html")

@app.route('/products')
def products():
    products = Product.products()
    if products:
        return render_template("products.html", products=products)
    return render_template("noproducts.html")

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/product/<product_id>')
def product(product_id):
    opinions = Product.saved_opinions(product_id)
    if opinions is not None:
        return render_template("product.html", product_id=product_id, opinions=opinions.to_html(classes="table table-warning table-striped"), table_id="opinions", index=False)
    return redirect(url_for('extract'))

@app.route('/download_json/<product_id>')
def download_json(product_id):
    return send_file(f"data/opinions/{product_id}.json", 'text/json', as_attachment=True)

@app.route('/download_csv/<product_id>')
def download_csv(product_id):
    product_id = Product(product_id)
    return Product.csv(product_id)

@app.route('/download_xlsx/<product_id>')
def download_xlsx(product_id):
    product_id = Product(product_id)
    return Product.xlsx(product_id)

@app.route("/chart/<product_id>")
def send_chart(product_id):
    product = Product(product_id)
    img = product.charts()
    return send_file(img)
@app.route("/charts/<product_id>")
def charts(product_id):
    return render_template("charts.html", product_id=product_id)