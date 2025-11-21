"""
Flask Fairness Service for bias detection and mitigation.
Uses AIF360 and Fairlearn for fairness metrics and mitigation.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import numpy as np
import pandas as pd
from aif360.metrics import BinaryLabelDatasetMetric
from aif360.algorithms.preprocessing import Reweighing
from fairlearn.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    selection_rate
)
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'equihire'),
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin123')
    )


def calculate_disparate_impact(scores, protected_attributes):
    """
    Calculate disparate impact ratio.
    Returns ratio between 0.8-1.25 for fair outcomes.
    """
    if len(scores) == 0 or len(protected_attributes) == 0:
        return None
    
    # Group by protected attribute
    groups = {}
    for score, attr in zip(scores, protected_attributes):
        if attr not in groups:
            groups[attr] = []
        groups[attr].append(score)
    
    if len(groups) < 2:
        return None
    
    # Calculate selection rates (assuming threshold of 0.5)
    selection_rates = {}
    for attr, group_scores in groups.items():
        selection_rate = sum(1 for s in group_scores if s >= 0.5) / len(group_scores)
        selection_rates[attr] = selection_rate
    
    # Calculate disparate impact ratio
    rates = list(selection_rates.values())
    min_rate = min(rates)
    max_rate = max(rates)
    
    if max_rate == 0:
        return None
    
    disparate_impact = min_rate / max_rate
    return disparate_impact


def calculate_demographic_parity(scores, protected_attributes):
    """Calculate demographic parity difference."""
    if len(scores) == 0 or len(protected_attributes) == 0:
        return None
    
    # Convert to binary predictions (threshold 0.5)
    predictions = [1 if s >= 0.5 else 0 for s in scores]
    
    # Create DataFrame
    df = pd.DataFrame({
        'prediction': predictions,
        'protected': protected_attributes
    })
    
    # Calculate selection rates by group
    selection_rates = df.groupby('protected')['prediction'].mean()
    
    if len(selection_rates) < 2:
        return None
    
    # Calculate difference
    max_rate = selection_rates.max()
    min_rate = selection_rates.min()
    
    return max_rate - min_rate


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'fairness_service'
    })


@app.route('/api/audit', methods=['POST'])
def audit_fairness():
    """Audit application for fairness metrics."""
    try:
        data = request.json
        application_id = data.get('application_id')
        job_id = data.get('job_id')
        score = data.get('score')
        
        if score is None:
            return jsonify({'error': 'Score is required'}), 400
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get all applications for this job
            query = """
                SELECT a.id, a.score, a.status,
                       r.skills, r.education, r.experience_years,
                       u.email, u.role
                FROM applications a
                JOIN resumes r ON a.resume_id = r.id
                JOIN users u ON r.candidate_id = u.id
                WHERE a.job_id = %s
                  AND a.score IS NOT NULL
            """
            cursor.execute(query, (job_id,))
            applications = cursor.fetchall()
            
            if len(applications) < 2:
                return jsonify({
                    'success': True,
                    'metrics': {
                        'message': 'Insufficient data for fairness audit',
                        'total_applications': len(applications)
                    }
                }), 200
            
            # Extract scores and attributes
            scores = [float(app['score']) for app in applications]
            
            # For demo purposes, use experience_years as protected attribute
            # In production, this would be gender, race, etc. (if available)
            protected_attributes = []
            for app in applications:
                exp_years = app['experience_years'] or 0
                # Group into categories
                if exp_years < 2:
                    protected_attributes.append('junior')
                elif exp_years < 5:
                    protected_attributes.append('mid')
                else:
                    protected_attributes.append('senior')
            
            # Calculate fairness metrics
            disparate_impact = calculate_disparate_impact(scores, protected_attributes)
            demographic_parity_diff = calculate_demographic_parity(scores, protected_attributes)
            
            # Determine if fair
            is_fair = True
            if disparate_impact is not None:
                if disparate_impact < 0.8 or disparate_impact > 1.25:
                    is_fair = False
            
            if demographic_parity_diff is not None:
                if abs(demographic_parity_diff) > 0.1:
                    is_fair = False
            
            metrics = {
                'disparate_impact_ratio': disparate_impact,
                'demographic_parity_difference': demographic_parity_diff,
                'is_fair': is_fair,
                'total_applications': len(applications),
                'protected_attribute': 'experience_level',
                'threshold': 0.8
            }
            
            logger.info(f"Fairness audit completed for job_id: {job_id}")
            
            return jsonify({
                'success': True,
                'metrics': metrics
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Error auditing fairness: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mitigate', methods=['POST'])
def mitigate_bias():
    """Apply bias mitigation using reweighting."""
    try:
        data = request.json
        job_id = data.get('job_id')
        
        if not job_id:
            return jsonify({'error': 'Job ID is required'}), 400
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get all applications for this job
            query = """
                SELECT a.id, a.score, a.status,
                       r.skills, r.education, r.experience_years,
                       u.email
                FROM applications a
                JOIN resumes r ON a.resume_id = r.id
                JOIN users u ON r.candidate_id = u.id
                WHERE a.job_id = %s
                  AND a.score IS NOT NULL
            """
            cursor.execute(query, (job_id,))
            applications = cursor.fetchall()
            
            if len(applications) < 2:
                return jsonify({
                    'error': 'Insufficient data for bias mitigation'
                }), 400
            
            # Extract data
            scores = [float(app['score']) for app in applications]
            protected_attributes = []
            for app in applications:
                exp_years = app['experience_years'] or 0
                if exp_years < 2:
                    protected_attributes.append('junior')
                elif exp_years < 5:
                    protected_attributes.append('mid')
                else:
                    protected_attributes.append('senior')
            
            # Create DataFrame for reweighting
            df = pd.DataFrame({
                'score': scores,
                'protected': protected_attributes,
                'application_id': [app['id'] for app in applications]
            })
            
            # Calculate weights for reweighting
            # Simple approach: equalize selection rates
            selection_rates = df.groupby('protected')['score'].apply(
                lambda x: (x >= 0.5).mean()
            )
            overall_rate = (df['score'] >= 0.5).mean()
            
            weights = {}
            for attr in selection_rates.index:
                if selection_rates[attr] > 0:
                    weights[attr] = overall_rate / selection_rates[attr]
                else:
                    weights[attr] = 1.0
            
            # Apply weights to scores
            adjusted_scores = []
            for idx, row in df.iterrows():
                weight = weights.get(row['protected'], 1.0)
                # Apply weight (cap at reasonable values)
                adjusted_score = min(1.0, row['score'] * weight)
                adjusted_scores.append({
                    'application_id': row['application_id'],
                    'original_score': row['score'],
                    'adjusted_score': adjusted_score,
                    'weight': weight
                })
            
            logger.info(f"Bias mitigation completed for job_id: {job_id}")
            
            return jsonify({
                'success': True,
                'adjusted_scores': adjusted_scores,
                'weights': weights
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Error mitigating bias: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)

