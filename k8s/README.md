# Kubernetes manifests (EKS / future CD)

Baseline manifests for deploying the **web** app to AWS EKS. PostgreSQL is expected **outside** the cluster (e.g. RDS); only the Django/gunicorn workload runs here.

## Files

| File | Purpose |
| ---- | ------- |
| `deployment.yaml` | Pods, probes (`/health/live`, `/health/ready`), env from Secret |
| `service.yaml` | ClusterIP `:80` → container `:8000` |
| `ingress.yaml` | ALB Ingress (AWS Load Balancer Controller) |
| `secret.example.yaml` | Env var template — copy and fill for each environment |

## Quick apply (manual smoke test)

```bash
# 1. Build & push image (example)
docker build -t backend-devops-interview:local .
# tag + push to ECR, then set image in deployment.yaml

# 2. Secret (never commit real values)
cp secret.example.yaml secret.yaml
# edit secret.yaml, then:
kubectl apply -f secret.yaml

# 3. App + networking
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Future CD (GitHub Actions → EKS)

Typical split per environment (`staging` / `production`):

1. **CI** (existing): test + lint + build image.
2. **CD workflow** (later): push image to ECR → `kubectl set image` or `kustomize`/`helm` with env-specific overlays → apply Ingress host + Secret from GitHub Environment secrets.

Placeholder replacements done in CD:

- `REPLACE_ME_ECR_IMAGE:tag` in `deployment.yaml`
- `api.REPLACE_ME.example.com` and ACM ARN in `ingress.yaml`
- Secret keys from GitHub Environment / AWS Secrets Manager

## EKS prerequisites

- EKS cluster + `kubectl` access
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) installed (`ingressClassName: alb`)
- RDS (or other) Postgres reachable from the cluster security groups
- `ALLOWED_HOSTS` includes the Ingress hostname

## Notes

- Run **migrations** outside the Deployment lifecycle (CI job, init Job, or one-off `kubectl run`) — not included here yet.
- Scale `replicas` and resource limits per environment in CD overlays when you add `k8s/overlays/staging` and `k8s/overlays/production`.
