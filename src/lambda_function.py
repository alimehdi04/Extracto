import json
import boto3
import os
import io
import urllib.parse
import urllib.request
from PyPDF2 import PdfReader

# Initialize AWS Clients (Pre-installed in AWS Lambda)
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ExtractoResults')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def call_gemini(prompt_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        return res_data['candidates'][0]['content']['parts'][0]['text']

def lambda_handler(event, context):
    try:
        # 1. Extract Bucket and decoded Key
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        raw_key = event['Records'][0]['s3']['object']['key']
        file_key = urllib.parse.unquote_plus(raw_key, encoding='utf-8')
        
        # 2. Download File Content from S3 into memory
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read()
        
        extracted_text = ""
        
        # 3. Extract text based on file type
        if file_key.lower().endswith('.pdf'):
            print(f"Processing PDF document: {file_key}")
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        else:
            print(f"Processing TXT document: {file_key}")
            extracted_text = file_content.decode('utf-8', errors='ignore')
        
        # 4. Prompt Gemini for structured analysis
        prompt = (
            "Analyze the following document. Provide a short professional summary and extract a list of key technical skills. "
            "Respond strictly in valid JSON format with keys 'summary' and 'skills' (array of strings). Do not use markdown backticks.\n\n"
            f"Document text:\n{extracted_text[:8000]}"
        )
        
        ai_raw_output = call_gemini(prompt)
        
        # Clean up any potential markdown formatting
        cleaned_json = ai_raw_output.replace('```json', '').replace('```', '').strip()
        parsed_data = json.loads(cleaned_json)
        
        # 5. Save structured data to DynamoDB
        table.put_item(
            Item={
                'document_id': file_key,
                'summary': parsed_data.get('summary', 'No summary generated.'),
                'skills': parsed_data.get('skills', [])
            }
        )
        
        print(f"Successfully processed {file_key}")
        return {"statusCode": 200, "body": json.dumps("Success")}
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(str(e))}