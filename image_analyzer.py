import os

def read_image(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as file:
        return file.read()

def format_image_info(image_info):

    formatted_image_info = {
        "image_name": image_info["image_name"],
        "product_description": image_info["product_description"],
        "price": image_info["price"],
        "unit": image_info["unit"]
    }
    
    return formatted_image_info

def parse_image(image_info):

    final_image_info = []
    return final_image_info
