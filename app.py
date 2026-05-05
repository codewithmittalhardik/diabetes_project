from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

def train_model_on_fly():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'diabetes.csv')
        df = pd.read_csv(csv_path)
        
        selected_features = ['Glucose', 'BloodPressure', 'BMI', 'Age']
        
        # Clean data
        df[selected_features] = df[selected_features].replace(0, np.nan)
        df.fillna(df.median(), inplace=True)
        
        X = df[selected_features]
        y = df['Outcome']
        
        scaler_obj = StandardScaler()
        X_scaled = scaler_obj.fit_transform(X)
        
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_scaled, y)
        print("Model trained successfully on the fly from CSV!")
        return rf_model, scaler_obj
    except Exception as e:
        print(f"Error training model on the fly: {e}")
        return None, None

# Train the model when the app starts
model, scaler = train_model_on_fly()

# Initialize Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/dataset', methods=['GET'])
def get_dataset():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'diabetes.csv')
        df = pd.read_csv(csv_path)
        # Convert first 100 rows to JSON
        data = df.head(100).to_dict(orient='records')
        columns = df.columns.tolist()
        return jsonify({"columns": columns, "data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict_diabetes():
    if model is None or scaler is None:
        return jsonify({"error": "Machine Learning model not initialized."}), 500

    data = request.json
    try:
        features = np.array([[
            float(data['Glucose']),
            float(data['BloodPressure']),
            float(data['BMI']),
            float(data['Age'])
        ]])
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input data."}), 400

    features_scaled = scaler.transform(features)
    probability = float(model.predict_proba(features_scaled)[0][1])
    
    # Use a custom clinical threshold (0.35) instead of the default 0.50
    # This increases sensitivity, ensuring extremely high glucose levels aren't missed
    prediction = 1 if probability >= 0.35 else 0

    precautions = []
    foods_to_avoid = []

    if prediction == 1:
        precautions = [
            "Monitor blood sugar levels regularly.",
            "Engage in at least 30 minutes of moderate exercise daily.",
            "Maintain a healthy weight.",
            "Manage stress through relaxation techniques.",
            "Follow up with your healthcare provider for a personalized plan."
        ]
        foods_to_avoid = [
            "Sugary beverages (soda, sweet tea)",
            "Refined carbohydrates (white bread, pasta)",
            "Trans fats (margarine, certain baked goods)",
            "Highly processed snacks",
            "Foods with added sugars"
        ]

    return jsonify({
        "prediction": prediction,
        "probability": probability,
        "is_diabetic": bool(prediction == 1),
        "precautions": precautions,
        "foods_to_avoid": foods_to_avoid
    })


@app.route('/check-food', methods=['POST'])
def check_food():
    if not groq_client:
        return jsonify({"error": "Groq API key not configured. Cannot perform AI food checking."}), 500
    
    data = request.json
    food_name = data.get('food_name')
    if not food_name:
        return jsonify({"error": "Food name is required."}), 400
    
    prompt = f"""
    You are an expert nutritionist and diabetes educator.
    A user is asking about the food item: "{food_name}".
    
    You must provide your response EXACTLY in the following format, with no extra text before or after:

    VERDICT: [SAFE, AVOID, or MODERATE]
    REASONING: [1-2 sentences explaining its general glycemic index and if it's safe for long-term consumption for someone looking to prevent or manage diabetes.]
    ALTERNATIVES: [List 3 specific similar foods they CAN eat instead, separated by commas]
    """

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        advice = chat_completion.choices[0].message.content
        return jsonify({"food": food_name, "advice": advice})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
