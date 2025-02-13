## N8N KNOWLEDGE BASE PROJECT

**Main Objective**
A knowledge base system built using n8n as the workflow automation platform. 
The system allows users to upload documents, query the content, and give suggestion on how to improve the knowledge base based on user feedback.


## Requirements and End Results:

**Document Upload:**
- Used N8N file handlings nodes to allow local files (PDF) uploading and drive files (PDF/TXT in a publicly shared folder) uploading.
- The maximum number of files can be handled at once is 20. The larger the quanity, the slower the processing speed.
- Stored the uploaded documents on Google Drive.


**Document Processing:**
- Deployed a HTTP Request Node to send documents' chunks to OpenAI Embedding API (text-embedding-3-small).
- Stored and indexed chunks and their embeddings using QDRANT Vector Database using HTTP Request Node on local QDRANT service.


**Query / Web Interface:**
- Deployed a Webhook with HTTP Request Node to receive user query, extract embedding using OpenAI Embedding API (text-embedding-3-small).
- Deployed a HTTP Request Node to retrieval relevant chunks from the QDRANT Vector Database and used the question and chunks to generate answer using HTTP Request Node and OpenAI Chat API (gpt-4o-mini).
- Used Flask, Python, HTML to deploy an API with Web Interface that allows users to: 1) Create knowledge base and upload document ; 2) Query a knowledge base with a textual question ; 3) Send feedback based on the answers received.
- Hosted the app locally and used NGROK to tunnel the API to public access.


**Self-Learning Mechanism:**
- Store the knowledge bases, questions, answers and user feedbacks (thumb up, thumb down and text comments).
- Used the above information for an AI Agent to generate suggestions on how to improve the results.
- Development Direction: Use the above suggestions and AI Tools to automatically tune the parameter or generate finetune datasets for LLM and embedding models.


**Reusable Workflow:**
- The workflow is splitted into seperate parts correspond to the subtasks.
- Each type of uploading methods and files uploaded are handled seperately.
- No over-reliance on n8n's exclusive features (for example use HTTP Request Nodes for Embedding / Chat models instead of using AI Agent and Vector Stores)



