"""
Flask Matcher Service for generating embeddings and matching resumes to jobs.
Uses Sentence-BERT for embeddings and cosine similarity for matching.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
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

# Load ultra-lightweight model with optimizations
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'  # Smaller and faster
try:
    # Optimize model loading with CPU-specific settings
    model = SentenceTransformer(
        MODEL_NAME,
        device='cpu',
        use_auth_token=False,
        cache_folder='/tmp/models'  # Use tmpfs for faster access
    )
    model.max_seq_length = 128  # Reduce sequence length for faster processing
    logger.info(f"Loaded optimized lightweight model: {MODEL_NAME}")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    model = None

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'equihire'),
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin123')
    )


def vector_to_array(vector_str):
    """Convert PostgreSQL vector string to numpy array."""
    if vector_str is None:
        return None
    # Remove brackets and split
    vector_str = vector_str.strip('[]')
    return np.array([float(x) for x in vector_str.split(',')])


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'matcher_service',
        'model_loaded': model is not None
    })


@app.route('/api/embed', methods=['POST'])
def generate_embedding():
    """Generate embedding for given text."""
    try:
        if not model:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        if not text or len(text.strip()) == 0:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        
        # Convert to list for JSON serialization
        embedding_list = embedding.tolist()
        
        logger.info(f"Generated embedding for text (length: {len(text)})")
        
        return jsonify({
            'success': True,
            'embedding': embedding_list,
            'dimensions': len(embedding_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/match', methods=['POST'])
def match_resumes():
    """Match resumes to a job based on embeddings."""
    try:
        if not model:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.json
        if not data or 'job_embedding' not in data:
            return jsonify({'error': 'Job embedding is required'}), 400
        
        job_embedding = np.array(data['job_embedding'])
        job_id = data.get('job_id')
        top_k = data.get('top_k', 10)
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Query resumes with embeddings
            if job_id:
                # Exclude resumes that already have applications for this job
                query = """
                    SELECT r.id, r.candidate_id, r.embedding, r.skills, r.education,
                           r.experience_years, r.file_name, u.email as candidate_email
                    FROM resumes r
                    JOIN users u ON r.candidate_id = u.id
                    WHERE r.embedding IS NOT NULL
                      AND r.is_active = TRUE
                      AND r.id NOT IN (
                          SELECT resume_id FROM applications WHERE job_id = %s
                      )
                """
                cursor.execute(query, (job_id,))
            else:
                query = """
                    SELECT r.id, r.candidate_id, r.embedding, r.skills, r.education,
                           r.experience_years, r.file_name, u.email as candidate_email
                    FROM resumes r
                    JOIN users u ON r.candidate_id = u.id
                    WHERE r.embedding IS NOT NULL
                      AND r.is_active = TRUE
                """
                cursor.execute(query)
            
            resumes = cursor.fetchall()
            
            if not resumes:
                return jsonify({
                    'success': True,
                    'matches': [],
                    'message': 'No resumes with embeddings found'
                }), 200
            
            # Calculate similarities
            matches = []
            for resume in resumes:
                resume_embedding = vector_to_array(resume['embedding'])
                if resume_embedding is None:
                    continue
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    job_embedding.reshape(1, -1),
                    resume_embedding.reshape(1, -1)
                )[0][0]
                
                matches.append({
                    'resume_id': resume['id'],
                    'candidate_id': resume['candidate_id'],
                    'candidate_email': resume['candidate_email'],
                    'score': float(similarity),
                    'skills': resume['skills'] or [],
                    'education': resume['education'] or [],
                    'experience_years': resume['experience_years'],
                    'file_name': resume['file_name']
                })
            
            # Sort by similarity score (descending)
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top K matches
            top_matches = matches[:top_k]
            
            logger.info(f"Matched {len(top_matches)} resumes for job_id: {job_id}")
            
            return jsonify({
                'success': True,
                'matches': top_matches,
                'total_candidates': len(matches)
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Error matching resumes: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch_embed', methods=['POST'])
def batch_embed():
    """Generate embeddings for multiple texts."""
    try:
        if not model:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.json
        if not data or 'texts' not in data:
            return jsonify({'error': 'Texts array is required'}), 400
        
        texts = data['texts']
        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({'error': 'Texts must be a non-empty array'}), 400
        
        # Generate embeddings in batch
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Convert to list of lists
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        logger.info(f"Generated {len(embeddings_list)} embeddings in batch")
        
        return jsonify({
            'success': True,
            'embeddings': embeddings_list,
            'count': len(embeddings_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch embedding: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)

