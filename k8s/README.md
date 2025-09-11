# Kubernetes Ollama Deployment for AI CV Parsing

This directory contains Kubernetes configurations to deploy Ollama with persistent storage and connect it to the AI CV parsing Python application.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Python App    │───▶│  Ollama Service  │───▶│ Ollama Pod      │
│   (Job/Pod)     │    │  (ClusterIP)     │    │ + Models        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Persistent      │
                                                │ Volume (20Gi)   │
                                                └─────────────────┘
```

## Files

- `ollama-namespace.yaml` - Creates dedicated namespace for isolation
- `ollama-pvc.yaml` - Persistent storage for model data (20Gi)
- `ollama-deployment.yaml` - Ollama server deployment with health checks
- `ollama-service.yaml` - Internal service for pod communication
- `ollama-configmap.yaml` - Configuration for models and settings
- `app-job.yaml` - Job to run the Python CV parsing application

## Quick Start

### 1. Deploy Ollama Infrastructure

```bash
# Apply all Kubernetes configurations
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n ollama
```

### 2. Download Models

```bash
# Get the Ollama pod name
OLLAMA_POD=$(kubectl get pods -n ollama -l app=ollama -o jsonpath='{.items[0].metadata.name}')

# Download the deepseek-r1:7b model
kubectl exec -it $OLLAMA_POD -n ollama -- ollama pull deepseek-r1:7b

# Verify model is available
kubectl exec -it $OLLAMA_POD -n ollama -- ollama list
```

### 3. Build and Deploy Application

```bash
# Build Docker image
docker build -t ai-cv-parsing:latest .

# Load image into minikube (if using minikube)
minikube image load ai-cv-parsing:latest

# Deploy the application job
kubectl apply -f k8s/app-job.yaml

# Check job status
kubectl get jobs -n ollama
kubectl logs job/ai-cv-parsing-job -n ollama
```

## Configuration

### Environment Variables

The Python application automatically detects the Kubernetes environment through:

- `OLLAMA_BASE_URL`: Set to `http://ollama-service:11434/v1` in Kubernetes
- `PYTHONPATH`: Set to `/app/src` for proper module loading

### Resource Limits

- **Ollama Pod**: 2-4Gi memory, 0.5-2 CPU cores
- **App Job**: 512Mi-1Gi memory, 0.25-0.5 CPU cores
- **Storage**: 20Gi persistent volume for model storage

### Health Checks

Ollama deployment includes:
- **Liveness Probe**: HTTP check on port 11434 every 10s
- **Readiness Probe**: HTTP check on port 11434 every 5s

## Troubleshooting

### Check Ollama Status
```bash
kubectl get pods -n ollama
kubectl describe pod <ollama-pod-name> -n ollama
kubectl logs <ollama-pod-name> -n ollama
```

### Check Application Logs
```bash
kubectl logs job/ai-cv-parsing-job -n ollama
```

### Test Ollama Connectivity
```bash
# Port forward to test locally
kubectl port-forward svc/ollama-service 11434:11434 -n ollama

# Test in another terminal
curl http://localhost:11434/api/version
```

### Clean Up
```bash
# Delete all resources
kubectl delete namespace ollama
```

## Scaling Considerations

- **Horizontal**: Increase Ollama replicas for multiple concurrent requests
- **Vertical**: Adjust CPU/memory limits based on model requirements
- **Storage**: Monitor PV usage and expand if needed
- **Models**: Use initContainers to pre-download models

## Security Notes

- All resources are isolated in the `ollama` namespace
- No external ingress configured (ClusterIP only)
- Consider adding NetworkPolicies for production
- Use secrets for sensitive configuration data