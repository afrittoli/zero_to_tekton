# Demo Script

Some environment variables to access clusters:

```sh
KIND_CONTEXT=kind-tekton
IKS_CONTEXT=tekton-cnd/c1ipfjgl0c79a0bo9peg
```

This is specific to my laptop:

```sh
export PS1=$PSTEKTONIBM  # Nice prompts
ibm_login_eu  # login to IBM cloud
iks cluster config --cluster tekton-cnd # Update the token in the context
```

## Install

### Local setup on a kind cluster

- Deploy a registry
- Deploy a kind cluster with 3 nodes
- Deploy latest pipeline, triggers and dashboard

```sh
# Source: https://github.com/tektoncd/plumbing/blob/main/hack/tekton_in_kind.sh
./tekton/tekton_in_kind.sh
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
kubectl --context $IKS_CONTEXT port-forward service/tekton-dashboard -n tekton-pipelines 9097 &
```

### Nightly builds

[Nightly builds](https://console.cloud.google.com/storage/browser/tekton-releases-nightly;tab=objects?forceOnBucketsSortingFiltering=false&project=tekton-nightly&prefix=&forceOnObjectsSortingFiltering=false) are available for several repositories, including operator:

```sh
kubectl apply -f https://storage.googleapis.com/tekton-releases-nightly/operator/latest/release.yaml
```

### Multi-arch builds

This is an [example multi-arch image](https://console.cloud.google.com/gcr/images/tekton-nightly/GLOBAL/github.com/tektoncd/pipeline/cmd/controller@sha256:d85d7bb446d407640a1ddf97014e94656098e8d08ce30c5e23e6005ea660730c/details?tab=info&project=tekton-nightly).

Currently we build:

- _amd64_ - Tests: CI (unit, e2e tests, on GKE)
- _s390x_ - Tests: Nightly (e2e, on Z cluster at IBM)
- _ppc64le_ - Tests: Nightly (e2e, on Power cluster at IBM)
- _arm64_ - Tests: none yet, looking for an arm64 provider

Work [has started](https://github.com/tektoncd/community/pull/383) for Windows support.

## Authoring

```sh
kubectl config use-context kind-tekton
```

### The Tekton Hub

- Via web: [Tekton Hub](https://hub.tekton.dev)
- Via CLI:
  - `tkn hub`: online help
  - `tkn hub search git`: search tasks related to git
  - `tkn hub install task git-clone`: install a specific task

### Tasks and TaskRuns

- Details: `tkn task describe git-clone`
- Run: `tkn task start git-clone -p url=https://github.com/afrittoli/zero_to_tekton -p revision=main --workspace name=output,emptyDir=""`
- Logs: `tkn tr logs -f`
- Run Details: `tkn tr describe git-clone-run-<xyz>`

Notice the results in the `TaskRun`.

One can also use `kubectl` directly, the YAML can be verbose, but it does provide a few more insights, like annotations and events:

```sh
kubectl describe taskrun/git-clone-run-<xyz>
```

Annotations are inherited from the catalog task too!
Events are k8s events, we'll see later that CloudEvents can be sent too.

Let's have a look at what happened behind the curtains:

```sh
kubectl get pods -l tekton.dev/taskRun=git-clone-run-<xyz>
kubectl describe pod <pod-name>
```

Notice the `EmptyDir` workspace.
Notice the `step-clone` container. Steps in Tekton tasks are containers, executed sequentially.

Edit the task to see what happens `kubectl edit task/git-clone`:

```yaml
  - image: docker.io/library/busybox@sha256:ae39a6f5c07297d7ab64dbd4f82c77c874cc6a94cea29fdec309d0992574b4f7
    name: hello
    resources: {}
    script: |
      echo "Hello, everyone"
      echo "======"
      ls $(workspaces.output.path)
```

Look at the steps via the dashboard.

### Pipelines, PipelineRuns, Workspaces, Results

Let's build something more interesting:

```sh
tkn hub search --tags image-build
tkn hub install task kaniko
tkn task describe kaniko
```

We build a simple pipeline:

```sh
kubectl create -f tekton/pipeline.yaml
```

To run the pipeline:

```sh
cat <<EOF > workspace-template.yaml
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
tkn pipeline start zero2cd --workspace name=source,volumeClaimTemplateFile=workspace-template.yaml --workspace name=dockerconfig,secret=regcred
```

Check results using `tkn`:

```sh
tkn pr describe zero2cd-run-<xyz>
```

The pipeline is made of two tasks. Each task is executed in a dedicated
pod. They share data through the PVC:

```sh
kubectl get pod -l tekton.dev/pipelineRun=zero2cd-run-<xyz>
```

Try and browse the `PipelineRun` via the [dashboard](http://localhost:9197/#/namespaces/default/pipelineruns/).

### Deploy and update the built image

Check the sha:

```sh
tkn pr describe zero2cd-run-<xyz>
```

Run in docker:

```sh
docker run -it --rm -d -p 8080:80 --name web uk.icr.io/tekton/zero2tekton@sha256:<from results>
open http://localhost:8080/
```

Add a deploy task to the pipeline:

```sh
kubectl replace -f tekton/pipeline2.yaml
kubectl create -f tekton/ingress.yaml
```

Re-run the pipeline:

```sh
tkn pipeline start zero2cd --workspace name=source,volumeClaimTemplateFile=workspace-template.yaml --workspace name=dockerconfig,secret=regcred
```

Check in the dashboard. Once finished:

```sh
open http://localhost/demo/
```

## Launching

Create trigger resources: event listener, trigger:

```sh
kubectl create -f tekton/eventlistener.yaml
kubectl create -f tekton/trigger.yaml
```

Enabled the OCI bundles feature in pipelines:

```sh
kubectl edit cm/feature-flags -n tekton-pipelines
```

Push our pipelines to a bundle:

```sh
tkn-dev bundle push uk.icr.io/tekton/zero2cd-pipeline:1.0 -f tekton/pipeline.yaml
tkn-dev bundle push uk.icr.io/tekton/zero2cd-pipeline:2.0 -f tekton/pipeline2.yaml
```

Run the smee client to receive events from the smee channel configured
in the GitHub App:

```sh
smee -u https://smee.io/uIq3Yv0K0PRZxqMB --target http://localhost/ci &
```

Make a change to the demo page.
Create a commit and push it. See the PR running in the dashboard.
Describe the PR via `tkn`

Notice the labels. We can use them to filter resources.

```sh
tkn pr list --label triggers.tekton.dev/trigger=github-push
```

Have a look at the trigger definition.
We use a CEL filter to filter based on headers and body.
One can build custom interceptors to add content or implement special filtering. When expression could be used to build and deploy only when changes were made to the container image.
