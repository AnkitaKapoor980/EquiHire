"""
Script to preprocess and clean data.
"""
import pandas as pd
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text):
    """Clean and normalize text."""
    if pd.isna(text):
        return ''
    
    text = str(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-]', '', text)
    return text.strip()


def preprocess_resumes(input_path, output_path):
    """Preprocess resume data."""
    logger.info(f"Preprocessing resumes from {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Clean text fields
    if 'text' in df.columns:
        df['text'] = df['text'].apply(clean_text)
    
    # Normalize skills
    if 'skills' in df.columns:
        df['skills'] = df['skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')] if pd.notna(x) else []
        )
    
    # Normalize education
    if 'education' in df.columns:
        df['education'] = df['education'].apply(clean_text)
    
    # Save processed data
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed resumes to {output_path}")


def preprocess_jobs(input_path, output_path):
    """Preprocess job description data."""
    logger.info(f"Preprocessing jobs from {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Clean text fields
    for col in ['title', 'description', 'requirements']:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
    
    # Normalize skills
    if 'required_skills' in df.columns:
        df['required_skills'] = df['required_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')] if pd.notna(x) else []
        )
    
    # Save processed data
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed jobs to {output_path}")


def main():
    """Main preprocessing function."""
    raw_dir = Path(__file__).parent / 'raw'
    processed_dir = Path(__file__).parent / 'processed'
    processed_dir.mkdir(exist_ok=True)
    
    # Process resumes
    resume_files = list(raw_dir.glob('*resume*.csv'))
    for resume_file in resume_files:
        output_file = processed_dir / f"processed_{resume_file.name}"
        preprocess_resumes(resume_file, output_file)
    
    # Process jobs
    job_files = list(raw_dir.glob('*job*.csv'))
    for job_file in job_files:
        output_file = processed_dir / f"processed_{job_file.name}"
        preprocess_jobs(job_file, output_file)
    
    logger.info("Preprocessing completed")


if __name__ == '__main__':
    main()

