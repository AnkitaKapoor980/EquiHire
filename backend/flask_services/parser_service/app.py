"""
Flask Parser Service for resume parsing.
Extracts text from PDF/DOCX and uses spaCy for entity extraction.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from docx import Document
import spacy
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    logger.warning("spaCy model not found. Please download: python -m spacy download en_core_web_sm")
    nlp = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOAD_FOLDER = '/tmp/uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise


def clean_text(text):
    """Clean and normalize extracted text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-]', '', text)
    return text.strip()


def extract_entities(text):
    """Extract entities using spaCy NER."""
    if not nlp:
        return {
            'skills': [],
            'education': [],
            'organizations': [],
            'locations': []
        }
    
    doc = nlp(text)
    
    # Extract skills (common technical terms)
    skills_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'machine learning', 'deep learning', 'ai', 'nlp',
        'git', 'ci/cd', 'agile', 'scrum'
    ]
    skills = []
    text_lower = text.lower()
    for keyword in skills_keywords:
        if keyword in text_lower:
            skills.append(keyword.title())
    
    # Extract education entities
    education = []
    education_keywords = ['university', 'college', 'bachelor', 'master', 'phd', 'degree', 'diploma']
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PERSON']:
            for keyword in education_keywords:
                if keyword in ent.text.lower():
                    education.append(ent.text)
                    break
    
    # Extract organizations
    organizations = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
    
    # Extract locations
    locations = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
    
    return {
        'skills': list(set(skills)),
        'education': list(set(education)),
        'organizations': list(set(organizations[:10])),  # Limit to top 10
        'locations': list(set(locations[:10]))
    }


def extract_experience_years(text):
    """Extract years of experience from text."""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*in',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                years = int(match.group(1))
                return years
            except ValueError:
                continue
    
    return None


def extract_certifications(text):
    """Extract certifications from text."""
    cert_keywords = ['certified', 'certification', 'certificate', 'aws', 'azure', 'gcp', 'pmp', 'cissp']
    certifications = []
    
    # Look for lines containing certification keywords
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        for keyword in cert_keywords:
            if keyword in line_lower:
                # Extract the certification name
                cert = re.sub(r'[^\w\s\-]', '', line).strip()
                if cert and len(cert) > 5:
                    certifications.append(cert)
                    break
    
    return list(set(certifications[:10]))  # Limit to top 10


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'parser_service',
        'spacy_loaded': nlp is not None
    })


@app.route('/api/parse', methods=['POST'])
def parse_resume():
    """Parse resume file and extract structured data."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only PDF and DOCX are supported'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().timestamp()}_{filename}")
        file.save(file_path)
        
        try:
            # Extract text based on file type
            if filename.endswith('.pdf'):
                raw_text = extract_text_from_pdf(file_path)
            elif filename.endswith('.docx'):
                raw_text = extract_text_from_docx(file_path)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400
            
            # Clean text
            cleaned_text = clean_text(raw_text)
            
            # Extract entities
            entities = extract_entities(cleaned_text)
            
            # Extract additional information
            experience_years = extract_experience_years(cleaned_text)
            certifications = extract_certifications(cleaned_text)
            
            # Build parsed data structure
            parsed_data = {
                'raw_text': cleaned_text,
                'skills': entities['skills'],
                'education': entities['education'],
                'organizations': entities['organizations'],
                'locations': entities['locations'],
                'experience_years': experience_years,
                'certifications': certifications,
                'extracted_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully parsed resume: {filename}")
            
            return jsonify({
                'success': True,
                'raw_text': cleaned_text,
                'parsed_data': parsed_data,
                'skills': entities['skills'],
                'education': entities['education'],
                'experience_years': experience_years,
                'certifications': certifications
            }), 200
            
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

