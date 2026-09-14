# Cloud-Native DevOps Platform

A cloud-native infrastructure health monitoring platform built to demonstrate
modern DevOps, containerization, Kubernetes, GitOps, Infrastructure as Code,
CI/CD, and observability practices.

## Overview

This project implements a containerized FastAPI application that exposes
infrastructure health endpoints and Prometheus metrics.

The application is automatically tested and built through GitHub Actions,
published as a Docker image to GitHub Container Registry (GHCR), and deployed
to Kubernetes using Helm and Argo CD.

Infrastructure resources are managed with Terraform, while Nginx is used as a
reverse proxy and Prometheus and Grafana provide monitoring, visualization,
and alerting.

## Architecture

The platform follows a GitOps-based deployment workflow:

```text
Developer
    │
    ▼
GitHub Repository
    │
    ▼
GitHub Actions
(Test → Build → Push Docker Image)
    │
    ▼
GitHub Container Registry (GHCR)
    │
    ▼
Argo CD
    │
    ▼
Kubernetes
    │
    ├── FastAPI Application
    │       │
    │       ▼
    │   Prometheus Metrics
    │
    └── Nginx Reverse Proxy


Kubernetes → Prometheus → Grafana Dashboard & Alerting

Terraform → Infrastructure Provisioning
```

## Tech Stack

### Application
- Python 3.11
- FastAPI
- Uvicorn

### Containerization & CI/CD
- Docker
- GitHub Actions
- GitHub Container Registry (GHCR)

### Kubernetes & GitOps
- Kubernetes
- Helm
- Argo CD
- Nginx
- kind

### Infrastructure as Code
- Terraform
- Terraform Kubernetes Provider

### Observability
- Prometheus
- Grafana
- Prometheus FastAPI Instrumentator

## CI/CD Pipeline

The project uses GitHub Actions to automate testing and Docker image builds.

The workflow runs on pushes to the `main` branch and on pull requests.

For each workflow run:

1. The repository is checked out.
2. Python dependencies are installed.
3. Automated API tests are executed with Pytest.
4. A Docker image is built.

On pushes to the `main` branch, the Docker image is published to GitHub
Container Registry (GHCR). 

Argo CD continuously monitors the Git repository and reconciles the Kubernetes
environment with the desired state defined in Git and Helm.

## Kubernetes & GitOps

The application is deployed on a local Kubernetes cluster using kind.

Helm is used to package and configure the application deployment, including:

- 2 application replicas
- Readiness and liveness probes
- CPU and memory requests and limits
- Kubernetes Service configuration
- Prometheus ServiceMonitor configuration

Argo CD manages the application deployment using a GitOps approach. The
desired Kubernetes state is stored in the Git repository and continuously
reconciled by Argo CD.

Automated synchronization, pruning, and self-healing are enabled, allowing
the cluster to automatically return to the desired state defined in Git.

## Infrastructure as Code

Terraform is used to provision and manage Kubernetes infrastructure through
the Terraform Kubernetes Provider.

In this project, Terraform manages the `platform` Kubernetes namespace,
demonstrating Infrastructure as Code and declarative infrastructure
management.

## Observability

The application exposes Prometheus metrics through the FastAPI
Prometheus Instrumentator.

Prometheus collects application and Kubernetes metrics, while Grafana is used
for visualization and alerting.

The custom Grafana dashboard includes:

- HTTP request rate
- HTTP error rate
- 95th percentile request latency
- Number of ready API pods

A Grafana alert is configured to detect when fewer than 2 API pods are ready,
helping demonstrate basic Kubernetes availability monitoring and alerting.

## Project Structure

```text
cloud-devops-platform/
├── app/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   └── test_api.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── helm/
│   └── infrastructure-health-api/
│       ├── templates/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   ├── servicemonitor.yaml
│       │   └── _helpers.tpl
│       ├── Chart.yaml
│       ├── values.yaml
│       └── .helmignore
│
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── nginx/
│       ├── deployment.yaml
│       └── service.yaml
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
│
├── argocd/
│   ├── application.yaml
│   └── nginx-application.yaml
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── .terraform.lock.hcl
│
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

## Application Endpoints

The FastAPI application exposes the following endpoints:

| Endpoint | Description |
|----------|-------------|
| `/` | Application information |
| `/health` | Health check endpoint |
| `/api/system` | Basic system information |
| `/metrics` | Prometheus metrics |

## Deployment Workflow

The deployment workflow follows a GitOps-based approach:

```text
Code Change
    │
    ▼
GitHub
    │
    ▼
GitHub Actions
    │
    ├── Run Tests
    └── Build Docker Image
            │
            ▼
          GHCR
            │
            ▼
      Git-defined State
            │
            ▼
         Argo CD
            │
            ▼
      Helm Deployment
            │
            ▼
       Kubernetes
```
Argo CD continuously reconciles the Kubernetes environment against the
desired configuration stored in Git.

## Running the Project Locally

### Prerequisites

The following tools are required:

- Docker Desktop
- Git
- Python 3.11+
- kubectl
- kind
- Helm
- Terraform

### Run the Tests

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
Install the project dependencies:
pip install -r requirements.txt
pip install pytest httpx
Run the automated tests:
python -m pytest
Kubernetes Cluster
Create the local Kubernetes cluster using kind:
kind create cluster --name cloud-devops
If the cluster already exists, verify its status with:
kubectl get nodes
The Kubernetes node should be in Ready status.
Terraform
Initialize Terraform:
cd terraform
terraform init
Review the planned infrastructure changes:
terraform plan
Apply the Terraform configuration:
terraform apply
Terraform manages the Kubernetes infrastructure defined in the Terraform configuration, currently provisioning the platform namespace.
Return to the project root:
cd ..
Validate the Helm Chart
The Helm chart can be validated locally with:
helm lint helm/infrastructure-health-api
The chart is deployed through Argo CD as part of the GitOps workflow.
Argo CD Deployment
The Argo CD application definition is located at:
argocd/application.yaml
Argo CD monitors the Git repository and uses the Helm chart to deploy and manage the FastAPI application.
The application status can be checked with:
kubectl get applications -n argocd
The application should eventually report:
Synced
Healthy
Verify Kubernetes Resources
Check the application pods:
kubectl get pods
Check the Kubernetes services:
kubectl get services
The FastAPI application should run with two replicas.
Access the Application
The application can be accessed locally through the Nginx reverse proxy:
kubectl port-forward service/nginx-reverse-proxy 8081:80
Then open:
http://localhost:8081
The Nginx reverse proxy forwards requests to the FastAPI application running inside the Kubernetes cluster.
GitOps Self-Healing
Argo CD is configured with automated synchronization, pruning, and self-healing.
When the Kubernetes state is manually changed, Argo CD detects the difference between the live cluster and the desired state stored in Git and automatically reconciles the resource.
For example, scaling the application deployment manually:
kubectl scale deployment infrastructure-health-api --replicas=1
causes Argo CD to reconcile the deployment back to the desired replica count of 2.
This demonstrates GitOps-based self-healing and declarative Kubernetes management.
Validation
The project has been validated through multiple layers:
Automated API tests with Pytest
Docker image build through GitHub Actions
Docker image publishing to GHCR
Kubernetes deployment on kind
Readiness and liveness health checks
Helm chart validation with helm lint
Argo CD synchronization
Argo CD GitOps self-healing
Prometheus application metrics collection
Prometheus target monitoring
Grafana dashboard visualization
Grafana alerting
Nginx reverse proxy routing
Terraform infrastructure provisioning
The application was also verified with two running API replicas and Kubernetes health checks.
Project Goals
The project was developed as a practical demonstration of Cloud and DevOps engineering skills, with emphasis on:
Containerization
Kubernetes
GitOps
Infrastructure as Code
CI/CD automation
Monitoring and observability
Application reliability
Declarative infrastructure management
Automated health monitoring
Infrastructure troubleshooting
Future Improvements
Possible future improvements include:
Kubernetes Horizontal Pod Autoscaling
Ingress configuration
Secret management
Automated image version updates
Additional Prometheus alerts
Centralized log aggregation
Deployment to a managed cloud Kubernetes service
Automated deployment promotion between environments
These items represent potential extensions of the current platform and are not presented as currently implemented features.
Conclusion
This project demonstrates an end-to-end Cloud and DevOps workflow, from application development and automated testing to containerization, Kubernetes deployment, GitOps reconciliation, Infrastructure as Code, monitoring, and alerting.
The implementation focuses on practical automation, reliability, observability, and reproducible infrastructure rather than application complexity.
