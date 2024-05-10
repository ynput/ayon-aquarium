AYON_ADDON_NAME=$(shell python -c "import os;import sys;content={};f=open('$(CURDIR)/../package.py');exec(f.read(),content);f.close();print(content['name'])")
AYON_ADDON_VERSION=$(shell python -c "import os;import sys;content={};f=open('$(CURDIR)/../package.py');exec(f.read(),content);f.close();print(content['version'])")
SERVICE = $(error Please specify the service to build with 'SERVICE', for example: 'make build SERVICE=leecher')
IMAGE := ynput/ayon-aquarium-$(SERVICE):$(AYON_ADDON_VERSION)


build:
	cp -r ./common/ ./$(SERVICE)/aquarium_common
	sed -i '/^\[tool.poetry\]/,/^\[/ s/^version = .*/version = "$(AYON_ADDON_VERSION)"/' $(SERVICE)/pyproject.toml
	docker build -t $(IMAGE) ./$(SERVICE)

clean:
	docker rmi $(IMAGE)

dev:
	cp -r ./common/ ./$(SERVICE)/aquarium_common

	docker run --rm -ti \
		-v ./$(SERVICE)/$(SERVICE):/service/$(SERVICE) \
		--hostname dev-aysvc-$(AYON_ADDON_NAME) \
		--env-file $(CURDIR)/.env \
		--env AYON_ADDON_NAME=${AYON_ADDON_NAME} \
		--env AYON_ADDON_VERSION=$(AYON_ADDON_VERSION) \
		--network=host \
		$(IMAGE) python -m $(SERVICE)

bash:
	docker run --name dev-aysvc-$(AYON_ADDON_NAME)-$(SERVICE) --rm -it --entrypoint /bin/bash $(IMAGE)
