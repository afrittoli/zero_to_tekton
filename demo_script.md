# Demo Script

Some environment variables to access clusters:

```sh
KIND_CONTEXT=kind-tekton
IKS_CONTEXT=tekton-cnd/c1ipfjgl0c79a0bo9peg
```

## Install

### Local setup on a kind cluster

- Deploy a registry
- Deploy a kind cluster with 3 nodes
- Deploy latest pipeline, triggers and dashboard

```sh
# Source: https://github.com/tektoncd/plumbing/blob/main/hack/tekton_in_kind.sh
curl https://raw.githubusercontent.com/tektoncd/plumbing/main/hack/tekton_in_kind.sh | bash -s
```

### Setup in IBM Cloud with the Tekton Operator

```sh
# Source https://github.com/tektoncd/operator

# Install the operator
kubectl apply -f https://storage.googleapis.com/tekton-releases/operator/latest/release.yaml

# Check that all pods are ready in the tekton-operator ns
kubectl wait --for=condition=ready pod --all -n tekton-operator

# Install Tekton
kubectl apply -f https://raw.githubusercontent.com/tektoncd/operator/main/config/crs/kubernetes/config/all/operator_v1alpha1_config_cr.yaml
```

### Check versions

With the CLI:

```sh
tkn version
```

With the Dashboard:

```sh
kubectl --context $KIND_CONTEXT port-forward service/tekton-dashboard -n tekton-pipelines 9197:9097 &
kubectl --context $IKS_CONTEXT port-forward service/tekton-dashboard -n tekton-pipelines 9297:9097 &
```