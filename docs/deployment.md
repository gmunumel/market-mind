# Deployment steps

## Using Own Server with Kubernetes (k3s)

### Build images

```
docker build --no-cache -t gabrielmunumel/market-mind-backend:latest -f backend/Dockerfile ./backend
docker build --no-cache -t gabrielmunumel/market-mind-frontend:latest -f frontend/Dockerfile ./frontend
```

### Push Images to Docker Hub

```
docker login -u gabrielmunumel
docker push gabrielmunumel/market-mind-backend:latest
docker push gabrielmunumel/market-mind-frontend:latest
```

### Create a namespace in Kubernetes

```
kubectl create namespace market-mind
```

### Generate secrets

```
kubectl delete secret market-mind-secrets -n market-mind

kubectl -n market-mind create secret generic market-mind-secrets \
  --from-literal=OPENAI_API_KEY="<YOUR_OPENAI_KEY>" \
  --from-literal=DATABASE_URL="postgresql+psycopg://market_mind:<PG_PASSWORD>@<PG_HOST>:5432/market_mind" \
  --from-literal=CHROMA_URL="http://<chroma-service-host>:8000" \
  --from-literal=LANGFUSE_PUBLIC_KEY="<YOUR_LANGFUSE_PUBLIC>" \
  --from-literal=LANGFUSE_SECRET_KEY="<YOUR_LANGFUSE_SECRET>"

kubectl delete secret market-mind-backend-market-mind-backend-postgres -n market-mind

kubectl create secret generic market-mind-backend-market-mind-backend-postgres -n market-mind \
  --from-literal=POSTGRES_DB=market_mind \
  --from-literal=POSTGRES_USER=market_mind \
  --from-literal=POSTGRES_PASSWORD=market_mind
```

### Install backend/frontend

```
helm upgrade --install market-mind-backend ./charts/backend -n market-mind \
  --set image.repository=gabrielmunumel/market-mind-backend \
  --set image.tag=latest \
  --set existingSecretName=market-mind-secrets

or

helm upgrade --install market-mind-backend ./charts/backend -n market-mind

helm upgrade --install market-mind-frontend ./charts/frontend -n market-mind
```

Force Kubernetes to re-pull the image:

```
kubectl rollout restart deploy/market-mind-backend-market-mind-backend -n market-mind

kubectl rollout restart deploy/market-mind-frontend-market-mind-frontend -n market-mind
```

Watch the rollout:

```
kubectl rollout status deploy/market-mind-backend-market-mind-backend -n market-mind

kubectl rollout status deploy/market-mind-frontend-market-mind-frontend -n market-mind
```

### All together

```
docker build -t gabrielmunumel/market-mind-backend:latest -f backend/Dockerfile ./backend
docker push gabrielmunumel/market-mind-backend:latest
helm upgrade --install market-mind-backend ./charts/backend \
  -n market-mind \
  --set image.repository=gabrielmunumel/market-mind-backend \
  --set image.tag=latest \
  --set image.pullPolicy=Always
kubectl rollout restart deployment/market-mind-backend-market-mind-backend -n market-mind

docker build -t gabrielmunumel/market-mind-frontend:latest -f frontend/Dockerfile ./frontend
docker push gabrielmunumel/market-mind-frontend:latest
helm upgrade --install market-mind-frontend ./charts/frontend \
  -n market-mind \
  --set image.repository=gabrielmunumel/market-mind-frontend \
  --set image.tag=latest \
  --set image.pullPolicy=Always
kubectl rollout restart deployment/market-mind-frontend-market-mind-frontend -n market-mind
```

## Monitoring

1. Check pods are running

   ```
   kubectl get pods -n market-mind
   ```

2. Verify service is running

   ```
   kubectl get svc -n
   ```

## Troubleshooting

List the ingress:

```
kubectl get ingress -n market-mind
```

Get ingress full detail:

```
kubectl describe ingress market-mind-backend -n market-mind
```

Make sure Kubernetes always pull latest:

```
helm upgrade market-mind-backend ./charts/backend -n market-mind \
  --set image.pullPolicy=Always

helm upgrade market-mind-frontend ./charts/frontend -n market-mind \
  --set image.pullPolicy=Always
```

Delete a ingress

```
kubectl delete ingress market-mind-ingress -n market-mind
```

If need to set the postgres password manually:

```
kubectl exec -it market-mind-backend-market-mind-backend-postgres-548dd55698g75n -n market-mind -- bash

psql -U market_mind

ALTER USER market_mind WITH PASSWORD 'market_mind';
\q

exit

kubectl delete secret market-mind-backend-market-mind-backend-postgres -n market-mind

kubectl create secret generic market-mind-backend-market-mind-backend-postgres -n market-mind \
  --from-literal=POSTGRES_DB=market_mind \
  --from-literal=POSTGRES_USER=market_mind \
  --from-literal=POSTGRES_PASSWORD=market_mind

kubectl get pods -n market-mind
```

Get postgres password:

```
kubectl get secret market-mind-backend-market-mind-backend-postgres \
  -n market-mind -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo

kubectl exec -it <backend-pod-name> -n market-mind -- env | grep POSTGRES
```
