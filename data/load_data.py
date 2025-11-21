"""
Script to load Kaggle datasets into PostgreSQL.
Handles resume and job description data.
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from pathlib import Path

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


def load_resumes(csv_path, conn):
    """Load resume data from CSV."""
    logger.info(f"Loading resumes from {csv_path}")
    
    df = pd.read_csv(csv_path)
    cursor = conn.cursor()
    
    # Create a default candidate user if not exists
    cursor.execute("""
        INSERT INTO users (email, username, role, is_active)
        VALUES ('default_candidate@example.com', 'default_candidate', 'candidate', true)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
    """)
    result = cursor.fetchone()
    if result:
        candidate_id = result[0]
    else:
        cursor.execute("SELECT id FROM users WHERE email = 'default_candidate@example.com'")
        candidate_id = cursor.fetchone()[0]
    
    # Insert resumes
    resumes_data = []
    for idx, row in df.iterrows():
        # Handle different column name formats
        resume_text = row.get('text', '') or row.get('Resume_str', '') or row.get('Resume', '')
        resume_id = row.get('ID', idx)
        category = row.get('Category', '') or row.get('Role', '')
        
        # Extract skills and education from text if not in separate columns
        skills = []
        if 'skills' in df.columns and pd.notna(row.get('skills')):
            skills = [s.strip() for s in str(row.get('skills')).split(',')]
        elif 'Skills' in df.columns and pd.notna(row.get('Skills')):
            skills = [s.strip() for s in str(row.get('Skills')).split(';')]
        
        education = []
        if 'education' in df.columns and pd.notna(row.get('education')):
            education = [e.strip() for e in str(row.get('education')).split(',')]
        
        experience_years = None
        if 'experience_years' in df.columns and pd.notna(row.get('experience_years')):
            try:
                experience_years = int(row.get('experience_years'))
            except (ValueError, TypeError):
                pass
        elif 'YearsOfExperience' in df.columns and pd.notna(row.get('YearsOfExperience')):
            try:
                # Handle ranges like "0-1" or "3-5"
                exp_str = str(row.get('YearsOfExperience'))
                if '-' in exp_str:
                    experience_years = int(exp_str.split('-')[0])
                else:
                    experience_years = int(exp_str)
            except (ValueError, TypeError):
                pass
        
        resumes_data.append((
            candidate_id,
            f'resume_{resume_id}.pdf',
            f'data/raw/resumes/resume_{resume_id}.pdf',
            0,  # file_size
            'application/pdf',
            resume_text,
            {'raw_text': resume_text, 'category': category, 'html': row.get('Resume_html', '')},
            skills,
            education,
            experience_years,
            True
        ))
    
    execute_values(
        cursor,
        """
        INSERT INTO resumes (candidate_id, file_name, file_path, file_size, file_type,
                           raw_text, parsed_data, skills, education, experience_years, is_active)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        resumes_data
    )
    
    conn.commit()
    logger.info(f"Loaded {len(resumes_data)} resumes")
    cursor.close()


def load_jobs(csv_path, conn):
    """Load job descriptions from CSV."""
    logger.info(f"Loading jobs from {csv_path}")
    
    df = pd.read_csv(csv_path)
    cursor = conn.cursor()
    
    # Create a default recruiter user if not exists
    cursor.execute("""
        INSERT INTO users (email, username, role, is_active)
        VALUES ('default_recruiter@example.com', 'default_recruiter', 'recruiter', true)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
    """)
    result = cursor.fetchone()
    if result:
        recruiter_id = result[0]
    else:
        cursor.execute("SELECT id FROM users WHERE email = 'default_recruiter@example.com'")
        recruiter_id = cursor.fetchone()[0]
    
    # Insert job descriptions
    jobs_data = []
    for idx, row in df.iterrows():
        # Handle different column name formats
        title = row.get('title', '') or row.get('Title', '') or f'Job {idx}'
        description = row.get('description', '') or row.get('Job_Description', '') or row.get('Responsibilities', '')
        requirements = row.get('requirements', '') or row.get('Requirements', '') or row.get('Responsibilities', '')
        location = row.get('location', '') or row.get('Location', '')
        
        # Handle skills
        required_skills = []
        if 'required_skills' in df.columns and pd.notna(row.get('required_skills')):
            required_skills = [s.strip() for s in str(row.get('required_skills')).split(',')]
        elif 'Skills' in df.columns and pd.notna(row.get('Skills')):
            required_skills = [s.strip() for s in str(row.get('Skills')).split(';')]
        elif 'Keywords' in df.columns and pd.notna(row.get('Keywords')):
            required_skills = [s.strip() for s in str(row.get('Keywords')).split(';')]
        
        # Handle salary (if available)
        salary_min = None
        salary_max = None
        if 'salary_min' in df.columns and pd.notna(row.get('salary_min')):
            try:
                salary_min = float(row.get('salary_min'))
            except (ValueError, TypeError):
                pass
        if 'salary_max' in df.columns and pd.notna(row.get('salary_max')):
            try:
                salary_max = float(row.get('salary_max'))
            except (ValueError, TypeError):
                pass
        
        # Determine employment type from experience level if available
        employment_type = row.get('employment_type', 'full-time')
        if 'ExperienceLevel' in df.columns:
            exp_level = str(row.get('ExperienceLevel', '')).lower()
            if 'fresher' in exp_level or 'intern' in exp_level:
                employment_type = 'full-time'  # or 'internship' if you have that option
        
        jobs_data.append((
            title,
            description,
            requirements,
            location,
            salary_min,
            salary_max,
            employment_type,
            required_skills,
            recruiter_id,
            True
        ))
    
    execute_values(
        cursor,
        """
        INSERT INTO job_descriptions (title, description, requirements, location,
                                     salary_min, salary_max, employment_type,
                                     required_skills, posted_by_id, is_active)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        jobs_data
    )
    
    conn.commit()
    logger.info(f"Loaded {len(jobs_data)} job descriptions")
    cursor.close()


def main():
    """Main function to load all data."""
    data_dir = Path(__file__).parent / 'raw'
    
    conn = get_db_connection()
    
    try:
        # Load resumes
        resume_files = list(data_dir.glob('*resume*.csv'))
        for resume_file in resume_files:
            load_resumes(resume_file, conn)
        
        # Load jobs
        job_files = list(data_dir.glob('*job*.csv'))
        for job_file in job_files:
            load_jobs(job_file, conn)
        
        logger.info("Data loading completed successfully")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()

