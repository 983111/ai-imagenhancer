from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageEnhance
import io
import base64
from flask_cors import CORS
import uuid
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def enhance_image(image):
    # Professional photo enhancement - no filters that destroy quality
    
    # Contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.08)
    
    # Color
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.2)
    
    # Sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    
    return image

@app.route('/enhance', methods=['POST'])
def enhance():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    try:
        img = Image.open(file.stream)
        
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        enhanced_img = enhance_image(img)
        
        img_id = str(uuid.uuid4())
        original_path = os.path.join(UPLOAD_FOLDER, f'{img_id}_original.jpg')
        enhanced_path = os.path.join(UPLOAD_FOLDER, f'{img_id}_enhanced.jpg')
        
        img.save(original_path, 'JPEG', quality=95)
        enhanced_img.save(enhanced_path, 'JPEG', quality=95)
        
        img_buffer = io.BytesIO()
        enhanced_img.save(img_buffer, format='JPEG', quality=95)
        enhanced_b64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        orig_buffer = io.BytesIO()
        img.save(orig_buffer, format='JPEG', quality=95)
        original_b64 = base64.b64encode(orig_buffer.getvalue()).decode()
        
        return jsonify({
            'id': img_id,
            'original': f'data:image/jpeg;base64,{original_b64}',
            'enhanced': f'data:image/jpeg;base64,{enhanced_b64}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<img_id>', methods=['GET'])
def download(img_id):
    enhanced_path = os.path.join(UPLOAD_FOLDER, f'{img_id}_enhanced.jpg')
    
    if not os.path.exists(enhanced_path):
        return jsonify({'error': 'Image not found'}), 404
    
    return send_file(enhanced_path, mimetype='image/jpeg', as_attachment=True, download_name='enhanced_image.jpg')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
