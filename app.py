import os
import json
from flask import Flask, render_template, request
import google.generativeai as genai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 🔑 Gemini API anahtarını environment variable ile al
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return "Dosya yüklenmedi!"

    file = request.files['image']
    if file.filename == '':
        return "Dosya seçilmedi!"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    prompt = """
    Fotoğraftaki tabakta bulunan yemekleri tanı.
    Her biri için yalnızca adını ve tahmini kalorisini belirt.
    JSON formatında döndür:
    {
      "foods": [
        {"name": "Tavuk", "calories": 200},
        {"name": "Pilav", "calories": 250}
      ]
    }
    Lütfen sadece geçerli JSON döndür.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([
        prompt,
        genai.upload_file(filepath)
    ])

    result_text = response.text.strip().replace("```json", "").replace("```", "")

    try:
        data = json.loads(result_text)
        foods = data.get("foods", [])
        total_calories = sum([
            int(item.get("calories", 0)) 
            for item in foods 
            if isinstance(item.get("calories"), (int, float))
        ])
    except Exception:
        foods = [{"name": "Belirlenemedi", "calories": "?"}]
        total_calories = 0

    return render_template('index.html', image_path=filepath, foods=foods, total=total_calories)

if __name__ == "__main__":
    os.makedirs("static/uploads", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
