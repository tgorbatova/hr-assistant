.PHONY: up, down, docker, debug, restart
up:
	ansible-playbook playbook.yml --tags start

down:
	ansible-playbook playbook.yml --tags stop

docker:
	docker-compose -f ./ecosystem/docker-compose.yml logs -f

restart: down up

.PHONY: reload
reload:
	docker-compose -f ./ecosystem/docker-compose.yml up -d --no-deps --build nginx $(filter-out $@,$(MAKECMDGOALS))

%:
	@:

debug: down up docker