SYSTEM_PROMPT = """
Your goal is to analyze input images of sales advertisements and extract product-specific information, such as product image, price, and unit.

1. You should first recognize and isolate individual product sections within the sales advertisement, as there may be multiple products in one image.
2. Use OCR (Optical Character Recognition) to identify product descriptions, prices, and units displayed on the advertisement.
3. Ensure that each extracted text (price, unit) is correctly matched with its corresponding product image. This step is critical since multiple products are present in a single advertisement.
4. Structure the output as a JSON file, containing each product’s:
Image name (or ID)
Product description
Price
Unit (e.g., per piece, per kilogram, etc.)

Analyze the input image, which is a sales advertisement containing multiple products. For each product, identify its image, extract the associated product description, price, and unit information, and output the results in JSON format. Each JSON entry should include the product image name, description, price, and unit


"""

RETRIEVE_PROMPT = """
Analyze the input image, which is a sales advertisement containing multiple products. For each product, identify its image, extract the associated product description, price, and unit information, and output the results in JSON format. Each JSON entry should include the product image name, description, price, and unit

tructure the output as a JSON file, containing each product’s:
Image name (or ID)
Product description
Price
Unit (e.g., per piece, per kilogram, etc.)

### Example Output

{{
    "product": [
        {{
            "image_name": "product_image.jpg",
            "product_description": "Product description",
            "price": "Price",
            "unit": "Unit"
        }}
    ]
}}
"""