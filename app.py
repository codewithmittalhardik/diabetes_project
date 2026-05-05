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
        csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'diabetes_early_stage_cleaned.csv')
        df = pd.read_csv(csv_path)
        
        selected_features = [
            'Polyuria', 'Polydipsia', 'Age', 'Gender', 
            'sudden weight loss', 'Irritability', 'visual blurring', 'Polyphagia'
        ]
        
        X = df[selected_features]
        y = df['class']
        
        scaler_obj = StandardScaler()
        X_scaled = scaler_obj.fit_transform(X)
        
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_scaled, y)
        print("Model trained successfully on the fly from cleaned dataset!")
        return rf_model, scaler_obj
    except Exception as e:
        print(f"Error training model on the fly: {e}")
        return None, None

model, scaler = train_model_on_fly()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/severity-guide')
def severity_guide():
    return render_template('severity.html')


@app.route('/tech-stack')
def tech_stack():
    return render_template('tech_stack.html')


@app.route('/food-checker')
def food_checker():
    return render_template('food_checker.html')


@app.route('/predict', methods=['POST'])
def predict_diabetes():
    if model is None or scaler is None:
        return jsonify({"error": "Machine Learning model not initialized."}), 500

    data = request.json
    try:
        features = np.array([[
            float(data['Polyuria']),
            float(data['Polydipsia']),
            float(data['Age']),
            float(data['Gender']),
            float(data['sudden weight loss']),
            float(data['Irritability']),
            float(data['visual blurring']),
            float(data['Polyphagia'])
        ]])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400

    features_scaled = scaler.transform(features)
    probability = float(model.predict_proba(features_scaled)[0][1])
    
    # Count positive indicators: Polyuria, Polydipsia, sudden weight loss, Irritability, visual blurring, Polyphagia
    symptom_keys = ['Polyuria', 'Polydipsia', 'sudden weight loss', 'Irritability', 'visual blurring', 'Polyphagia']
    symptom_count = sum(1 for key in symptom_keys if float(data.get(key, 0)) == 1)
    
    prediction = 1 if probability >= 0.5 else 0
    
    if prediction == 0:
        severity_level = 0
        risk_level = "Low"
        precautions = [
            "Maintain your current healthy lifestyle.",
            "Continue regular physical activity (150 mins/week).",
            "Get a routine check-up once a year."
        ]
        foods_to_avoid = ["Excessive refined sugars", "Highly processed snacks"]
    else:
        if symptom_count <= 2:
            severity_level = 1
            risk_level = "Moderate"
            precautions = [
                "Monitor your glucose levels monthly.",
                "Increase fiber intake and focus on low-sugar fruits.",
                "Engage in daily walking (30-45 minutes)."
            ]
            foods_to_avoid = ["Refined flour products", "Sweetened beverages", "White rice"]
        elif 3 <= symptom_count <= 4:
            severity_level = 2
            risk_level = "High"
            precautions = [
                "Strict blood sugar monitoring is advised.",
                "Follow a strict low-carb/Keto-friendly diet.",
                "Avoid all refined flours and sugars.",
                "Schedule a clinical consultation soon."
            ]
            foods_to_avoid = ["All breads and pastas", "High-sugar fruits", "Fried foods"]
        else:
            severity_level = 3
            risk_level = "Very High"
            precautions = [
                "URGENT: Consult an endocrinologist immediately.",
                "Implement a 'Medical Grade' diet plan.",
                "Calorie deficit and high hydration required.",
                "Monitor glucose levels multiple times daily."
            ]
            foods_to_avoid = [
                "All processed sugars and carbs",
                "Full-fat dairy and trans fats",
                "Sodas and sweetened drinks"
            ]

    return jsonify({
        "prediction": prediction,
        "probability": probability,
        "risk_level": risk_level,
        "severity_level": severity_level,
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
    app.run(debug=True, port=5002)
