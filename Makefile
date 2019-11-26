.PHONY: default
default: build reset-db start

# build the docker image
.PHONY: build
build:
	docker-compose build

# start the docker image
.PHONY: start
start:
	docker-compose up --force-recreate --build -d

# stop the docker image
.PHONY: stop
stop:
	docker-compose down

# stop the docker image and remove database information
.PHONY: clean 
clean:
	docker-compose down -v

# reset the database
.PHONY: reset-db
reset-db:
	mkdir -p schema/migrations
	docker-compose run web scripts/new_database_unsafe.sh

# attach a shell to the running docker image
.PHONY: shell
shell:
	docker exec -it murmur_web /bin/sh -c "[ -e /bin/bash ] && /bin/bash || /bin/sh" || echo "\e[33mmake sure you already ran make start\e[0m"

.PHONY: solo-shell
solo-shell:
	docker-compose run web /bin/sh -c "[ -e /bin/bash ] && /bin/bash || /bin/sh"

# get a manage.py shell for running django things
.PHONY: django-shell
django-shell:
	docker exec -it murmur_web python manage.py shell && from schema.youps import *

# show logs for the running docker containers
.PHONY: logs
logs:
	docker-compose logs -f

# old script for updating code on the server after pushing
.PHONY: update-dev
update-dev:
	ssh -t ubuntu@youps-dev.csail.mit.edu " \
	cd /home/ubuntu/production/mailx; \
	git pull; \
	sudo lamson restart || sudo lamson start; \
	./youps_reboot.sh \
	" 