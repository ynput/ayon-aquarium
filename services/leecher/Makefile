include ../.env

SERVICE := leecher
AYON_ADDON_VERSION=$(shell python -c "import os;import sys;content={};f=open('$(CURDIR)/../../version.py');exec(f.read(),content);f.close();print(content['__version__'])")
BASE_NAME := ayon-aquarium-$(SERVICE)
IMAGE := ghcr.io/fatfish-lab/$(BASE_NAME):$(AYON_ADDON_VERSION)
BASH_CONTAINER_NAME := $(BASE_NAME)-bash-$(AYON_ADDON_VERSION)
AYON_ADDON_NAME := aquarium
DEV_BUNDLE_NAME := dev02
build:
	cp -r ../common/ ./aquarium_common
	docker build -t $(IMAGE) .

clean:
	docker rmi $(IMAGE)

dist: build
	docker push $(IMAGE)

dev:
	cp -r ../common/ ./aquarium_common
	docker run --rm -ti \
		--hostname aquarium-${SERVICE} \
		--env AYON_API_KEY=${AYON_API_KEY} \
		--env AYON_SERVER_URL=${AYON_SERVER_URL} \
		--env AYON_ADDON_NAME=${AYON_ADDON_NAME} \
		--env AYON_ADDON_VERSION=$(AYON_ADDON_VERSION)+git \
		--env AYON_DEFAULT_SETTINGS_VARIANT=${DEV_BUNDLE_NAME} \
		-v ./${SERVICE}:/service/${SERVICE} \
		$(IMAGE) python -m $(SERVICE)

bash:
	docker run --name $(BASH_CONTAINER_NAME) --rm -it --entrypoint /bin/bash $(IMAGE)
