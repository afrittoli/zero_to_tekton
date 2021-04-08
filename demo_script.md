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

### The Tekton Hub

- Via web: [Tekton Hub](https://hub.tekton.dev)
- Via CLI:
  - `tkn hub`: online help
  - `tkn hub search git`: search tasks related to git
  - `tkn hub install task git-clone`: install a specific task

### Tasks and TaskRuns

- Details: `tkn task describe git-clone`
- Run: `tkn task start git-clone -p url=https://github.com/afrittoli/zero_to_tekton -p revision=main`
- Logs: `tkn tr logs`
- Run Details: `tkn tr describe git-clone-run-<xyz>`

Notice the results in the `TaskRun`.

One can also use `kubectl` directly, the YAML can be verbose, but it does provide a few more insights, like annotations and events:

```sh
kubectl describe tr/git-clone-run-<xyz>
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
  - image: busybox
    name: hello
    resources: {}
    script: |
      echo "Hello, everyone"
      echo "======"
      ls $(workspaces.output.path)
```

### Pipelines, PipelineRuns, Workspaces, Results

Let's build something more interesting:

```sh
tkn hub search --tags image-build
tkn hub install task kaniko
tkn task describe kaniko
```

We build a simple pipeline:

```yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: clone-build
spec:
  workspaces:
    - name: source
  results:
    - name: git-sha
      description: the git sha that has been built
      value: $(tasks.clone.results.commit)
    - name: image-sha
      description: the sha of the target container image
      value: $(tasks.build.results.IMAGE-DIGEST)
  tasks:
    - name: clone
      taskRef:
        name: git-clone
      params:
        - name: url
          value: https://github.com/afrittoli/zero_to_tekton
        - name: revision
          value: main
      workspaces:
        - name: output
          workspace: source
    - name: build
      runAfter: ['clone']
      taskRef:
        name: kaniko
      params:
        - name: IMAGE
          value: uk.icr.io/tekton/zero2tekton:$(tasks.clone.results.commit)
        - name: CONTEXT
          value: image
      workspaces:
        - name: source
          workspace: source
        - name: dockerconfig
          workspace: dockerconfig
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
tkn pipeline start clone-build -s build-bot --workspace name=source,volumeClaimTemplateFile=workspace-template.yaml
```

Check results using `tkn`:

```sh
tkn pr describe clone-build-run-<xyz>
```

The pipeline is made of two tasks. Each task is executed in a dedicated
pod. They share data through the PVC:

```sh
kubectl get pod -l tekton.dev/pipelineRun=clone-build-run-<xyz>
```

Try and browse the `PipelineRun` via the [dashboard](http://localhost:9197/#/namespaces/default/pipelineruns/).

### Deploy the built image

Check the sha:

```sh
tkn pr describe <or-name>
```

Run in docker:

```sh
docker run -it --rm -d -p 8080:80 --name web uk.icr.io/tekton/zero2tekton@sha256:<from results>
```

