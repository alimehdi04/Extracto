import boto3
import time
import sys

# --- Configuration ---
REGION = "ap-south-1"
BUCKET_NAME = "extracto-docs-alimehdi-2026"
TABLE_NAME = "ExtractoResults"
FILE_NAME = "test_resume.txt"

# --- Initialize AWS Clients ---
# boto3 automatically uses the credentials configured in your AWS CLI
try:
    s3 = boto3.client('s3', region_name=REGION)
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
except Exception as e:
    print(f"❌ Failed to initialize AWS clients. Ensure your AWS CLI is configured.\nError: {e}")
    sys.exit(1)

def run_demo():
    print("🚀 Starting Extracto Serverless AI Pipeline...\n")
    
    # 1. Upload the file to S3
    print(f"📤 [Step 1] Uploading '{FILE_NAME}' to S3 bucket '{BUCKET_NAME}'...")
    try:
        s3.upload_file(FILE_NAME, BUCKET_NAME, FILE_NAME)
        print("✅ Upload successful! S3 Event Trigger fired.")
    except Exception as e:
        print(f"❌ Failed to upload file: {e}")
        return

    # 2. Wait for the asynchronous backend to finish
    print("⏳ [Step 2] AI Backend is processing (Lambda -> Gemini AI -> DynamoDB)...")
    
    # Create a simple visual loading spinner in the terminal
    for _ in range(7):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(1)
    print("\n")

    # 3. Fetch the results from DynamoDB
    print(f"📥 [Step 3] Fetching structured AI data from DynamoDB table '{TABLE_NAME}'...")
    try:
        response = table.get_item(Key={'document_id': FILE_NAME})
        
        if 'Item' in response:
            item = response['Item']
            print("\n🎉 --- AI ANALYSIS COMPLETE --- 🎉\n")
            print(f"📄 Document ID : {item.get('document_id')}")
            print(f"📝 AI Summary  : {item.get('summary')}")
            
            # Format the skills list nicely
            skills = item.get('skills', [])
            skills_str = ", ".join(skills) if skills else "None extracted"
            print(f"🛠️  Tech Skills : {skills_str}\n")
            print("----------------------------------\n")
        else:
            print("⚠️ Data not found yet. The AI processing might be taking longer than expected.")
    except Exception as e:
        print(f"❌ Failed to fetch from DynamoDB: {e}")

if __name__ == "__main__":
    run_demo()