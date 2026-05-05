import os
import numpy as np
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from django.conf import settings

load_dotenv()

class ClinicalAIService:
    _instance = None
    model = None
    scaler = None
    groq_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClinicalAIService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.model, self.scaler = self._train_model_on_fly()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if GROQ_API_KEY:
            self.groq_client = Groq(api_key=GROQ_API_KEY)

    def _train_model_on_fly(self):
        try:
            csv_path = os.path.join(settings.BASE_DIR, 'dataset', 'diabetes_early_stage_cleaned.csv')
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
            print("Model trained successfully in Django service!")
            return rf_model, scaler_obj
        except Exception as e:
            print(f"Error training model in Django: {e}")
            return None, None

    def predict(self, data):
        if self.model is None or self.scaler is None:
            return {"error": "Model not initialized"}, 500

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
            return {"error": f"Invalid data: {str(e)}"}, 400

        features_scaled = self.scaler.transform(features)
        probability = float(self.model.predict_proba(features_scaled)[0][1])
        
        symptom_keys = ['Polyuria', 'Polydipsia', 'sudden weight loss', 'Irritability', 'visual blurring', 'Polyphagia']
        symptom_count = sum(1 for key in symptom_keys if float(data.get(key, 0)) == 1)
        
        prediction = 1 if probability >= 0.5 else 0
        
        if prediction == 0:
            severity_level = 0
            risk_level = "Low"
            precautions = ["Maintain healthy lifestyle", "Continue physical activity", "Annual check-up"]
            foods_to_avoid = ["Excessive refined sugars", "Highly processed snacks"]
        else:
            if symptom_count <= 2:
                severity_level = 1
                risk_level = "Moderate"
                precautions = ["Monitor glucose monthly", "Increase fiber", "Daily walking"]
                foods_to_avoid = ["Refined flour", "Sweetened beverages", "White rice"]
            elif 3 <= symptom_count <= 4:
                severity_level = 2
                risk_level = "High"
                precautions = ["Strict glucose monitoring", "Low-carb/Keto diet", "Avoid refined flour", "Consult doctor"]
                foods_to_avoid = ["All breads/pastas", "High-sugar fruits", "Fried foods"]
            else:
                severity_level = 3
                risk_level = "Very High"
                precautions = ["URGENT: Consult endocrinologist", "Medical grade diet", "High hydration", "Frequent monitoring"]
                foods_to_avoid = ["All processed sugars/carbs", "Full-fat dairy", "Sodas"]

        return {
            "prediction": prediction,
            "probability": probability,
            "risk_level": risk_level,
            "severity_level": severity_level,
            "is_diabetic": bool(prediction == 1),
            "precautions": precautions,
            "foods_to_avoid": foods_to_avoid
        }, 200

    def check_food(self, food_name):
        if not self.groq_client:
            return {"error": "Groq not configured"}, 500
        
        prompt = f"""
        You are an expert nutritionist and diabetes educator. Response for: "{food_name}".
        Format:
        VERDICT: [SAFE, AVOID, or MODERATE]
        REASONING: [1-2 sentences]
        ALTERNATIVES: [3 foods, comma separated]
        """
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            return {"food": food_name, "advice": chat_completion.choices[0].message.content}, 200
        except Exception as e:
            return {"error": str(e)}, 500

ai_service = ClinicalAIService()
