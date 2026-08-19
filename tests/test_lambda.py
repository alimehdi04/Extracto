import os
import sys
import json
import pytest
import boto3
from unittest.mock import patch
from moto import mock_aws

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set dummy credentials BEFORE importing the Lambda function
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
os.environ["GEMINI_API_KEY"] = "fake-key"

from src import lambda_function

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    pass

@mock_aws
# We mock 'call_gemini' so it doesn't try to hit the real internet during CI tests
@patch('src.lambda_function.call_gemini') 
def test_lambda_txt_processing(mock_call_gemini, aws_credentials):
    # Setup the mock AI response
    mock_call_gemini.return_value = '{"summary": "Test Summary", "skills": ["Python", "AWS"]}'

    # 1. Setup Fake AWS Infrastructure (S3 and DynamoDB)
    s3 = boto3.client('s3', region_name='ap-south-1')
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    # Create the Fake Bucket
    bucket = "test-bucket"
    file_key = "test_resume.txt"
    s3.create_bucket(
        Bucket=bucket, 
        CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
    )
    # Upload a fake file
    s3.put_object(Bucket=bucket, Key=file_key, Body=b"I am a software engineer knowing Java.")

    # Create the Fake DynamoDB Table
    dynamodb.create_table(
        TableName='ExtractoResults',
        KeySchema=[{'AttributeName': 'document_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'document_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    # 2. Simulate the S3 Event that triggers Lambda
    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": file_key}
            }
        }]
    }

    # 3. ACTUALLY EXECUTE THE LAMBDA FUNCTION
    response = lambda_function.lambda_handler(event, None)
    
    # Verify the Lambda function succeeded
    assert response['statusCode'] == 200

    # 4. Verify DynamoDB received the data
    dynamodb_resource = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb_resource.Table('ExtractoResults')
    db_response = table.get_item(Key={'document_id': file_key})
    
    assert 'Item' in db_response
    assert db_response['Item']['summary'] == "Test Summary"
    assert "Python" in db_response['Item']['skills']