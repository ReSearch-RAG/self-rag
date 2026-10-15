import os
import boto3
from dotenv import load_dotenv

# Pathing to your root folder .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

def verify_cloud_link():
    print("gChecking configuration setup...")
    
    bucket_name = os.getenv("R2_BUCKET_NAME")
    if not bucket_name:
        print(" Error: Could not read your .env file! Double-check the filename or path.")
        return

    print(f" Found configurations for bucket: {bucket_name}")

    try:
        s3_client = boto3.client(
            service_name="s3",
            endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto"
        )
        
        # FIXED: Instead of listing all buckets, we test writing a tiny micro-file right into your bucket
        test_object_key = "connection_test_marker.txt"
        
        print(f"Attempting to verify write access in bucket '{bucket_name}'...")
        s3_client.put_object(
            Bucket=bucket_name, 
            Key=test_object_key, 
            Body=b"Cloudflare R2 connection test successful!"
        )
        print("Write access verified successfully!")

        print(f" Attempting to verify read access...")
        s3_client.get_object(Bucket=bucket_name, Key=test_object_key)
        print("Read access verified successfully!")

        # Clean up the test marker file
        s3_client.delete_object(Bucket=bucket_name, Key=test_object_key)
        
        print("Success! Full read/write connection established. Your CRAG storage pipeline is ready!")
        
    except Exception as e:
        print(f" Cloud Connection Refused: {e}")

if __name__ == "__main__":
    verify_cloud_link()
