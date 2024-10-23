from flask import Flask, redirect, render_template, request, jsonify, Response
import os
import numpy as np
from roboflow import Roboflow
from ultralytics import YOLO
import httpx
from bs4 import BeautifulSoup

app = Flask(__name__)

os.makedirs('./images', exist_ok=True)

def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (" ", "_")).rstrip()

rf = Roboflow(api_key="AXwpMdB3TsNEHit6rI2Z")
roboflow_project = rf.workspace("ganesh73005").project("cat-rvm7j")
roboflow_model = roboflow_project.version(1).model

yolo_model = YOLO('best.pt')



import google.generativeai as genai
generation_config = {
               "temperature": 1,
               "top_p": 0.95,
               "top_k": 64,
               "max_output_tokens": 40000,
               "response_mime_type": "text/plain",
}
genai.configure(api_key="AIzaSyBwW6NRgXEWDGtkSUhYkBWIkqEKYoo_TZQ")
ai_model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
  
        )
chat_session = ai_model.start_chat(
                history=[
                      ]
        )

def predict(image,language):
    roboflow_output = predict_disease_with_roboflow(image,language)
    yolo_output = predict_disease_with_yolo(image,language)
    
    json_data = {
        'roboflow_output': roboflow_output,
        'yolo_output': yolo_output,
    }
    
    response = jsonify(json_data)
    return response

def fetch_ai_recommendations(disease_classes, target_language='en'):
    recommendations = []
    for disease_class in disease_classes:
        if disease_class == 'dermatophilus':
            prompt = f"What are the vitamin supplements name in English and recommended healing activities for cattle's dermatophilosis  ? Give supplements names in English and healing activities in {target_language}"
        elif disease_class == 'pediculosis':
            prompt = f"What are the vitamin supplements name in English and recommended healing activities for cattle's pediculosis  ? Give supplements names in English and healing activities in {target_language}"
        elif disease_class == 'ringworm':
            prompt = f"What are the vitamin supplements name in English and recommended healing activities for cattle's ringworm  ? Give supplements names in English and healing activities in {target_language}"
        print(prompt)
        if prompt:  # Check if prompt is not empty
            response = chat_session.send_message(prompt)
            
            recommendations_text = response.text.strip()
            recommendations.append(recommendations_text)
        else:
            recommendations.append("No prompt generated for disease class {}".format(disease_class))
    
    return recommendations

def fetch_ai_2_recommendations(disease_class, target_language='en'):
    prompt = ""
    if disease_class == 'FMD':
        prompt = f"What are the  vitamin supplements  name in English and recommended healing activities for cattle's FMD Disease ? Give supplements names in English and healing activities in {target_language}"
    elif disease_class == 'IBK':
        prompt = f"What are the vitamin supplements name in English and recommended healing activities for cattle's Eye infectious keratoconjunctivitis  ? Give supplements names in English and healing activities in {target_language}"
    elif disease_class == 'LSD':
        prompt = f"What are the vitamin supplements name in English and recommended healing activities for cattle's lumpy skin  ? Give supplements names in English and healing activities in {target_language}"
    elif disease_class == 'NOR':
        prompt = f"What are the recommended activities for healthy cattle maintenance with supplements without side effects ? Give in {target_language}"


    response = chat_session.send_message(prompt)

    
    recommendations_text = response.text.strip()
    return recommendations_text

default_treatments = {
    'FMD': "Oxytetracycline",
    'LSD': "Antibiotics like Oxytetracycline or Streptomycin to treat secondary bacterial infections\n"
           "Anti-inflammatory drugs like Flunixin meglumine to reduce swelling and pain",
    'IKC': "Antibiotics like Oxytetracycline or Streptomycin to treat bacterial infections\n"
           "Topical antibiotics like Neomycin or Bacitracin to treat conjunctivitis",
    'dermatophilus': "Antibiotics like Oxytetracycline or Streptomycin to treat bacterial infections\n"
                     "Topical antiseptics like Iodine or Chlorhexidine to treat skin lesions",
    'pediculosis': "Insecticides like Ivermectin or Doramectin to kill lice\n"
                   "Topical treatments like Pyrethrin or Permethrin to kill lice and their eggs",
    'ringworm': "Antifungal medications like Griseofulvin or Itraconazole to treat fungal infections\n"
                "Topical antifungals like Clotrimazole or Miconazole to treat skin lesions",
}


def predict_disease_with_roboflow(img_path, language='en'):
    response = roboflow_model.predict(img_path, confidence=40, overlap=30).json()
    predictions = response['predictions']
    selected_classes = [prediction['class'] for prediction in predictions if prediction['class'].lower() not in ['foot infected', 'mouth infected', 'lumpy skin', 'healthy cow', 'healthy_cow_mouth']]
    print(selected_classes)
    recommendations = fetch_ai_recommendations(selected_classes, language)
    output = ""
    for i, disease_class in enumerate(selected_classes):
        output += f"Disease {i + 1}: {disease_class.capitalize()}\n\nMedicines: {default_treatments[disease_class]}\n\nRecommended Activities: {recommendations[i]}\n\n"
    return output.strip()

def predict_disease_with_yolo(img_path, language='en'):
    results = yolo_model.predict(source=img_path)
    probs = results[0].probs
    class_names = yolo_model.names

    if probs is not None:
        max_prob_index = probs.top1
        max_class_name = class_names[max_prob_index]
        recommendations = fetch_ai_2_recommendations(max_class_name, language)
        output = f"Disease: {max_class_name.capitalize()}\n\nMedicines: {default_treatments[max_class_name]}\n\nRecommended Activities: {recommendations}\n\n"
    else:
        output = "No predictions found."

    return output

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/s')
def s():
    return render_template('static/uploads')

@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/index')
def ai_engine_page():
    return render_template('index.html')

@app.route('/mobile-device')
def mobile_device_detected_page():
    return render_template('mobile-device.html')

@app.route('/map')
def map_page():
    return render_template('map.html') 

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        language = request.form.get("language")
        filename = image.filename
        
        save_path = f'C:/Users/ganes/Documents/LiveStock/App/static/uploads/{filename}'
        image.save(save_path)
       
        pred = predict(save_path,language) 
        title = "HERE YOU GO"
        img_url = f'../static/uploads/{filename}'
        
        print(pred)

        prevent = pred.get_json()  
        roboflow_output_html = prevent['roboflow_output'].replace('\n', '<br>').replace("**"," ")
        yolo_output_html = prevent['yolo_output'].replace('\n', '<br>').replace("**"," ")

        return render_template('submit.html', title=title, 
                               roboflow_output=roboflow_output_html, 
                               yolo_output=yolo_output_html,
                               img_url=img_url)

@app.route('/product-list', methods=['GET', 'POST'])
def product_list():
    if request.method == 'POST':
        query = request.form.get('query')
        product_items = scrape_amazon_in(query)
        return render_template('product_list.html',  product_items=product_items)
    return render_template('product_list.html')


def scrape_amazon_in(query):
    
    product_items = []
    print("Scraping Amazon for query:", query) 
    for page in range(1, 2):  
        url = f"https://www.amazon.com/s?k={query}-indian sellers&page={page}"
        print(url)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = httpx.get(url, headers=headers)
        print(response)
        soup = BeautifulSoup(response.text, "html.parser")
        print(soup)

        for product in soup.select(".s-result-item"):
            title_tag = product.select_one("h2 a span")
            price_tag = product.select_one(".a-price-whole")
            link_tag = product.select_one("h2 a")

            if title_tag and price_tag and link_tag:
                result = {
                    "link": product.select_one("img").attrs["src"],
                    "title": title_tag.text,
                    "price": price_tag.text,
                    "product_link": "https://www.amazon.com" + link_tag.attrs["href"]
                }
                product_items.append(result)
    print("Scraped products:", product_items)  # Debugging line
    return product_items

if __name__ == '__main__':
    app.run(debug=True)