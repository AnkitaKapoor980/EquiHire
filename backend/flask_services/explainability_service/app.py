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
        
        # Generate explanation
        def predict_fn(texts):
            return predict_proba(texts, vectorizer)
        
        # Get explanation
        exp = explainer.explain_instance(
            cleaned_text,
            predict_fn,
            num_features=10,  # Number of features to show
            top_labels=1
        )
        
        # Format explanation
        explanation = {
            'explanation': exp.as_list(),
            'prediction': float(predict_proba([cleaned_text], vectorizer)[0][1])
        }
        
        return jsonify(explanation), 200
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
        embeddings = model.encode([job_text, resume_text], convert_to_numpy=True, show_progress_bar=False)
        job_embedding = embeddings[0]
        resume_embedding = embeddings[1]
        
        # Calculate similarity score
        similarity_score = calculate_cosine_similarity(tuple(job_embedding.tolist()), tuple(resume_embedding.tolist()))
        
        # Generate explanation (simplified for performance)
        explanation = {
            'score': float(similarity_score),
            'interpretation': 'The score represents the cosine similarity between the job and resume embeddings. ' \
                            'Higher values indicate better matches based on semantic similarity.'
        }
        
        response_time = time.time() - start_time
        logger.info(f"Explanation generated in {response_time:.2f} seconds")
        
        return jsonify({
            'similarity': float(similarity_score),
            'explanation': explanation,
            'model': MODEL_NAME,
            'processing_time_seconds': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in explain_application: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to generate explanation',
            'details': str(e)
        }), 500


@app.route('/api/batch_explain', methods=['POST'])
def batch_explain():
    """Generate explanations for multiple applications in batch."""
    start_time = time.time()
    
    try:
        data = request.get_json()
        applications = data.get('applications', [])
        
        if not applications:
            return jsonify({'error': 'No applications provided'}), 400
            
        logger.info(f"Processing batch of {len(applications)} applications")
        
        # Prepare texts for batch processing
        texts = []
        text_pairs = []
        
        for app in applications:
            job_text = app.get('job_text', '')
            resume_text = app.get('resume_text', '')
            texts.extend([job_text, resume_text])
            text_pairs.append((job_text, resume_text))
        
        # Batch encode all texts at once
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        
        # Process results
        results = []
        for i, (job_text, resume_text) in enumerate(text_pairs):
            try:
                job_emb = embeddings[i*2]
                resume_emb = embeddings[i*2 + 1]
                
                # Calculate similarity
                similarity = calculate_cosine_similarity(
                    tuple(job_emb.tolist()),
                    tuple(resume_emb.tolist())
                )
                
                results.append({
                    'similarity': float(similarity),
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Error processing application {i}: {str(e)}")
                results.append({
                    'error': str(e),
                    'status': 'error'
                })
        
        total_time = time.time() - start_time
        logger.info(f"Batch processing completed in {total_time:.2f} seconds")
        return jsonify({
            'results': results,
            'batch_size': len(applications),
            'processing_time_seconds': total_time,
            'average_time_per_item': total_time / len(applications) if applications else 0
        })
        
    except Exception as e:
        logger.error(f"Error in batch_explain: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process batch',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)

