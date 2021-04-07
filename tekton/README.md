# Tekton Resources

Create service accounts and roles:

```sh
kubectl create -f rbac.yaml -n tekton-ci
```

Create the event listener, an ingress and a trigger:

```sh
kubectl create -f eventlistener.yaml
kubectl create -f trigger.yaml
```

Create a secret with the GitHub App key:

```sh
kubectl create secret generic github-app-key --from-file=key=<key file>
```