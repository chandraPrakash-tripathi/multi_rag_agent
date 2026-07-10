1) ARCHITECTURE:
Primary Assistant: This is the entry point for user queries. It routes the conversation to specialized assistants based on the user's needs.
Specialized Assistants:
                        Flight Booking Assistant: Handles flight-related queries and bookings.
                        Car Rental Assistant: Manages car rental requests.
                        Hotel Booking Assistant: Processes hotel reservation queries.
                        Excursion Assistant: Handles trip and excursion recommendations.
Tool Nodes: Each assistant has access to both safe and sensitive tools. Safe tools can be used without user confirmation, while sensitive tools require user approval before execution.
Routing Logic: The system uses conditional edges to route the conversation between assistants and tool nodes based on the current state and user input.
User Confirmation: For sensitive operations, the system pauses and asks for user confirmation before proceeding.
Memory and State Management: The system maintains conversation state and uses a memory checkpointer to save progress.


2) FOR OBSERVABILTY : To ensure effective monitoring and debugging capabilities, the project integrates LangSmith for enhanced observability. LangSmith helps track the lifecycle of requests, including tool usage, agent responses, and errors, allowing developers to understand how the multi-agent system performs over time.

3) Architecture on AWS
This architecture illustrates a production-ready **Multi-Agent Retrieval-Augmented Generation (RAG)** system deployed on **AWS** for an AI-powered customer support application. Users interact with the system through an **API Gateway**, which routes requests to the **Customer Support Chat** service running on **Amazon EKS**. The chatbot performs Retrieval-Augmented Generation by querying the **Qdrant Search API**, which retrieves semantically relevant document embeddings from the **Qdrant Vector Database**, while the **AI Platform (Amazon SageMaker/Amazon Bedrock)** generates the final response using Large Language Models (LLMs). Enterprise documents are ingested into an **Amazon S3 Data Lake**, orchestrated through **Apache Airflow on EKS**, where an **Embedding Generation Job** preprocesses, chunks, and converts documents into vector embeddings before storing them in Qdrant for efficient semantic search. **Redis Cache** is used to reduce latency by caching frequently accessed queries and responses. For analytics and reporting, data stored in S3 can be queried using **Amazon Athena**, transformed into analytical datasets within **Amazon Redshift**, and visualized through **Grafana** dashboards. Operational monitoring and logging are handled by **Amazon CloudWatch**, while sensitive credentials such as API keys and database passwords are securely managed using **AWS Secrets Manager**. The entire application lifecycle is automated through a **CI/CD pipeline**, where source code is built into Docker images, stored in **Amazon Elastic Container Registry (ECR)**, and deployed to **Amazon EKS**, enabling scalable, secure, and continuously deployable AI services.

                 User
                   │
                   ▼
             API Gateway
                   │
                   ▼
      Customer Support Chat (EKS)
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
Qdrant Search API      AI Platform
        │                     │
        ▼                     │
 Qdrant Vector DB             │
        ▲                     │
        │                     │
Embedding Generation Job ◄────┘
        ▲
        │
 Airflow on EKS
        ▲
        │
   Amazon S3 (Data Lake)

S3
 │
 ▼
Athena
 │
 ▼
Redshift
 │
 ▼
Grafana

CloudWatch monitors all services.
Secrets Manager provides secure credentials.
CI/CD builds Docker images, stores them in ECR, and deploys them to EKS.

Complete System Flow
A user sends a query through the application.
The request is routed via API Gateway to the Customer Support Chat service running on Amazon EKS.
The chatbot generates an embedding for the user query and sends it to the Qdrant Search API.
The Search API performs a semantic similarity search on the Qdrant Vector Database and retrieves the most relevant document chunks.
These retrieved documents are combined with the original user query to form an augmented prompt.
The prompt is sent to the AI Platform (Amazon Bedrock or SageMaker), which generates a context-aware response using a Large Language Model (LLM).
The generated response is returned to the chatbot and then back to the user.
In parallel, enterprise documents are continuously ingested into Amazon S3, processed by Airflow, converted into vector embeddings by the Embedding Generation Job, and stored in Qdrant for future retrieval.
Redis caches frequently accessed results to reduce response latency and minimize repeated LLM invocations.
Athena, Redshift, and Grafana support analytics, reporting, and operational dashboards, while CloudWatch monitors system health and Secrets Manager securely manages credentials. Finally, the CI/CD pipeline builds container images, stores them in Amazon ECR, and deploys updated services to Amazon EKS, enabling automated and reliable application updates.


Data Layer
S3 Data Lake: Stores raw, intermediate, and processed data following a medallion architecture (Bronze, Silver, Gold). Data engineers manage these datasets, which are used for AI models and vector embeddings.
Athena and Redshift: Athena queries the S3 Data Lake, providing SQL-like access to large datasets. Redshift acts as the data warehouse for more complex and large-scale analytics tasks, providing a consolidated view of the processed data.
Qdrant Vector Database (DynamoDB on the image): Stores and manages the vector embeddings generated by the system, enabling fast retrieval of relevant documents or information through vector search.
ElastiCache (Redis): Serves as a cache and state management system, storing user session data and interactions for long-term memory in the chat service, enhancing user experience by allowing agents to retain historical context.


Data Processing
Airflow on EKS: Manages the orchestration of scheduled tasks such as data processing and embedding generation. It ensures that the embeddings are up-to-date by running scheduled jobs.
Embedding Generation Job (EC2): A dedicated job that generates embeddings for the processed data, which are stored in the Qdrant Vector Database. This is triggered as part of the data processing pipeline.
SageMaker/Bedrock: AWS machine learning services are used for training AI models and improving the performance of the support system. SageMaker allows for scaling and management of model training and deployment.


Chat Service
Customer Support Chat (EKS): The customer-facing chat service is hosted on Amazon EKS. It handles incoming user queries and delegates tasks to various agents. This component interfaces with the Qdrant database for vector search and the Redis cache for maintaining user session data.
API Gateway: Exposes the chat service API, acting as the entry point for client requests. It helps route user queries to the right service.
Qdrant Search API: Handles search queries against the Qdrant vector database, retrieving relevant data based on vector embeddings.

Model CI/CD
CodePipeline and CodeBuild: The CI/CD pipeline automates the build and deployment process for both the vectorizer and the chat services. This allows for continuous updates to the system with minimal manual intervention.
Docker Image Store (ECR): Stores the Docker images for the vectorizer and chat services, allowing for scalable deployment within EKS or other containerized environments.
Monitoring and Security
CloudWatch: Monitors the system's health, logging performance metrics and triggering alerts for any issues across the chat service, embedding generation, and vector search.
Secrets Manager: Manages sensitive information such as API keys, database credentials, and other configuration secrets securely across the system.
Grafana: Provides real-time visualization and monitoring for data analytics, connected to Redshift for dashboarding insights from the underlying data.