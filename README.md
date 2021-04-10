# From Zero to CD with Tekton

Talk slides are available in [pdf](zero_to_tekton.pdf).
A [script](demo_script.md) is available for the demo parts.

## Rebuilding the slides

Install xelatex with most of the plugins via your distro.
Either xelatex or lualatex are required for the fontspec package to work.

Install the IBMPlex font from https://github.com/IBM/plex.

To build the example just run:

```shell
% xelatex zero_to_tekton.tex
```

the output will be [zero\_to\_tekton.pdf](zero_to_tekton.pdf).
