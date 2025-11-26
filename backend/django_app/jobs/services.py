"""Services for processing job applications with ML services."""
import requests
import logging
from django.conf import settings
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn not available, will use manual cosine similarity calculation")


def calculate_match_score(job, resume):
    """Calculate match score between job and resume using embeddings."""
    try:
        # Check if both have embeddings (handle numpy arrays properly)
        if job.embedding is None or resume.embedding is None:
            logger.warning(f"Missing embeddings: job={job.id} has embedding={job.embedding is not None}, resume={resume.id} has embedding={resume.embedding is not None}")
            return None
        
        # Convert embeddings to numpy arrays
        job_embedding = np.array(job.embedding)
        resume_embedding = np.array(resume.embedding)
        
        # Check if arrays are empty
        if job_embedding.size == 0 or resume_embedding.size == 0:
            logger.warning(f"Empty embeddings: job={job.id}, resume={resume.id}")
            return None
        
        # Calculate cosine similarity
        if HAS_SKLEARN:
            similarity = cosine_similarity(
                job_embedding.reshape(1, -1),
                resume_embedding.reshape(1, -1)
            )[0][0]
        else:
            # Manual cosine similarity calculation
            dot_product = np.dot(job_embedding, resume_embedding)
            norm_job = np.linalg.norm(job_embedding)
            norm_resume = np.linalg.norm(resume_embedding)
            similarity = dot_product / (norm_job * norm_resume) if (norm_job * norm_resume) > 0 else 0.0
        
        # Convert to score (0-100 scale)
        score = float(similarity * 100)
        logger.info(f"Calculated match score: {score:.2f} for job={job.id}, resume={resume.id}")
        return score
        
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        return None


def get_fairness_metrics(application):
    """Get fairness metrics for an application."""
    try:
        # Get all applications for this job to calculate fairness
        from .models import Application
        job_applications = Application.objects.filter(job=application.job)
        
        if job_applications.count() < 2:
            logger.info("Not enough applications for fairness analysis")
            return {}
        
        # Prepare data for fairness service
        applications_data = []
        for app in job_applications:
            applications_data.append({
                'application_id': app.id,
                'score': float(app.score) if app.score else 0.0,
                'protected_attributes': {
                    # Add protected attributes if available
                    # For now, we'll use a placeholder
                    'gender': 'unknown',  # Would need to extract from resume
                    'age': None  # Would need to calculate from resume
                }
            })
        
        # Call fairness service
        response = requests.post(
            f"{settings.FAIRNESS_SERVICE_URL}/api/audit",
            json={
                'application_id': application.id,
                'job_id': application.job.id,
                'score': float(application.score) if application.score else 0.0
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # The service returns {'success': True, 'metrics': {...}}
            metrics = data.get('metrics', {})
            # If there's a message (insufficient data), include it
            if 'message' in data:
                metrics['message'] = data.get('message')
            return metrics
        else:
            logger.warning(f"Fairness service returned {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting fairness metrics: {str(e)}")
        return {}


def get_explanation(application):
    """Get explanation for application score using explainability service."""
    try:
        # Prepare text for explanation
        job_text = f"{application.job.title} {application.job.description} {application.job.requirements}"
        resume_text = application.resume.raw_text or ' '.join(application.resume.skills)
        
        # Call explainability service
        response = requests.post(
            f"{settings.EXPLAINABILITY_SERVICE_URL}/explain",
            json={
                'text': f"Job: {job_text}\nResume: {resume_text}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Return the full response which includes 'explanation' list and 'prediction'
            return data
        else:
            logger.warning(f"Explainability service returned {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting explanation: {str(e)}")
        return {}


def process_application(application):
    """Process application with all ML services: matching, fairness, explainability."""
    try:
        # 1. Calculate match score
        score = calculate_match_score(application.job, application.resume)
        if score is not None:
            application.score = score
            application.save(update_fields=['score'])
            logger.info(f"Updated application {application.id} with score {score}")
        else:
            logger.warning(f"Could not calculate score for application {application.id}")
        
        # 2. Get fairness metrics (async or background task in production)
        try:
            fairness_metrics = get_fairness_metrics(application)
            if fairness_metrics:
                application.fairness_metrics = fairness_metrics
                application.save(update_fields=['fairness_metrics'])
                logger.info(f"Updated application {application.id} with fairness metrics")
        except Exception as e:
            logger.warning(f"Fairness analysis failed for application {application.id}: {str(e)}")
        
        # 3. Get explanation (async or background task in production)
        try:
            explanation = get_explanation(application)
            if explanation:
                application.explanation = explanation
                application.save(update_fields=['explanation'])
                logger.info(f"Updated application {application.id} with explanation")
        except Exception as e:
            logger.warning(f"Explanation generation failed for application {application.id}: {str(e)}")
        
        return application
        
    except Exception as e:
        logger.error(f"Error processing application {application.id}: {str(e)}")
        return application

