.PHONY: update-dev
update-dev:
	ssh -t ubuntu@youps-dev.csail.mit.edu " \
	cd /home/ubuntu/production/mailx; \
	git pull; \
	sudo service apache2 restart; \
	sudo lamson restart || sudo lamson start`; \
	celery multi restart worker1 -A http_handler --pidfile=logs/worker1.pid --logfile=logs/worker1.log; \
	" 

