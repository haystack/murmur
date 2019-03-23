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
	docker-compose down -v

# reset the database
.PHONY: reset-db
reset-db:
	docker-compose run web scripts/new_database_unsafe.sh

# attach a shell to the running docker image
.PHONY: shell
shell:
	docker exec -it youps_web /bin/sh -c "[ -e /bin/bash ] && /bin/bash || /bin/sh" || echo "\e[33mmake sure you already ran make start\e[0m"

# get a manage.py shell for running django things
.PHONY: django-shell
django-shell:
	docker exec -it youps_web python manage.py shell

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