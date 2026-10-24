
import os
import json
import boto3
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Read the SNS topic ARN from Lambda environment variables
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

URL_EXPIRY_SECONDS = int(
    os.environ.get("URL_EXPIRY_SECONDS", "86400")
)


def lambda_handler(event, context):
    sns = boto3.client("sns", region_name="eu-north-1")
    results = []

    for record in event.get("Records", []):
        try:
            bucket_name = record["s3"]["bucket"]["name"]

            object_key = unquote_plus(
                record["s3"]["object"]["key"],
                encoding="utf-8"
            )

            region = record["awsRegion"]

            s3 = boto3.client("s3", region_name=region)

            object_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": object_key
                },
                ExpiresIn=URL_EXPIRY_SECONDS
            )

            message = (
                "A new object has been uploaded to Amazon S3.\n\n"
                f"Bucket: {bucket_name}\n"
                f"Object: {object_key}\n\n"
                "Click the link below to access the object.\n"
                f"The link expires after "
                f"{URL_EXPIRY_SECONDS // 3600} hours.\n\n"
                f"{object_url}"
            )

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="New S3 Object Uploaded",
                Message=message
            )

            logger.info("Notification sent for %s", object_key)

            results.append({
                "bucket": bucket_name,
                "key": object_key,
                "status": "success"
            })

        except Exception:
            logger.exception("Failed to process S3 upload")
            raise

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
