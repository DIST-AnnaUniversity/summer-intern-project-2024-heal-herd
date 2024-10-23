import os
from flask import Flask, request, render_template_string
import httpx
from bs4 import BeautifulSoup

app = Flask(__name__)

# Ensure the images directory exists
os.makedirs('./images', exist_ok=True)

# Function to sanitize file names
def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (" ", "_")).rstrip()

# CSS styles (note the use of double curly braces for Jinja2)
css_template = """
body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background-color: #f8f8f8;
    color: #333;
    margin: 0;
    padding: 0;
}}
.container {{
    width: 80%;
    margin: 40px auto;
    padding: 20px;
    background-color: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    border-radius: 10px;
}}
.search-bar {{
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
}}
.search-bar input[type="text"] {{
    width: 60%;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 5px 0 0 5px;
    font-size: 16px;
}}
.search-bar button {{
    padding: 15px;
    border: none;
    background-color: #ff9900;
    color: #fff;
    font-size: 16px;
    border-radius: 0 5px 5px 0;
    cursor: pointer;
}}
.search-bar button:hover {{
    background-color: #e68a00;
}}
.product-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: center;
}}
.product-item {{
    width: 300px;
    border: 1px solid #ddd;
    padding: 20px;
    background-color: #fff;
    border-radius: 10px;
    transition: all 0.3s ease-in-out;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}
.product-item:hover {{
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}}
.product-item img {{
    width: 100%;
    height: auto;
    border-radius: 10px;
}}
.product-item h3 {{
    font-size: 18px;
    font-weight: bold;
    margin-top: 15px;
}}
.product-item p {{
    font-size: 16px;
    color: #ff9900;
    margin-top: 10px;
    font-weight: bold;
}}
.product-item p::before {{
    content: "₹ ";
}}
"""

# HTML template for the product list page
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product List</title>
    <style>{{ css_template | safe }}</style>
    <script>
        function searchProducts() {
            let input = document.getElementById('search').value.toLowerCase();
            let items = document.getElementsByClassName('product-item');
            for (let i = 0; i < items.length; i++) {
                let title = items[i].getElementsByTagName('h3')[0].innerText.toLowerCase();
                if (title.includes(input)) {
                    items[i].style.display = '';
                } else {
                    items[i].style.display = 'none';
                }
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <form method="POST" class="search-bar">
            <input type="text" id="search" name="query" placeholder="Search for products...">
            <button type="submit">Search</button>
        </form>
        <div class="product-list">
            {{ product_items }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    product_html = ""
    print("Request method:", request.method)  # Debugging line

    if request.method == 'POST':
        query = request.form.get('query')
        print("Search query:", query)  # Debugging line
        product_items = scrape_amazon_in(query)

        for product in product_items:
            sanitized_title = sanitize_filename(product['title'])
            product_html += f"""
            <div class="product-item">
                <a href="{product['product_link']}">
                    <img src="{product['link']}" alt="{product['title']}">
                    <h3>{product['title']}</h3>
                    <p>{product['price']}</p>
                </a>
            </div>
            """
        print("Product HTML generated:", product_html)  # Debugging line

    return render_template_string(html_template, css_template=css_template, product_items=product_html)

def scrape_amazon_in(query):
    # Scrape Amazon India based on the user input query
    product_items = []
    print("Scraping Amazon for query:", query)  # Debugging line
    for page in range(1, 2):  # Limiting to 1 page for simplicity
        url = f"https://www.amazon.in/s?k={query}&page={page}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = httpx.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        for product in soup.select(".s-result-item"):
            title_tag = product.select_one("h2 a span")
            price_tag = product.select_one(".a-price-whole")
            link_tag = product.select_one("h2 a")

            if title_tag and price_tag and link_tag:
                result = {
                    "link": product.select_one("img").attrs["src"],
                    "title": title_tag.text,
                    "price": price_tag.text,
                    "product_link": "https://www.amazon.in" + link_tag.attrs["href"]
                }
                product_items.append(result)
    print("Scraped products:", product_items)  # Debugging line
    return product_items

if __name__ == '__main__':
    app.run(debug=True)
