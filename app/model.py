import requests
from bs4 import BeautifulSoup
from flask import send_file
from app.utils import extract_content, transformations, selectors
from matplotlib import pyplot as plt
from io import BytesIO
import os
import io
import json
import pandas as pd
import numpy as np
import base64

class Product:
    def __init__(self, product_id):
        self.product_id = product_id
        self.scraper = Scraper(product_id)
        self.opinions = []

    def extract_opinions(self):
        self.opinions = self.scraper.get_opinions()
        if not self.opinions:
            return False  
        self.save_opinions()
        self.save_statistics()
        return True
    
    def products():
        products_list = [filename.split(".")[0] for filename in os.listdir("app/data/opinions")]
        products = []
        for product_id in products_list:
            with open(f"app/data/statistics/{product_id}.json", "r", encoding="UTF-8") as jf:
                statistics = json.load(jf)
                products.append(statistics)
        return products
    
    def xlsx(self):
        opinions = pd.read_json(f"app/data/opinions/{self.product_id}.json")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            opinions.to_excel(writer, index=False)
        buffer.seek(0)
        return send_file(buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{self.product_id}.xlsx")
    
    def csv(self):
        opinions = pd.read_json(f"app/data/opinions/{self.product_id}.json")
        buffer = io.BytesIO(opinions.to_csv(index=False).encode())
        return send_file(buffer, 'text/csv', as_attachment=True, download_name=f"{self.product_id}.csv")
    
    def saved_opinions(product_id):
        filepath = f"app/data/opinions/{product_id}.json"
        if os.path.exists(filepath):
            return pd.read_json(filepath)
        return None
    
    def save_opinions(self):
        if not os.path.exists("app/data"):
                os.mkdir("app/data")
        if not os.path.exists("app/data/opinions"):
            os.mkdir("app/data/opinions")
        with open(f"app/data/opinions/{self.product_id}.json","w", encoding="UTF-8") as jf:
            json.dump(self.opinions, jf, indent=4, ensure_ascii=False)
    
    def save_statistics(self):
        MAX_SCORE = 5
        opinions = pd.DataFrame.from_dict(self.opinions)
        opinions['stars'] = opinions['stars'].apply(lambda s: round(s * MAX_SCORE, 1))
        statistics = {
            'product_id': self.product_id,
            'product_name': self.scraper.product_name,
            'opinions_count': len(self.opinions),
            'pros_count': int(opinions.pros.astype(bool).sum()),
            'cons_count': int(opinions.cons.astype(bool).sum()),
            'average_score': opinions.stars.mean().round(2),
            'score_distribution': opinions.stars.value_counts().reindex(np.arange(0.5, 5.5, 0.5)).to_dict(),
            'recommendation_distribution': opinions.recommendation.value_counts(dropna=False).reindex([1, np.nan, 0]).to_dict(),
        }
        if not os.path.exists("app/data/statistics"):
            os.mkdir("app/data/statistics")
        with open(f"app/data/statistics/{self.product_id}.json","w", encoding="UTF-8") as jf:
            json.dump(statistics, jf, indent=4, ensure_ascii=False)
    
    def charts(self):
        opinions = pd.DataFrame.from_dict(self.opinions)
        score_distribution = opinions.score.value_counts().reindex(np.arange(0.5,5.5,0.5))
        fig, ax = plt.subplots()
        score_distribution.plot.bar()
        ax.bar_label(ax.containers[0], label_type='edge', fmt=lambda l: int(1) if l > 0 else '')
        ax.set_xlabel("Number of stars")
        ax.set_ylabel("Number of opinions")
        ax.set_title(f"Opinions score histogram for product {self.product_id}")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_data

class Opinion:
    
    def __init__(self, not_transformed):
        self.not_transformed = not_transformed
        self.opinion = self.transform()

    def transform(self):
        transformed = {
            key : extract_content(self.not_transformed, *value)
            for key, value in selectors.items()
        }
        for key, value in transformations.items():
            transformed[key] = value(transformed[key])
        return transformed
    
    def get_opinion(self):
        return self.opinion
    
class Scraper:
    def __init__(self, product_id):
        self.product_id = product_id
        self.opinions = []
        self.product_name = None  
        self.url = "https://www.ceneo.pl/"

    def fetch(self, url):
        response = requests.get(url)
        if response.status_code == requests.codes.ok:
            return BeautifulSoup(response.text, "html.parser")
        return None

    def scrape(self):
        url = f'{self.url}{self.product_id}'
        page_dom = self.fetch(url)
        if page_dom is None:
            return
        self.product_name = extract_content(page_dom, "h1")
        while url:
            page_dom = self.fetch(url)
            if page_dom is None:
                break
            opinions = page_dom.select("div.js_product-review")
            for opinion in opinions:
                transformed_opinion = Opinion(opinion)
                self.opinions.append(transformed_opinion.get_opinion())
            try:
                url = "https://www.ceneo.pl" + extract_content(page_dom, "a.pagination__next", "href")
            except TypeError:
                url = None

    def get_opinions(self):
        self.scrape()
        return self.opinions