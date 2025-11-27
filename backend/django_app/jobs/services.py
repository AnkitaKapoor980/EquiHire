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
    """
    Get fairness metrics for an application with fallback to static analysis.
    
    Returns:
        dict: Fairness metrics including bias detection results
    """
    # Fallback metrics in case the service is unavailable
    FALLBACK_METRICS = {
        'bias_detected': False,
        'message': 'Using fallback fairness analysis - service unavailable',
        'metrics': {
            'statistical_parity_difference': 0.0,
            'disparate_impact_ratio': 1.0,
            'average_odds_difference': 0.0,
            'equal_opportunity_difference': 0.0,
            'analysis_quality': 'low',
            'suggested_actions': [
                'Fairness service is currently unavailable',
                'Review applications manually for potential biases',
                'Ensure diverse hiring panels are in place',
                'Use structured interviews and evaluation criteria'
            ]
        },
        'is_fallback': True
    }
    
    try:
        # Check if fairness service is enabled
        if not getattr(settings, 'FAIRNESS_SERVICE_ENABLED', True):
            logger.info("Fairness service is disabled, using fallback metrics")
            return FALLBACK_METRICS
            
        # Get all applications for this job to calculate fairness
        from .models import Application
        job_applications = Application.objects.filter(job=application.job)
        
        if job_applications.count() < 2:
            logger.info("Not enough applications for fairness analysis, using fallback")
            FALLBACK_METRICS['message'] = 'Not enough applications for fairness analysis (minimum 2 required)'
            return FALLBACK_METRICS
        
        # Prepare data for fairness service
        applications_data = []
        for app in job_applications:
            applications_data.append({
                'application_id': app.id,
                'score': float(app.score) if app.score else 0.0,
                'protected_attributes': {
                    'gender': 'unknown',  # Would need to extract from resume
                    'age': None  # Would need to calculate from resume
                }
            })
        
        # Call fairness service with timeout
        try:
            response = requests.post(
                f"{settings.FAIRNESS_SERVICE_URL}/api/audit",
                json={
                    'application_id': application.id,
                    'job_id': application.job.id,
                    'score': float(application.score) if application.score else 0.0,
                    'total_applications': job_applications.count()
                },
                timeout=5  # Shorter timeout for better responsiveness
            )
            
            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                if not isinstance(data, dict):
                    logger.warning("Invalid response format from fairness service")
                    return FALLBACK_METRICS
                    
                # Ensure we have at least some metrics
                if 'metrics' not in data:
                    data['metrics'] = {}
                    
                # Add fallback message if no metrics are available
                if not data['metrics']:
                    data['message'] = 'No fairness metrics available' + (
                        f" - {data.get('message', '').lower()}" if data.get('message') else ''
                    )
                
                return data
                
            else:
                logger.warning(f"Fairness service returned {response.status_code}: {response.text}")
                return FALLBACK_METRICS
                
        except requests.exceptions.Timeout:
            logger.warning("Fairness service request timed out")
            FALLBACK_METRICS['message'] = 'Fairness analysis timed out - using fallback metrics'
            return FALLBACK_METRICS
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling fairness service: {str(e)}")
            FALLBACK_METRICS['message'] = f'Fairness service error: {str(e)} - using fallback metrics'
            return FALLBACK_METRICS
            
    except Exception as e:
        logger.error(f"Error in get_fairness_metrics: {str(e)}", exc_info=True)
        FALLBACK_METRICS['message'] = f'Unexpected error: {str(e)} - using fallback metrics'
        return FALLBACK_METRICS


def get_explanation(application):
    """
    Get explanation for application score with fallback to rule-based explanation.
    
    Returns:
        dict: Contains 'explanation' (list of explanation points) and 'prediction' (score)
    """
    # Fallback explanation in case the service is unavailable
    FALLBACK_EXPLANATION = {
        'explanation': [
            'This is a fallback explanation because the explainability service is currently unavailable.',
            'The match score is based on keyword matching and semantic similarity between the job requirements and resume content.',
            'Key factors considered include: skills match, experience relevance, and education alignment with job requirements.',
            'For a more detailed analysis, please try again later when the explainability service is available.'
        ],
        'prediction': float(application.score) if application.score else 0.0,
        'is_fallback': True,
        'confidence': 0.5,
        'suggestions': [
            'Review the resume for relevant experience and skills',
            'Consider additional qualifications that might not be explicitly listed',
            'Contact the candidate for clarification if needed'
        ]
    }
    
    try:
        # Check if explainability service is enabled
        if not getattr(settings, 'EXPLAINABILITY_SERVICE_ENABLED', True):
            logger.info("Explainability service is disabled, using fallback explanation")
            return FALLBACK_EXPLANATION
            
        # Prepare text for explanation with basic validation
        if not hasattr(application, 'job') or not application.job:
            logger.warning("No job associated with application")
            FALLBACK_EXPLANATION['explanation'].insert(0, 'No job information available for this application.')
            return FALLBACK_EXPLANATION
            
        job_text = f"{application.job.title or ''} {application.job.description or ''} {application.job.requirements or ''}".strip()
        if not job_text:
            logger.warning("Empty job text for explanation")
            FALLBACK_EXPLANATION['explanation'].insert(0, 'No job description available for analysis.')
            return FALLBACK_EXPLANATION
            
        if not hasattr(application, 'resume') or not application.resume:
            logger.warning("No resume associated with application")
            FALLBACK_EXPLANATION['explanation'].insert(0, 'No resume information available for this application.')
            return FALLBACK_EXPLANATION
            
        resume_text = application.resume.raw_text or ' '.join(getattr(application.resume, 'skills', []))
        if not resume_text.strip():
            logger.warning("Empty resume text for explanation")
            FALLBACK_EXPLANATION['explanation'].insert(0, 'No resume content available for analysis.')
            return FALLBACK_EXPLANATION
        
        # Call explainability service with timeout
        try:
            response = requests.post(
                f"{settings.EXPLAINABILITY_SERVICE_URL}/explain",
                json={
                    'text': f"Job: {job_text}\nResume: {resume_text}",
                    'job_id': application.job.id if hasattr(application.job, 'id') else None,
                    'resume_id': application.resume.id if hasattr(application.resume, 'id') else None,
                    'score': float(application.score) if application.score else 0.0
                },
                timeout=5  # Shorter timeout for better responsiveness
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.warning("Invalid response format from explainability service")
                    return FALLBACK_EXPLANATION
                    
                # Ensure we have required fields
                if 'explanation' not in data:
                    data['explanation'] = FALLBACK_EXPLANATION['explanation']
                    
                if 'prediction' not in data:
                    data['prediction'] = float(application.score) if application.score else 0.0
                    
                # Ensure explanation is a list
                if not isinstance(data['explanation'], list):
                    if isinstance(data['explanation'], str):
                        data['explanation'] = [data['explanation']]
                    else:
                        data['explanation'] = FALLBACK_EXPLANATION['explanation']
                
                # Add fallback flag if not present
                if 'is_fallback' not in data:
                    data['is_fallback'] = False
                    
                return data
                
            else:
                logger.warning(f"Explainability service returned {response.status_code}: {response.text}")
                return FALLBACK_EXPLANATION
                
        except requests.exceptions.Timeout:
            logger.warning("Explainability service request timed out")
            FALLBACK_EXPLANATION['explanation'].insert(0, 'Explanation service timed out - showing fallback explanation.')
            return FALLBACK_EXPLANATION
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling explainability service: {str(e)}")
            FALLBACK_EXPLANATION['explanation'].insert(0, f'Explanation service error - {str(e)}')
            return FALLBACK_EXPLANATION
            
    except Exception as e:
        logger.error(f"Error in get_explanation: {str(e)}", exc_info=True)
        FALLBACK_EXPLANATION['explanation'].insert(0, f'Unexpected error: {str(e)}')
        return FALLBACK_EXPLANATION


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

