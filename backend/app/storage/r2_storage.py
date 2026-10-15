import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class R2Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self.bucket_name = settings.R2_BUCKET_NAME

    def upload_file(self, file_obj, object_key: str, content_type: str) -> str:
        self.client.upload_fileobj(
            file_obj,
            self.bucket_name,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
        return object_key

    def delete_file(self, object_key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=object_key,
        )

    def file_exists(self, object_key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return True
        except ClientError as exc:
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code == 404:
                return False
            raise