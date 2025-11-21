"""
Script to batch generate embeddings for resumes and job descriptions.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'equihire'),
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin123')
    )


def generate_embeddings_batch(texts, matcher_service_url):
    """Generate embeddings for a batch of texts."""
    try:
        response = requests.post(
            f"{matcher_service_url}/api/batch_embed",
            json={'texts': texts},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get('embeddings', [])
        else:
            logger.error(f"Error generating embeddings: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception generating embeddings: {str(e)}")
        return None


def update_resume_embeddings(conn, matcher_service_url, batch_size=10):
    """Generate and update embeddings for resumes."""
    logger.info("Generating embeddings for resumes")
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get resumes without embeddings
    cursor.execute("""
        SELECT id, raw_text, skills, education
        FROM resumes
        WHERE embedding IS NULL
          AND (raw_text IS NOT NULL OR skills IS NOT NULL)
        LIMIT 1000
    """)
    
    resumes = cursor.fetchall()
    logger.info(f"Found {len(resumes)} resumes without embeddings")
    
    for i in range(0, len(resumes), batch_size):
        batch = resumes[i:i+batch_size]
        texts = []
        resume_ids = []
        
        for resume in batch:
            # Combine text fields
            text_parts = []
            if resume['raw_text']:
                text_parts.append(resume['raw_text'])
            if resume['skills']:
                text_parts.extend(resume['skills'])
            if resume['education']:
                text_parts.extend(resume['education'])
            
            text = ' '.join(text_parts)
            if text:
                texts.append(text)
                resume_ids.append(resume['id'])
        
        if not texts:
            continue
        
        # Generate embeddings
        embeddings = generate_embeddings_batch(texts, matcher_service_url)
        
        if embeddings:
            # Update database
            for resume_id, embedding in zip(resume_ids, embeddings):
                cursor.execute("""
                    UPDATE resumes
                    SET embedding = %s::vector
                    WHERE id = %s
                """, (str(embedding), resume_id))
            
            conn.commit()
            logger.info(f"Updated {len(embeddings)} resume embeddings")
        
        time.sleep(1)  # Rate limiting
    
    cursor.close()


def update_job_embeddings(conn, matcher_service_url, batch_size=10):
    """Generate and update embeddings for job descriptions."""
    logger.info("Generating embeddings for job descriptions")
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get jobs without embeddings
    cursor.execute("""
        SELECT id, title, description, requirements
        FROM job_descriptions
        WHERE embedding IS NULL
        LIMIT 1000
    """)
    
    jobs = cursor.fetchall()
    logger.info(f"Found {len(jobs)} jobs without embeddings")
    
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i+batch_size]
        texts = []
        job_ids = []
        
        for job in batch:
            text = f"{job['title']} {job['description']} {job['requirements']}"
            if text.strip():
                texts.append(text)
                job_ids.append(job['id'])
        
        if not texts:
            continue
        
        # Generate embeddings
        embeddings = generate_embeddings_batch(texts, matcher_service_url)
        
        if embeddings:
            # Update database
            for job_id, embedding in zip(job_ids, embeddings):
                cursor.execute("""
                    UPDATE job_descriptions
                    SET embedding = %s::vector
                    WHERE id = %s
                """, (str(embedding), job_id))
            
            conn.commit()
            logger.info(f"Updated {len(embeddings)} job embeddings")
        
        time.sleep(1)  # Rate limiting
    
    cursor.close()


def main():
    """Main function."""
    matcher_service_url = os.getenv('MATCHER_SERVICE_URL', 'http://localhost:5002')
    
    conn = get_db_connection()
    
    try:
        # Generate embeddings for resumes
        update_resume_embeddings(conn, matcher_service_url)
        
        # Generate embeddings for jobs
        update_job_embeddings(conn, matcher_service_url)
        
        logger.info("Embedding generation completed")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()

