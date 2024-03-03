Привет!  Прога моя сейчас деплоит DEV стек без ручных вмешателств, все сервисы в UP.
Старался сильно структуру исходного кода не менять- вызываю самописные методы там,где необходимо.

Из жёстких костылей:  
1) сети в блоки объявления: проставляю  параметр сети "external": False, в сетях со словом internal  (ориг код проставляет True и не деплоится)
2) сети в блоки объявления: фильтруются на наличие слова internal,
3) директивы сетей в каждом модуле фильтруются на наличие слова internal и выводятся ,если только  в имени сети таковое имеется

Не костыли:
4) Не выводим сервисы по нахождению в их имени слова Portainer
5) не выводим "ipc" , т.к. swarm при деплое пишет, что не поддерживает
6) не выводим   "container_name" 

7) меняем имя сервисов на короткие  ,напр.  postgres-smev  -(иначе ошибка имени при деплое)
8) программа выводит данные по контейнерам в .yml файл
9) программа добавляет в блоки сервисов директиву  constraints, обращаясь в SERVICES(где происходит обработка алгоритмом поиска  сервиса соответствующего каждому контейнеру)









# docker-autocompose
Generates a docker-compose yaml definition from a docker container.

Required Modules:
* [pyaml](https://pypi.python.org/project/pyaml/)
* [docker](https://pypi.python.org/project/docker)
* [six](https://pypi.python.org/project/six)

Example Usage:

    sudo python autocompose.py <container-name-or-id>


Generate a compose file for multiple containers together:

    sudo python autocompose.py apache-test mysql-test


The script defaults to outputting to compose file version 3, but use "-v 1" to output to version 1:

    sudo python autocompose.py -v 1 apache-test


Outputs a docker-compose compatible yaml structure:

[docker-compose reference](https://docs.docker.com/compose/)

[docker-compose yaml file specification](https://docs.docker.com/compose/compose-file/)

While experimenting with various docker containers from the Hub, I realized that I'd started several containers with complex options for volumes, ports, environment variables, etc. and there was no way I could remember all those commands without referencing the Hub page for each image if I needed to delete and re-create the container (for updates, or if something broke).

With this tool, I can easily generate docker-compose files for managing the containers that I've set up manually.

## Docker Usage

You can use this tool from a docker container by either cloning this repo and building the image or using the [automatically generated image on GitHub](https://github.com/Red5d/docker-autocompose/pkgs/container/docker-autocompose)

Pull the image from GitHub (supports both x86 and ARM)

    docker pull ghcr.io/red5d/docker-autocompose:latest

Use the new image to generate a docker-compose file from a running container or a list of space-separated container names or ids:

    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/red5d/docker-autocompose <container-name-or-id> <additional-names-or-ids>...

To print out all containers in a docker-compose format:

    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/red5d/docker-autocompose $(docker ps -aq)
    
## Contributing

When making changes, please validate the output from the script by writing it to a file (docker-compose.yml or docker-compose.yaml) and running "docker-compose config" in the same folder with it to ensure that the resulting compose file will be accepted by docker-compose.
