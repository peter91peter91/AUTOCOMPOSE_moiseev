#тест выводит все айди сервисов  и все имена контейнеров
#тестируем удаление портейнеров всех
import docker
import argparse
import sys

c = docker.from_env()
#services_id_list = c.services.list()  # список всех айди сервисов
#print(services_id_list)
##################################################


def list_container_names():
    return [container.name for container in c.containers.list(all=True)]

parser = argparse.ArgumentParser(
    description="Generate docker-compose yaml definition from running container.",
)

parser.add_argument(
    "cnames",
    nargs="*",
    type=str,
    help="The name of the container to process.",
)

args = parser.parse_args()
print(args.cnames)
args.cnames.extend(list_container_names())
print(args.cnames)
i=0
for cname in args.cnames:
    if cname.find("portainer"):
        cid = [x.short_id for x in c.containers.list(all=True) if cname == x.name or x.short_id in cname][0]
        print("---------------------------------------")
        print("вывод c.services.get(cid).name  "+ c.containers.get(cid).name)
        print("первые 9 символов = " + cname[:9])
        print("вывод cid  " + cid)
        i=i+1
print("кол-во сервисов ,не явл. портейнером "+str(i))