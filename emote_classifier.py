"""
ML-based Emote Classifier
Uses machine learning to accurately detect emotes from face and hand positions
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import json


class EmoteClassifier:
    """Machine Learning-based emote classifier"""

    def __init__(self, model_path="emote_model.pkl"):
        """
        Initialize the classifier

        Args:
            model_path: Path to saved model file
        """
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.label_encoder = {}  # Maps label names to integers
        self.label_decoder = {}  # Maps integers back to label names

        # Try to load existing model
        if os.path.exists(model_path):
            self.load_model(model_path)
            print(f"✓ Loaded trained model from {model_path}")
        else:
            print(f"No trained model found at {model_path}")
            print("Please run train_emote_classifier.py to train a model first")

    def train(self, training_data_path="emote_training_data.json", test_size=0.2, random_state=42):
        """
        Train the classifier on collected data

        Args:
            training_data_path: Path to JSON file with training data
            test_size: Fraction of data to use for testing
            random_state: Random seed for reproducibility

        Returns:
            dict: Training results including accuracy and metrics
        """
        # Load training data
        print(f"Loading training data from {training_data_path}...")
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)

        if len(training_data) == 0:
            raise ValueError("No training data found!")

        print(f"Loaded {len(training_data)} samples")

        # Extract features and labels
        X = []
        y = []
        labels_set = set()

        for sample in training_data:
            X.append(sample['features'])
            y.append(sample['label'])
            labels_set.add(sample['label'])

        X = np.array(X)
        y = np.array(y)

        # Create label encoding
        unique_labels = sorted(list(labels_set))
        self.label_encoder = {label: i for i, label in enumerate(unique_labels)}
        self.label_decoder = {i: label for label, i in self.label_encoder.items()}

        print(f"\nEmote classes found: {unique_labels}")
        print(f"Samples per class:")
        for label in unique_labels:
            count = np.sum(y == label)
            print(f"  {label}: {count}")

        # Encode labels as integers
        y_encoded = np.array([self.label_encoder[label] for label in y])

        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=random_state, stratify=y_encoded
        )

        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")

        # Normalize features
        print("\nNormalizing features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train Random Forest classifier
        print("\nTraining Random Forest classifier...")
        self.model = RandomForestClassifier(
            n_estimators=200,        # Increased from 100
            max_depth=25,            # Increased from 20
            min_samples_split=3,     # More aggressive splitting
            min_samples_leaf=1,      # Allow single-sample leaves
            max_features='sqrt',     # Use sqrt of features for each split
            random_state=random_state,
            n_jobs=-1,               # Use all CPU cores
            bootstrap=True,          # Enable bootstrap sampling
            class_weight='balanced'  # Handle class imbalance
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate on test set
        print("\nEvaluating model...")
        y_pred = self.model.predict(X_test_scaled)
        accuracy = np.mean(y_pred == y_test)

        print(f"\n{'='*60}")
        print(f"Test Accuracy: {accuracy:.2%}")
        print(f"{'='*60}\n")

        # Detailed classification report
        print("Classification Report:")
        print(classification_report(
            y_test, y_pred,
            target_names=[self.label_decoder[i] for i in sorted(self.label_decoder.keys())]
        ))

        # Confusion matrix
        print("\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)

        # Feature importance
        feature_importance = self.model.feature_importances_
        print(f"\nTop 10 most important features:")
        top_indices = np.argsort(feature_importance)[-10:][::-1]
        for idx in top_indices:
            print(f"  Feature {idx}: {feature_importance[idx]:.4f}")

        # Save model
        self.save_model()

        return {
            'accuracy': accuracy,
            'classification_report': classification_report(
                y_test, y_pred,
                target_names=[self.label_decoder[i] for i in sorted(self.label_decoder.keys())],
                output_dict=True
            ),
            'confusion_matrix': cm.tolist()
        }

    def predict(self, features):
        """
        Predict emote from features

        Args:
            features: numpy array of features (same format as training)

        Returns:
            dict: {
                'emote': str (predicted emote name),
                'confidence': float (0-1),
                'probabilities': dict mapping emote names to probabilities
            }
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained! Run train() first or load a trained model.")

        # Ensure features is 2D array
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        # Normalize features
        features_scaled = self.scaler.transform(features)

        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        # Decode prediction
        emote_name = self.label_decoder[prediction]
        confidence = probabilities[prediction]

        # Get probabilities for all classes
        prob_dict = {
            self.label_decoder[i]: float(probabilities[i])
            for i in range(len(probabilities))
        }

        return {
            'emote': emote_name,
            'confidence': float(confidence),
            'probabilities': prob_dict
        }

    def predict_batch(self, features_batch):
        """
        Predict emotes for multiple feature vectors

        Args:
            features_batch: numpy array of shape (n_samples, n_features)

        Returns:
            list of prediction dicts
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained! Run train() first or load a trained model.")

        # Normalize features
        features_scaled = self.scaler.transform(features_batch)

        # Predict
        predictions = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)

        results = []
        for i in range(len(predictions)):
            pred = predictions[i]
            probs = probabilities[i]

            emote_name = self.label_decoder[pred]
            confidence = probs[pred]

            prob_dict = {
                self.label_decoder[j]: float(probs[j])
                for j in range(len(probs))
            }

            results.append({
                'emote': emote_name,
                'confidence': float(confidence),
                'probabilities': prob_dict
            })

        return results

    def save_model(self, path=None):
        """Save trained model to disk"""
        if path is None:
            path = self.model_path

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'label_decoder': self.label_decoder
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\n✓ Model saved to {path}")

    def load_model(self, path=None):
        """Load trained model from disk"""
        if path is None:
            path = self.model_path

        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.label_decoder = model_data['label_decoder']

        print(f"Loaded model with {len(self.label_encoder)} classes:")
        for label in sorted(self.label_encoder.keys()):
            print(f"  - {label}")

    def is_trained(self):
        """Check if model is trained and ready"""
        return self.model is not None and self.scaler is not None
