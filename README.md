# S3 Object Upload Email Notification Using AWS Lambda and SNS

A beginner-friendly, console-based AWS serverless project. Whenever a new object is uploaded to an Amazon S3 bucket, an S3 event invokes an AWS Lambda function. Lambda generates a temporary presigned URL for the object and publishes an email notification through Amazon SNS.

> **Infrastructure is created manually in the AWS Management Console.** This repository stores the Lambda source code and documentation only. It does not deploy AWS resources automatically.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [AWS Services](#aws-services)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Step 1: Create an S3 Bucket](#step-1-create-an-s3-bucket)
- [Step 2: Create an SNS Topic](#step-2-create-an-sns-topic)
- [Step 3: Subscribe an Email Address](#step-3-subscribe-an-email-address)
- [Step 4: Create the Lambda Execution Role](#step-4-create-the-lambda-execution-role)
- [Step 5: Add the Required IAM Permissions](#step-5-add-the-required-iam-permissions)
- [Step 6: Create the Lambda Function](#step-6-create-the-lambda-function)
- [Step 7: Configure Environment Variables](#step-7-configure-environment-variables)
- [Step 8: Add and Deploy the Lambda Code](#step-8-add-and-deploy-the-lambda-code)
- [Step 9: Add the S3 Trigger](#step-9-add-the-s3-trigger)
- [Step 10: Test the Project](#step-10-test-the-project)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Clean Up Resources](#clean-up-resources)
- [Push This Project to GitHub](#push-this-project-to-github)

## Architecture

```text
User uploads an object
        |
        v
Amazon S3 bucket
        |
        | ObjectCreated event
        v
AWS Lambda function
        |
        | 1. Reads bucket, object key, and Region
        | 2. Generates a presigned GET URL
        | 3. Publishes a message
        v
Amazon SNS topic
        |
        | Email subscription
        v
Recipient receives an email with the object link
        |
        v
Clicks the link to access the private object
```

## Features

- Automatically detects new S3 object uploads.
- Uses Lambda to process S3 event notifications.
- Sends email notifications through Amazon SNS.
- Generates a presigned URL with a configurable expiration period.
- Keeps the S3 bucket private; public access is not required.
- Uses IAM permissions to control access between AWS services.
- Uses CloudWatch Logs for troubleshooting.

## AWS Services

| Service | Purpose |
|---|---|
| Amazon S3 | Stores uploaded files and emits object-created events |
| AWS Lambda | Processes the event and generates a presigned URL |
| Amazon SNS | Delivers the notification email |
| AWS IAM | Controls Lambda permissions |
| Amazon CloudWatch Logs | Stores Lambda logs and errors |

## Prerequisites

- An AWS account with permission to create S3, SNS, Lambda, IAM, and CloudWatch resources.
- An email address you can access to confirm the SNS subscription.
- A web browser.
- Git and a GitHub account if you want to publish this repository.

**Region:** Use the same AWS Region for the S3 bucket, Lambda function, and SNS topic for this project. The example environment in this project uses `eu-north-1` (Europe/Stockholm). If you choose another Region, use it consistently and use your actual resource ARNs.

**Important:** AWS services may incur charges. Review current AWS pricing before creating resources.

## Project Structure

```text
s3-lambda-sns-notification/
├── lambda_function.py
├── README.md
└── .gitignore
```

- `lambda_function.py`: Lambda function source code.
- `README.md`: This setup guide.
- `.gitignore`: Helps exclude local files and secrets from Git.

---

## Step 1: Create an S3 Bucket

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Open **Amazon S3**.
3. Select **Create bucket**.
4. Choose the AWS Region you intend to use, for example `eu-north-1`.
5. Enter a globally unique bucket name, such as `my-s3-lambda-notification-demo-12345`. Bucket names must be unique across AWS.
6. Under **Object Ownership**, keep the recommended **Bucket owner enforced** setting unless you have a specific requirement otherwise.
7. Under **Block Public Access settings for this bucket**, keep **Block all public access** enabled.
8. Leave other settings at their defaults unless your requirements differ.
9. Select **Create bucket**.

Record the bucket name and Region for your own notes. Do not make the bucket public to make presigned URLs work.

## Step 2: Create an SNS Topic

1. Open **Amazon SNS** in the AWS Console.
2. Confirm that the console is set to the same Region as the S3 bucket.
3. In the navigation pane, select **Topics**.
4. Select **Create topic**.
5. Select **Standard** as the topic type.
6. Enter a topic name, for example `s3-object-upload-notifications`.
7. Select **Create topic**.
8. Open the topic and copy its **ARN**. It will look similar to:

   ```text
   arn:aws:sns:eu-north-1:123456789012:s3-object-upload-notifications
   ```

   This is only an example. Use the ARN shown in your own AWS account.

## Step 3: Subscribe an Email Address

1. Open the SNS topic you created.
2. Select **Create subscription**.
3. Set **Protocol** to `Email`.
4. Set **Endpoint** to the email address that should receive notifications.
5. Select **Create subscription**.
6. Open the confirmation email from AWS Notifications.
7. Click **Confirm subscription**.
8. Return to SNS and verify that the subscription status is **Confirmed**.

SNS email notifications will not be delivered to an unconfirmed subscription.

## Step 4: Create the Lambda Execution Role

Lambda needs an execution role so it can write logs, read the S3 object when the presigned URL is used, and publish messages to SNS.

1. Open **IAM** in the AWS Console.
2. Select **Roles** in the navigation pane.
3. Select **Create role**.
4. For **Trusted entity type**, select **AWS service**.
5. For **Service or use case**, select **Lambda**.
6. Continue to the permissions step.
7. Attach the AWS-managed policy **AWSLambdaBasicExecutionRole**. This permits Lambda to write logs to CloudWatch.
8. Continue and give the role a name such as `s3-lambda-sns-execution-role`.
9. Review and create the role.
10. Open the newly created role and copy its name for reference.

The role's trust relationship should allow the Lambda service (`lambda.amazonaws.com`) to assume the role. Choosing Lambda as the trusted service configures this for you.

## Step 5: Add the Required IAM Permissions

The execution role also needs permission to read objects from your bucket and publish notifications to your SNS topic.

1. In IAM, open **Roles**.
2. Select `s3-lambda-sns-execution-role` (or the role you created).
3. Under **Permissions**, select **Add permissions** → **Create inline policy**.
4. Open the **JSON** editor.
5. Paste the policy below.
6. Replace `YOUR_BUCKET_NAME` with your exact S3 bucket name.
7. Replace the example SNS ARN with your actual SNS topic ARN.
8. Select **Next**.
9. Name the policy `S3SNSNotificationPolicy`.
10. Select **Create policy**.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadObjectsForPresignedLinks",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    },
    {
      "Sid": "PublishUploadNotifications",
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:eu-north-1:123456789012:s3-object-upload-notifications"
    }
  ]
}
```

The SNS ARN above is a placeholder. Replace the Region, account ID, and topic name with the actual values from your SNS topic.

### Why are these permissions needed?

| Permission | Reason |
|---|---|
| `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` through `AWSLambdaBasicExecutionRole` | Allows Lambda to write execution logs |
| `s3:GetObject` on your bucket's objects | Allows the signed request to retrieve an object, subject to applicable policies and valid credentials |
| `sns:Publish` on the specific SNS topic | Allows Lambda to send the notification |

The Lambda function does not need `s3:PutObject` or `s3:ListBucket` for this workflow.

### Lambda invocation permission

The S3 trigger setup normally adds a Lambda resource-based permission allowing S3 to invoke the function. You can verify it under **Lambda → Configuration → Permissions → Resource-based policy statements** after creating the trigger.

The invocation permission and execution role are different:

- **Resource-based policy:** Allows S3 to invoke Lambda.
- **Execution role:** Allows the running Lambda code to access services such as S3, SNS, and CloudWatch Logs.

---

## Step 6: Create the Lambda Function

1. Open **AWS Lambda** in the AWS Console.
2. Confirm that you are in the same Region as the S3 bucket and SNS topic.
3. Select **Create function**.
4. Select **Author from scratch**.
5. Enter the function name `s3-object-email-notifier` (or your preferred name).
6. Select a supported Python runtime, such as **Python 3.12**, if available in your Region.
7. Under **Permissions**, expand **Change default execution role**.
8. Select **Use an existing role**.
9. Choose `s3-lambda-sns-execution-role`.
10. Select **Create function**.

If you have already created a Lambda function, open that function and verify that its execution role has the required permissions rather than creating a duplicate.

## Step 7: Configure Environment Variables

1. Open the Lambda function.
2. Go to **Configuration** → **Environment variables**.
3. Select **Edit** → **Add environment variable**.
4. Add the following variables:

| Key | Value |
|---|---|
| `SNS_TOPIC_ARN` | The actual SNS topic ARN copied in Step 2 |
| `URL_EXPIRY_SECONDS` | `86400` |

5. Save the changes.

`86400` seconds equals 24 hours. The URL may become invalid earlier if the temporary AWS credentials used to sign it expire or if another policy prevents access.

**Do not use the ARN as the environment variable key.** The key must be `SNS_TOPIC_ARN`, because the Python code reads `os.environ["SNS_TOPIC_ARN"]`.

## Step 8: Add and Deploy the Lambda Code

1. Open the Lambda function's **Code** tab.
2. Open `lambda_function.py` in the inline editor.
3. Replace the existing code with the following.
4. Select **Deploy** to save the code.

```python
import os
import json
import boto3
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
                f"Object: {object_key}\n"
                f"Region: {region}\n\n"
                "Click the link below to access the object.\n"
                f"The link expires after {URL_EXPIRY_SECONDS} seconds.\n\n"
                f"{object_url}"
            )

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="New S3 Object Uploaded",
                Message=message
            )

            logger.info("Notification sent for object: %s", object_key)

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
```

### Important Region note

The SNS client in this example is explicitly configured for `eu-north-1`. If you created your SNS topic in a different Region, update `region_name` to match the SNS topic's Region. Keep the SNS topic ARN and Region consistent.

The S3 client uses the Region in the incoming S3 event. The code uses `unquote_plus` because S3 event notifications URL-encode object keys, including spaces.

### Lambda handler setting

Under **Runtime settings**, confirm that the handler is:

```text
lambda_function.lambda_handler
```

This means the file is named `lambda_function.py` and the handler function is named `lambda_handler`.

## Step 9: Add the S3 Trigger

1. Open the Lambda function.
2. In the function overview, select **Add trigger**.
3. Choose **S3** as the source.
4. Select your bucket.
5. Set **Event type** to **All object create events** (`s3:ObjectCreated:*`).
6. Leave prefix and suffix blank to receive events for all objects.
7. Acknowledge the recursive invocation warning if it appears.
8. Select **Add**.

The trigger configuration should show your S3 bucket attached to the Lambda function.

The function only reads the uploaded object and publishes an SNS message; it does not upload another object to the same bucket, so it should not create a recursive upload loop.

## Step 10: Test the Project

1. Confirm that the SNS email subscription is **Confirmed**.
2. Open your S3 bucket.
3. Select **Upload** and upload a test image, PDF, or text file.
4. Wait for the notification email.
5. Open the email and click the full presigned URL.
6. Verify that the object opens or downloads as expected.
7. Return to Lambda and open **Monitor** → **View CloudWatch logs** to review the execution.

### Expected result

- S3 receives the object.
- S3 invokes Lambda.
- Lambda generates a presigned GET URL.
- Lambda publishes a message to SNS.
- SNS sends an email containing the link.
- The recipient can access the object while the URL and signing credentials remain valid and applicable policies allow access.

---

## Troubleshooting

### 1. No email received

- Confirm the SNS email subscription is confirmed.
- Verify that `SNS_TOPIC_ARN` is correct.
- Confirm the Lambda execution role has `sns:Publish` for the exact topic.
- Check the Lambda's CloudWatch logs for errors.
- Verify the S3 trigger is attached to the correct bucket and event type.

### 2. `AccessDenied`

- Check the Lambda execution role's `s3:GetObject` permission for the exact bucket/object ARN.
- Check for bucket policies, AWS Organizations service control policies, VPC endpoint policies, or other explicit denies.
- Remember that a presigned URL uses the permissions of the AWS identity that signed it. The URL does not override explicit denies.

### 3. `SignatureDoesNotMatch`

- Use the complete URL exactly as generated; do not edit or truncate its query parameters.
- Ensure the S3 client uses the bucket's actual Region.
- Verify the exact bucket name and object key.
- Generate a fresh URL and test it before its expiration.
- Avoid copying a URL through software that changes characters or strips query parameters.

### 4. `ExpiredToken` or a link stops working early

The URL's configured expiry is a maximum, not a guarantee. If Lambda uses temporary role credentials, the URL can stop working when those credentials expire. Generate a fresh URL if needed.

### 5. Lambda logs show missing environment variable

Verify that the environment variable key is exactly `SNS_TOPIC_ARN` and its value is the full SNS topic ARN. Deploy code changes and save environment-variable changes.

### 6. S3 cannot invoke Lambda

Check **Lambda → Configuration → Permissions** for a resource-based policy allowing `s3.amazonaws.com` to invoke the function, scoped to the intended bucket and account. Adding permissions to the execution role does not grant S3 permission to invoke Lambda.

---

## Security Considerations

- Keep **S3 Block Public Access** enabled.
- Do not grant public `s3:GetObject` access just to make the link work.
- Treat presigned URLs as bearer credentials: anyone who obtains a valid URL can access the object while it works.
- Use the shortest practical URL expiry. This demo uses 24 hours for learning purposes.
- Never commit AWS access keys, secret keys, session tokens, `.aws/credentials`, real presigned URLs, or sensitive account data to GitHub.
- Restrict IAM policies to the specific S3 bucket and SNS topic.
- Consider validating allowed file types and sizes if the bucket accepts uploads from untrusted users.
- Enable appropriate logging and monitor failures.
- Review AWS pricing and delete resources when you finish experimenting.

## Clean Up Resources

To avoid ongoing charges after the project, delete resources when you no longer need them:

1. Remove the S3 event trigger from the Lambda function, if desired.
2. Empty the S3 bucket, including object versions and delete markers if versioning is enabled.
3. Delete the S3 bucket.
4. Delete the Lambda function.
5. Delete the SNS subscription and topic.
6. Delete the custom inline IAM policy.
7. Delete the custom Lambda execution role if it is no longer used.
8. Review CloudWatch log groups and delete them if you no longer need the logs.

Be careful not to delete IAM roles, buckets, topics, or log groups used by other projects.

## Push This Project to GitHub

Create a new repository on GitHub, for example `s3-lambda-sns-notification`. Do not add a second README on GitHub if you already created this file locally.

From your local project folder, run:

```bash
git init
git add lambda_function.py README.md .gitignore
git commit -m "Add S3 Lambda SNS notification project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/s3-lambda-sns-notification.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

Before pushing, inspect the files and run `git status`. If credentials are accidentally exposed, revoke or rotate them; deleting a secret in a later commit does not remove it from Git history.

## Future Improvements

- Add CloudWatch alarms for Lambda errors.
- Add unit tests for the Lambda function.
- Add file type and file size validation.
- Use a shorter URL expiry or a controlled download service for sensitive objects.
- Add GitHub Actions for linting and automated tests (without storing long-lived AWS keys in GitHub).
- Add an architecture diagram and screenshots with account IDs and sensitive details redacted.

## Author

Cloud / DevSecOps learning project.
