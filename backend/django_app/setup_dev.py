import os
import subprocess
from pathlib import Path

def setup_environment():
    """Set up the development environment."""
    # Project root directory
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    
    # Create .env file if it doesn't exist
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("""# Django Settings
DEBUG=True
SECRET_KEY='django-insecure-your-secret-key-here'
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MinIO Settings
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=resumes
MINIO_SECURE=False
""")
        print("✅ Created .env file with default settings")
    
    # Update settings.py with correct host configuration
    settings_path = project_root / 'equihire' / 'settings.py'
    if settings_path.exists():
        with open(settings_path, 'r+') as f:
            content = f.read()
            
            # Update database settings
            if "DB_HOST = 'host.docker.internal'" not in content:
                content = content.replace(
                    "'HOST': os.getenv('POSTGRES_HOST', 'postgres')",
                    "'HOST': os.getenv('POSTGRES_HOST', 'localhost')"
                )
                
                # Update MinIO settings
                content = content.replace(
                    "MINIO_HOST = 'minio' if IS_RUNNING_IN_DOCKER else 'localhost'",
                    "MINIO_HOST = 'host.docker.internal' if os.getenv('DOCKER_CONTAINER', 'False').lower() == 'true' else 'localhost'"
                )
                
                f.seek(0)
                f.write(content)
                f.truncate()
                print("✅ Updated settings.py with local development configuration")
    
    # Check if Docker is running
    try:
        subprocess.run(['docker', 'ps'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Docker is running")
        
        # Start services using docker-compose
        compose_file = project_root.parent / 'docker-compose.yml'
        if compose_file.exists():
            print("🚀 Starting Docker services...")
            subprocess.run(['docker-compose', 'up', '-d', 'postgres', 'minio'], cwd=project_root.parent)
            print("✅ Docker services started")
            
            # Create MinIO bucket
            print("🔄 Setting up MinIO bucket...")
            subprocess.run([
                'docker', 'run', '--rm', '--network', 'host', 'minio/mc',
                'alias', 'set', 'myminio', 'http://localhost:9000', 'minioadmin', 'minioadmin'
            ])
            subprocess.run([
                'docker', 'run', '--rm', '--network', 'host', 'minio/mc',
                'mb', '--ignore-existing', 'myminio/resumes'
            ])
            print("✅ MinIO bucket 'resumes' is ready")
            
    except subprocess.CalledProcessError:
        print("⚠️  Docker is not running or not installed. Please start Docker Desktop.")
    except FileNotFoundError:
        print("⚠️  Docker is not installed. Please install Docker Desktop.")
    
    print("\n🎉 Development environment setup complete!")
    print("You can now start the Django development server with:")
    print("python manage.py runserver")

if __name__ == "__main__":
    setup_environment()
