# aws_bedrock_examples
Examples of AWS bedrock
#### 07_how_to_create_a_knowledge_base

Below are the trust relation and the policy json required
for the role used in this example

```json

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AmazonBedrockKnowledgeBaseTrustPolicy",
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "643045476917"
                },
                "ArnLike": {
                    "aws:SourceArn": "arn:aws:bedrock:us-east-1:643045476917:knowledge-base/*"
                }
            }
        }
    ]
}

```

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": [
                "arn:aws:aoss:us-east-1:643045476917:collection/anddc4hozkwk6bnbzkd5"
            ]
        }
    ]
}
```

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:ListCustomModels"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
            ]
        }
    ]
}
```
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3ListBucketStatement",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bedrock-agent01"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceAccount": "643045476917"
                }
            }
        },
        {
            "Sid": "S3GetObjectStatement",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::bedrock-agent01/loan_estimate.pdf"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceAccount": "643045476917"
                }
            }
        }
    ]
}
```