from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import base64
from io import BytesIO
from torch.cuda.amp import autocast
import requests
import logging
import hmac
import hashlib

app = Flask(__name__)
CORS(app)

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Stable Diffusion model configuration
model_id = "stabilityai/stable-diffusion-2-1"
device = "cuda" if torch.cuda.is_available() else "cpu"
access_token = "your_huggingface_access_token"  # Replace with your HuggingFace access token

# Load the Stable Diffusion pipeline
logging.info("Loading Stable Diffusion Pipeline...")
try:
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        token=access_token
    )
    pipe = pipe.to(device)
    pipe.enable_sequential_cpu_offload()
    logging.info("Pipeline loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load Stable Diffusion Pipeline: {e}")
    pipe = None

# Environment variables for sensitive information
PRINTIFY_API_KEY = "your_printify_api_key"  # Replace with your Printify API key
SHOP_ID = "your_shop_id"  # Replace with your Printify shop ID
SHOPIFY_WEBHOOK_SECRET = "your_shopify_webhook_secret"  # Replace with your Shopify webhook secret

# In-memory product status tracking (for testing purposes)
published_products = {}

# Function to verify webhook authenticity
def verify_webhook(data, hmac_header):
    calculated_hmac = base64.b64encode(
        hmac.new(
            SHOPIFY_WEBHOOK_SECRET.encode('utf-8'),
            data,
            hashlib.sha256
        ).digest()
    )
    return hmac.compare_digest(calculated_hmac, hmac_header.encode('utf-8'))

# Generate image function
def generate_image(description):
    logging.info(f"Generating image for description: {description}")
    full_prompt = f"a cat {description}"

    if pipe is None:
        logging.error("Stable Diffusion pipeline is not loaded.")
        return None

    with torch.no_grad():
        torch.cuda.empty_cache()
        with autocast():
            try:
                image = pipe(prompt=full_prompt, num_inference_steps=15, guidance_scale=3.5).images[0]
                logging.info("Image generated successfully.")
            except Exception as ex:
                logging.error(f"Failed to generate image: {ex}")
                return None

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str

# Upload image to Printify
def upload_image_to_printify(image_data, file_name):
    url = "https://api.printify.com/v1/uploads/images.json"
    headers = {
        "Authorization": f"Bearer {PRINTIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "file_name": file_name,
        "contents": image_data
    }

    logging.info("Uploading image to Printify...")
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logging.info("Image uploaded successfully.")
            return response.json()
        else:
            logging.error(f"Failed to upload image to Printify: {response.status_code}")
            return {}
    except Exception as ex:
        logging.error(f"Exception during image upload: {ex}")
        return {}

# Flask API routes
@app.route('/api/generate', methods=['POST'])
def generate():
    description = request.json.get('description', '')
    if not description:
        return jsonify({"error": "Description not provided"}), 400

    # Generate image
    image_data = generate_image(description)
    if not image_data:
        return jsonify({"error": "Image generation failed"}), 500

    file_name = description.replace(' ', '_') + '.png'

    # Upload image to Printify
    upload_response = upload_image_to_printify(image_data, file_name)
    if not upload_response.get('id'):
        return jsonify({"error": "Failed to upload image to Printify"}), 500

    # Placeholder for further logic (e.g., creating products, publishing to Shopify)
    return jsonify({"message": "Image generated and uploaded successfully!"})

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5000)
