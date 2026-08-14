# Extracto: Serverless AI Document Analyzer

An enterprise-grade, event-driven cloud architecture that automatically analyzes uploaded documents using Generative AI. Built entirely on AWS, provisioned via Terraform, and deployed using a fully automated GitHub Actions CI/CD pipeline.

## 🚀 Overview

Extracto acts as a highly scalable, zero-maintenance backend for processing unstructured text. When a document (PDF or TXT) is uploaded to an S3 bucket, it triggers a serverless Lambda function. This function extracts the raw text, securely communicates with the Google Gemini AI REST API to generate a professional summary and extract technical skills, and saves the structured JSON data into a DynamoDB NoSQL table.

### Key Features
*   **100% Serverless:** No idle compute costs. The system scales instantly to zero when not in use.
*   **Event-Driven:** Fully decoupled architecture using S3 Event Notifications to trigger backend processing.
*   **Infrastructure as Code (IaC):** Every cloud resource is strictly defined in Terraform, utilizing a remote S3 backend for state management.
*   **Automated CI/CD:** GitHub Actions automatically lints, packages, and deploys infrastructure updates to AWS upon any push to the `main` branch.
*   **Zero-Dependency Python:** The Lambda execution environment uses native Python libraries (`urllib`) to handle REST API requests, keeping the deployment package under 5KB and eliminating binary incompatibility errors.

---

## 🏗 Architecture Flow

1.  **Input:** User uploads a `.txt` or `.pdf` file to the S3 Drop Bucket.
2.  **Trigger:** S3 instantly emits an `ObjectCreated` event.
3.  **Compute:** AWS Lambda wakes up, retrieves the file content, and formats a prompt.
4.  **AI Inference:** Lambda sends a native HTTP POST request to the Google Gemini 3.6 Flash API.
5.  **Storage:** The returned JSON (containing the summary and skills array) is written to Amazon DynamoDB.

---

## 💰 Cost Analysis (Strictly AWS Free Tier)

This architecture is designed mathematically to operate permanently within the AWS Free Tier constraints, resulting in a **$0.00 monthly bill** for portfolio demonstration purposes:

| Service | Free Tier Limit | Extracto Resource Usage |
| :--- | :--- | :--- |
| **AWS Lambda** | 1,000,000 requests / month | ~256MB memory allocation. Executes in < 2 seconds. |
| **Amazon S3** | 5 GB standard storage | Text/PDF files average < 1MB. |
| **Amazon DynamoDB** | 25 GB storage, 25 WCU/RCU | Records are stored as lightweight JSON (< 5KB each). |
| **Google Gemini API** | 1,500 requests / day | Completely free tier utilizing `gemini-3.6-flash`. |

---

## 🛠 Deployment Setup

### Prerequisites
*   AWS CLI installed and authenticated.
*   Terraform CLI installed.
*   A Google AI Studio API Key.

### Manual Deployment
1. Clone the repository: `git clone https://github.com/alimehdi04/Extracto.git`
2. Navigate to the root directory and initialize Terraform: `terraform init`
3. Apply the infrastructure: `terraform apply`
   *(Note: You will be prompted to provide your Gemini API key securely during this step).*

### Automated Deployment (GitHub Actions)
To utilize the CI/CD pipeline, add the following Repository Secrets to your GitHub settings:
*   `AWS_ACCESS_KEY_ID`
*   `AWS_SECRET_ACCESS_KEY`
*   `GEMINI_API_KEY`

---

## 👨‍💻 Author
**Ali Mehdi Naqvi**
Software Engineer | Cloud Infrastructure & Full-Stack Development