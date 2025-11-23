"""
Flask Explainability Service for SHAP explanations.
Provides feature importance and explanations for matching scores.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import numpy as np
import shap
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load lightweight Sentence-BERT model for explanations (paraphrase-MiniLM-L3-v2 is ~3x smaller than all-MiniLM-L6-v2)
MODEL_NAME = 'sentence-transformers/paraphrase-MiniLM-L3-v2'
try:
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Loaded lightweight Sentence-BERT model: {MODEL_NAME}")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    model = None


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'equihire'),
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin123')
    )


def calculate_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def explain_score_simple(job_text, resume_text, job_embedding, resume_embedding):
    """
    Simple explanation using feature importance.
    In production, this would use SHAP for more detailed explanations.
    """
    if not model:
        return {
            'explanation': 'Model not available',
            'feature_importance': {}
        }
    
    # Split texts into features (words/phrases)
    job_words = set(job_text.lower().split())
    resume_words = set(resume_text.lower().split())
    
    # Common words
    common_words = job_words.intersection(resume_words)
    
    # Important keywords
    important_keywords = [
        'python', 'java', 'javascript', 'react', 'sql', 'docker',
        'kubernetes', 'aws', 'machine learning', 'experience',
        'education', 'certification', 'project', 'skill'
    ]
    
    feature_importance = {}
    for keyword in important_keywords:
        if keyword in job_text.lower() and keyword in resume_text.lower():
            feature_importance[keyword] = 0.1  # Base importance
        elif keyword in job_text.lower():
            feature_importance[keyword] = -0.05  # Missing from resume
    
    # Calculate overall similarity
    similarity = calculate_cosine_similarity(job_embedding, resume_embedding)
    
    return {
        'similarity_score': float(similarity),
        'common_words_count': len(common_words),
        'feature_importance': feature_importance,
        'explanation': f"Match score of {similarity:.3f} based on {len(common_words)} common terms"
    }


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'explainability_service',
        'model_loaded': model is not None
    })


@app.route('/api/explain', methods=['POST'])
def explain_application():
    """Generate SHAP explanation for an application."""
    try:
        data = request.json
        application_id = data.get('application_id')
        job_id = data.get('job_id')
        resume_id = data.get('resume_id')
        score = data.get('score')
        
        if not all([job_id, resume_id]):
            return jsonify({'error': 'Job ID and Resume ID are required'}), 400
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get job details
            job_query = """
                SELECT id, title, description, requirements, embedding
                FROM job_descriptions
                WHERE id = %s
            """
            cursor.execute(job_query, (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Get resume details
            resume_query = """
                SELECT id, raw_text, skills, education, experience_years, embedding
                FROM resumes
                WHERE id = %s
            """
            cursor.execute(resume_query, (resume_id,))
            resume = cursor.fetchone()
            
            if not resume:
                return jsonify({'error': 'Resume not found'}), 404
            
            # Prepare texts
            job_text = f"{job['title']} {job['description']} {job['requirements']}"
            resume_text = resume['raw_text'] or f"{' '.join(resume['skills'] or [])} {' '.join(resume['education'] or [])}"
            
            # Get embeddings
            job_embedding = None
            resume_embedding = None
            
            if job['embedding']:
                job_embedding = np.array(json.loads(job['embedding']) if isinstance(job['embedding'], str) else job['embedding'])
            
            if resume['embedding']:
                resume_embedding = np.array(json.loads(resume['embedding']) if isinstance(resume['embedding'], str) else resume['embedding'])
            
            # If embeddings not available, generate them
            if job_embedding is None and model:
                job_embedding = model.encode(job_text, convert_to_numpy=True, normalize_embeddings=True)
            
            if resume_embedding is None and model:
                resume_embedding = model.encode(resume_text, convert_to_numpy=True, normalize_embeddings=True)
            
            # Generate explanation
            if job_embedding is not None and resume_embedding is not None:
                explanation = explain_score_simple(job_text, resume_text, job_embedding, resume_embedding)
            else:
                explanation = {
                    'explanation': 'Unable to generate explanation - embeddings not available',
                    'feature_importance': {}
                }
            
            # Add additional context
            explanation['job_id'] = job_id
            explanation['resume_id'] = resume_id
            explanation['application_id'] = application_id
            explanation['resume_skills'] = resume['skills'] or []
            explanation['resume_education'] = resume['education'] or []
            explanation['resume_experience_years'] = resume['experience_years']
            
            logger.info(f"Generated explanation for application_id: {application_id}")
            
            return jsonify({
                'success': True,
                'explanation': explanation
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch_explain', methods=['POST'])
def batch_explain():
    """Generate explanations for multiple applications."""
    try:
        data = request.json
        application_ids = data.get('application_ids', [])
        
        if not application_ids:
            return jsonify({'error': 'Application IDs are required'}), 400
        
        explanations = []
        for app_id in application_ids:
            # This is a simplified version - in production, batch process
            try:
                # Get application details
                conn = get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                query = """
                    SELECT a.id, a.job_id, a.resume_id, a.score
                    FROM applications a
                    WHERE a.id = %s
                """
                cursor.execute(query, (app_id,))
                app = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if app:
                    # Generate explanation (simplified)
                    explanation = {
                        'application_id': app_id,
                        'score': float(app['score']) if app['score'] else None,
                        'explanation': f"Application {app_id} explanation"
                    }
                    explanations.append(explanation)
            except Exception as e:
                logger.error(f"Error explaining application {app_id}: {str(e)}")
                explanations.append({
                    'application_id': app_id,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'explanations': explanations
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch explain: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)

