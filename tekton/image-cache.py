#!/usr/bin/env python3

import json
import subprocess

# Run as a subprocess and return the decoded stdout
def run(*args):
    return subprocess.run(args, stdout=subprocess.PIPE).stdout.decode("utf-8")

# Get the list of nodes
docker_ps = run('docker','ps')
nodes = [x.split()[-1] for x in docker_ps.splitlines() if 'kindest/node' in x]

# Load the images from each node
images = []
for node in nodes:
    images_raw = run('docker', 'exec', node, 'crictl', 'images', '-o', 'json')
    images_json = json.loads(images_raw)
    for image in images_json['images']:
        images.extend(image['repoTags'])
        images.extend(image['repoDigests'])

images = set(images)
print("Caching {} images".format(len(images)))

# Load all images into the local docker daemon
with open('image-cache.txt', 'w') as imagecache:
    for image in images:
        print("Caching {}...".format(image))
        cache_output = run('docker', 'pull', image).splitlines()[-1]
        imagecache.write(cache_output + '\n')
        print(cache_output)