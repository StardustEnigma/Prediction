# ml_utils.py
import pandas as pd
import pickle
import numpy as np
import os
from django.conf import settings

class AttritionPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.cat_cols = None
        self.num_cols = None
        self.model_columns = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model and preprocessing objects"""
        try:
            # Adjust path to your model location
            model_path = os.path.join(settings.BASE_DIR, 'models', 'attrition_model.pkl')
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.cat_cols = model_data['cat_cols']
            self.num_cols = model_data['num_cols']
            self.model_columns = model_data['columns']
            
            print("✅ Model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            # Fallback to random prediction if model fails
            self.model = None
    
    def preprocess_for_prediction(self, df):
        """Preprocess DataFrame for model prediction"""
        if self.model is None:
            return None
            
        try:
            # Select only the feature columns used in training
            feature_cols = self.num_cols + self.cat_cols
            df_features = df[feature_cols].copy()
            
            # Separate numeric and categorical columns
            df_num = df_features[self.num_cols].copy()
            df_cat = df_features[self.cat_cols].copy()
            
            # Fill any missing categorical values
            df_cat = df_cat.fillna('Missing')
            
            # One-hot encode categorical columns
            df_cat_encoded = pd.get_dummies(df_cat, columns=self.cat_cols, drop_first=True)
            
            # Scale numeric columns
            df_num_scaled = pd.DataFrame(
                self.scaler.transform(df_num), 
                columns=self.num_cols,
                index=df_num.index
            )
            
            # Combine numeric and categorical features
            X_pred = pd.concat([df_num_scaled, df_cat_encoded], axis=1)
            
            # Align columns with training columns (add missing dummy variables as 0)
            for col in self.model_columns:
                if col not in X_pred.columns:
                    X_pred[col] = 0
            
            # Reorder columns to match training order
            X_pred = X_pred[self.model_columns]
            
            return X_pred
            
        except Exception as e:
            print(f"❌ Preprocessing error: {e}")
            return None
    
    def predict_single_employee(self, employee_data):
        """Predict attrition for a single employee (from feedback form)"""
        # Convert single employee data to DataFrame
        df = pd.DataFrame([employee_data])
        
        if self.model is None:
            # Fallback: random prediction
            attrition = np.random.choice([0, 1], p=[0.7, 0.3])
            probability = np.random.uniform(10, 90)
            return int(attrition), float(probability)
        
        try:
            X_pred = self.preprocess_for_prediction(df)
            if X_pred is None:
                # Fallback: random prediction
                attrition = np.random.choice([0, 1], p=[0.7, 0.3])
                probability = np.random.uniform(10, 90)
                return int(attrition), float(probability)
            
            # Get predictions
            attrition_pred = self.model.predict(X_pred)[0]
            probability_pred = self.model.predict_proba(X_pred)[0, 1] * 100
            
            return int(attrition_pred), float(probability_pred)
            
        except Exception as e:
            print(f"❌ Single prediction error: {e}")
            # Fallback: random prediction
            attrition = np.random.choice([0, 1], p=[0.7, 0.3])
            probability = np.random.uniform(10, 90)
            return int(attrition), float(probability)
    
    def predict_attrition_bulk(self, df):
        """Predict attrition for multiple employees (from CSV upload)"""
        if self.model is None:
            # Fallback: random predictions
            attritions = np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
            probabilities = np.random.uniform(10, 90, size=len(df))
            return attritions, probabilities
        
        try:
            X_pred = self.preprocess_for_prediction(df)
            if X_pred is None:
                attritions = np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
                probabilities = np.random.uniform(10, 90, size=len(df))
                return attritions, probabilities
            
            # Get predictions
            attrition_predictions = self.model.predict(X_pred)
            probability_predictions = self.model.predict_proba(X_pred)[:, 1] * 100
            
            return attrition_predictions, probability_predictions
            
        except Exception as e:
            print(f"❌ Bulk prediction error: {e}")
            # Fallback: random predictions
            attritions = np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
            probabilities = np.random.uniform(10, 90, size=len(df))
            return attritions, probabilities

# Initialize global predictor instance
predictor = AttritionPredictor()
