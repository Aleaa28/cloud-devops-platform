# cloud-devops-platform

A small FastAPI service that I used as a vehicle to build a complete DevOps workflow from scratch: tests and image builds in CI, deployment with Helm and Argo CD on a local Kubernetes cluster, a bit of Terraform, and monitoring with Prometheus and Grafana.

The app is intentionally trivial. The interesting part is everything around it.

Everything runs locally on a [kind](https://kind.sigs.k8s.io/) cluster. Nothing here is deployed to a cloud provider.

## The app

| Endpoint      | What it returns                                   |
|---------------|---------------------------------------------------|
| `/`           | App name and version                              |
| `/health`     | `{"status": "healthy"}`, used by the k8s probes   |
| `/api/system` | Hostname of the pod that answered, plus a status  |
| `/metrics`    | Prometheus metrics (via `prometheus-fastapi-instrumentator`) |

`/api/system` returns the pod hostname on purpose, so you can see requests being spread across the two replicas.

## How it fits together

```
git push to main
   └─> GitHub Actions: pytest -> docker build -> push to GHCR (tags: latest + commit SHA)

Git repo (helm/ and k8s/nginx/)
   └─> Argo CD (auto-sync, prune, self-heal)
          └─> kind cluster
                ├─ infrastructure-health-api  (2 replicas, Helm chart)
                ├─ nginx-reverse-proxy        (plain manifests)
                └─ Prometheus + Grafana       (kube-prometheus-stack)
```

- **CI** (`.github/workflows/ci.yml`): installs dependencies, runs the tests, builds the image, and on pushes to `main` publishes it to GitHub Container Registry.
- **Helm chart** (`helm/infrastructure-health-api`): Deployment (2 replicas, readiness/liveness probes on `/health`, CPU and memory requests/limits), Service, ServiceMonitor, PrometheusRule and a Grafana dashboard ConfigMap.
- **Argo CD** (`argocd/`): two Applications, one for the Helm chart and one for the nginx manifests in `k8s/nginx`. Both have automated sync, pruning and self-heal enabled.
- **Nginx** (`nginx/`, `k8s/nginx/`): a reverse proxy in front of the API service.
- **Terraform** (`terraform/`): uses the Kubernetes provider to create a `platform` namespace. It is a small example, not a full infrastructure setup.

## Monitoring

Prometheus scrapes `/metrics` through the ServiceMonitor in the chart. The chart also ships:

- **A Grafana dashboard** (`helm/.../dashboards/infrastructure-health.json`) with four panels: request rate, error rate (4xx/5xx), p95 latency, and ready replicas. It is loaded through a ConfigMap labelled `grafana_dashboard: "1"`, which the Grafana sidecar picks up.
- **A Prometheus alert rule** (`templates/prometheusrule.yaml`): `InfrastructureHealthAPILowAvailability` fires when fewer than 2 replicas have been ready for 2 minutes. It uses the `kube_deployment_status_replicas_ready` metric from kube-state-metrics.

No notification receiver (email, Slack) is configured, so the alert only shows up in Prometheus/Alertmanager.

<!--
Add screenshots here once you have them, for example:
![Argo CD apps synced and healthy](docs/argocd.png)
![Grafana dashboard](docs/grafana.png)
-->

## Repository layout

```
app/                        FastAPI application
tests/                      Pytest tests for the endpoints
Dockerfile                  API image (python:3.11-slim)
nginx/                      nginx.conf and Dockerfile for the reverse proxy
helm/infrastructure-health-api/   Helm chart (see above)
k8s/nginx/                  Nginx Deployment and Service, deployed by Argo CD
k8s/deployment.yaml, service.yaml   My first plain-manifest version of the API,
                            before I moved to Helm. Not deployed any more.
argocd/                     Argo CD Application definitions
terraform/                  Namespace via the Kubernetes provider
.github/workflows/ci.yml    CI pipeline
```

## Running it locally

You need Docker, kubectl, kind, Helm, Terraform and Python 3.11+.

**Tests**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
python -m pytest
```

**Cluster and namespace**

```bash
kind create cluster --name cloud-devops
cd terraform && terraform init && terraform apply && cd ..
```

**Argo CD**

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Prometheus and Grafana**

The release name matters: the ServiceMonitor and PrometheusRule carry the label `release: monitoring`, so the stack must be installed as `monitoring`.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

**Nginx image**

The nginx image is built locally and loaded into kind (the manifest uses `imagePullPolicy: Never`):

```bash
docker build -t cloud-devops-nginx:latest ./nginx
kind load docker-image cloud-devops-nginx:latest --name cloud-devops
```

**Deploy the apps through Argo CD**

```bash
kubectl apply -f argocd/application.yaml -f argocd/nginx-application.yaml
kubectl get applications -n argocd     # wait for Synced / Healthy
```

**Try it**

```bash
kubectl port-forward service/nginx-reverse-proxy 8081:80
curl localhost:8081/api/system          # the hostname is the pod that answered
```

Grafana:

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

**Self-healing demo**

```bash
kubectl scale deployment infrastructure-health-api --replicas=1
kubectl get pods -w
```

Argo CD notices the drift from what is in Git and scales it back to 2.

## Known limitations

- **The image tag is bumped by hand.** CI publishes images tagged with the commit SHA, but `image.tag` in `values.yaml` is pinned manually. I originally used `latest` and it did not work with GitOps (with `IfNotPresent` the cluster never pulled the new image), which is why the tag is pinned. Automating this (CI updating the tag, or Argo CD Image Updater) is the next step.
- **The nginx image is not built in CI.** It only exists on my machine and in the kind cluster, so a fresh clone needs the manual build step above.
- **Terraform only manages a namespace,** with local state. A real setup would use a remote backend and manage more than this.
- **Argo CD, Prometheus and Grafana are installed manually,** not from this repo.
- **Local only.** Moving to a managed cluster (AKS, EKS, GKE) would also need an Ingress, proper secret handling and probably an HPA.
