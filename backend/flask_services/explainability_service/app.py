"""
Lightweight Explainability Service using LIME for text explanations.
Provides interpretable explanations for text classification tasks.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from lime.lime_text import LimeTextExplainer
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize text processing components
try:
    # Simple text cleaning function
    def clean_text(text):
        if not isinstance(text, str):
            return ""
        # Remove special chars and extra whitespace
        text = re.sub(r'[^\w\s]', '', text.lower())
        return ' '.join(text.split())

    # Initialize TF-IDF vectorizer (lighter than sentence transformers)
    vectorizer = TfidfVectorizer(
        max_features=5000,  # Limit features for memory efficiency
        stop_words='english',
        ngram_range=(1, 2)  # Consider unigrams and bigrams
    )
    
    # Initialize LIME explainer
    explainer = LimeTextExplainer(
        class_names=['Irrelevant', 'Relevant'],
        kernel_width=25,  # Controls the locality of explanations
        verbose=False
    )
    
    logger.info("Successfully initialized explainability service")
    
except Exception as e:
    logger.error(f"Error initializing service: {str(e)}")
    raise SystemExit(1)

# Add the explanation endpoints
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'explainability',
        'version': '1.0.0'
    }), 200

def predict_proba(texts, vectorizer):
    """Predict probability for LIME explainer."""
    if not isinstance(texts, list):
        texts = [texts]
    
    # This is a dummy predictor - in a real application, you would use your trained model here
    # For demonstration, we'll return random probabilities
    return np.random.rand(len(texts), 2)

@app.route('/explain', methods=['POST'])
def explain_text():
    """Explain text classification using LIME."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Ensure text is not empty after cleaning
        if not cleaned_text or len(cleaned_text.strip()) < 10:
            logger.warning(f"Text too short after cleaning: {len(cleaned_text)} chars")
            return jsonify({
                'explanation': [['text', 0.0]],
                'prediction': 0.5,
                'message': 'Text too short for meaningful explanation'
            }), 200
        
        # Generate explanation
        def predict_fn(texts):
            try:
                return predict_proba(texts, vectorizer)
            except Exception as e:
                logger.error(f"Error in predict_fn: {str(e)}")
                # Return default probabilities
                return np.array([[0.5, 0.5]] * len(texts))
        
        # Get explanation with error handling
        try:
            exp = explainer.explain_instance(
                cleaned_text,
                predict_fn,
                num_features=10,  # Number of features to show
                top_labels=1
            )
            
            explanation_list = exp.as_list()
        except Exception as e:
            logger.error(f"Error in LIME explain_instance: {str(e)}")
            # Return a simple explanation based on text length and keywords
            explanation_list = [
                ['text_length', 0.1 if len(cleaned_text) > 500 else -0.1],
                ['keywords', 0.05]
            ]
        
        # Format explanation
        explanation = {
            'explanation': explanation_list,
            'prediction': float(predict_proba([cleaned_text], vectorizer)[0][1])
        }
        
        return jsonify(explanation), 200
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)

