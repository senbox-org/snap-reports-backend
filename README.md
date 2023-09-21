# SNAP Reports Backend

Simple profile and statistics back-end.

## K8S deplyment

Pre-requisite:

Before starting the deployment, ingress controller should be updated with:

```yaml
containers:
- args:
  - /nginx-ingress-controller
  - --tcp-services-configmap=$(POD_NAMESPACE)/tcp-services
```

And create the relative configmap:

```yaml
apiVersion: v1
data:
  "3306": snap-report/mysql-service:3306
kind: ConfigMap
metadata:
  name: tcp-services
  namespace: nginx
```

1. Create the namespace `kubectl create namespace snap-report`
2. Create the secret based on `manifests/external-secret` and usage of *ExternalSecret* is optional.
3. Create the configmap `kubectl create configmap app-configs --from-env-file=assets/config -n snap-report`
4. Create other resources:

```sh
kubectl apply -f manifests/mysql-configmap.yaml -n snap-report
kubectl apply -f manifests/mysql-pvc.yaml -n snap-report
kubectl apply -f manifests/mysql-service.yaml -n snap-report
kubectl apply -f manifests/mysql-deployment.yaml -n snap-report
kubectl apply -f manifests/mysql-ingress.yaml -n snap-report
kubectl apply -f manifests/service.yaml -n snap-report
kubectl apply -f manifests/app-deployment.yaml -n snap-report
```
