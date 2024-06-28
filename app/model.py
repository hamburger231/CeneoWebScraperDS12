import requests
from bs4 import BeautifulSoup
from flask import render_template, request, redirect, url_for, send_file
from app.utils import extract_content, transformations, selectors
import os
import io
import json
import pandas as pd
import numpy as np

class Product:
    def __init__(self, product_id):
        self.product_id = product_id
    def extract():
        product_id = Product.product_id
        if request.method == 'POST':
            url = f"https://www.ceneo.pl/{product_id}"
            response = requests.get(url)
            if response.status_code == requests.codes['ok']:
                page_dom = BeautifulSoup(response.text, "html.parser")
                opinions_count = extract_content(page_dom, "a.product-review__link > span")
                product_name = extract_content(page_dom, "h1")
                if opinions_count:
                    url = f"https://www.ceneo.pl/{product_id}#tab=reviews"
                    all_opinions = []
                    while(url):
                        response = requests.get(url)
                        response.status_code
                        page_dom = BeautifulSoup(response.text, "html.parser")
                        opinions = page_dom.select("div.js_product-review")
                        for opinion in opinions:
                            single_opinion = {
                                key : extract_content(opinion, *value)
                                    for key, value in selectors.items()
                            }
                            for key, value in transformations.items():
                                single_opinion[key] = value(single_opinion[key])
                            all_opinions.append(single_opinion)
                        try:
                            url = "https://www.ceneo.pl"+extract_content(page_dom, "a.pagination__next", "href")
                        except TypeError:
                            url = None
                    if not os.path.exists("app/data"):
                        os.mkdir("app/data")
                    if not os.path.exists("app/data/opinions"):
                        os.mkdir("app/data/opinions")
                    with open(f"app/data/opinions/{product_id}.json","w", encoding="UTF-8") as jf:
                        json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
                    MAX_SCORE = 5
                    opinions = pd.DataFrame.from_dict(all_opinions)
                    opinions.stars = opinions.stars.apply(lambda s: round(s*MAX_SCORE,1))
                    statistics = {
                        'product_id': product_id,
                        'product_name': product_name,
                        'opinions_count' : opinions_count,
                        'pros_count' : int(opinions.pros.astype(bool).sum()),
                        'cons_count' : int(opinions.pros.astype(bool).sum()),
                        'average_count' : (opinions.stars.mean()).round(2),
                        'score_distribution' : opinions.stars.value_counts().reindex(np.arange(0.5,5.5,0.5)).to_dict(),
                        'recommendation_distribution' : opinions.recommendation.value_counts(dropna=False).reindex([1,np.nan,0]).to_dict(),
                    }
                    if not os.path.exists("app/data/statistics"):
                        os.mkdir("app/data/statistics")
                    with open(f"app/data/statistics/{product_id}.json","w", encoding="UTF-8") as jf:
                        json.dump(statistics, jf, indent=4, ensure_ascii=False)
                    return redirect(url_for('product', product_id=product_id))
                return render_template("extract.html", error = "Product has no opinions.")
            return render_template("extract.html", error = "Product does not exist.")
        return render_template("extract.html")
    
    def xlsx():
        product_id = Product.product_id
        opinions = pd.read_json(f"app/data/opinions/{product_id}.json")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            opinions.to_excel(writer, index=False)
        buffer.seek(0)
        return send_file(buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{product_id}.xlsx")
    
    def csv():
        product_id = Product.product_id
        opinions = pd.read_json(f"app/data/opinions/{product_id}.json")
        buffer = io.BytesIO(opinions.to_csv(index=False).encode())
        return send_file(buffer, 'text/csv', as_attachment=True, download_name=f"{product_id}.csv")

class Opinion:
    def __init__(self, product_id):
        self.product_id = product_id
    def opinion(product_id):
        product_id = Product.product_id
        if os.path.exists("app/data/opinions"):
            opinions = pd.read_json(f'app/data/opinions/{product_id}.json')
        return render_template("product.html", product_id=product_id, opinions = opinions.to_html(classes="", index=False, table_id="opinions"))
    
class Scraper:
    def __init__(self, product_id):
        self.product_id = product_id

    def products():
        product_id = Product.product_id
        products_list = [filename.split(".")[0] for filename in os.listdir("app/data/opinions")]
        products = []
        for product_id in products_list:
            with open(f"app/data/statistics/{product_id}.json","r", encoding="UTF-8") as jf:
                statistics = json.load(jf)
                products.append(statistics)
        return render_template("products.html",  products=products)