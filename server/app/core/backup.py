import boto3
import datetime
from ..config import settings
from ..core.logging import setup_logging
import asyncio
from typing import List

logger = setup_logging()

class BackupManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY
        )
        self.bucket_name = settings.BACKUP_BUCKET_NAME

    async def create_database_backup(self) -> str:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"db_backup_{timestamp}.sql"
        
        try:
            # Create PostgreSQL dump
            process = await asyncio.create_subprocess_shell(
                f"pg_dump -h {settings.POSTGRES_SERVER} "
                f"-U {settings.POSTGRES_USER} "
                f"-d {settings.POSTGRES_DB} > {backup_file}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Upload to S3
            self.s3_client.upload_file(backup_file, self.bucket_name, f"backups/{backup_file}")
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise

    async def list_backups(self) -> List[str]:
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="backups/"
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            raise
