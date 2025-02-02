#!/usr/bin/env bash

# Return SHA of image referenced by $1
# echo "$(grep $1 $SCRIPT_DIR/docker_image_aliases.txt | awk '{print $2}')"
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

DOCKER_RESULT=$(docker build --pull "${SCRIPT_DIR}/$1" 2>docker-image-alias-resolve-error.txt)
RESULT_IMAGE_ID=$(awk '/Successfully built/{print $3}' <<< "${DOCKER_RESULT}")

# Get the nexus repo tag via the meta.yml file. You're asking why not via docker image inspect?
# It seems that we don't always get the nexus repo tag via the field "RepoTags", so we go this way...
REPO_TAG=$(grep "tag:" "${SCRIPT_DIR}/$1/meta.yml" | awk '{ print $2}')

# We need to pull also the tag, otherwise Nexus may delete those images
docker pull -q "${REPO_TAG}" > /dev/null

if [ -n "$RESULT_IMAGE_ID" ] ; then
    rm docker-image-alias-resolve-error.txt
    echo $RESULT_IMAGE_ID
else
    echo "Could not resolve $1, error was:" 1>&2
    cat docker-image-alias-resolve-error.txt 1>&2
    echo "Make sure you're correctly logged into the registry and the image exists" 1>&2
    echo "INVALID_IMAGE_ID"
fi

