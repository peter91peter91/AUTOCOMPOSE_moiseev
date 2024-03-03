
import docker
c = docker.from_env()
services_id_list = c.services.list()  # список всех айди сервисов
# удаляем в списке весь мусор кроме самих айдишников <Service: 0lt5gop7c9x9>

print("вывод в цикле services_id_list")
print(services_id_list[1])
print(services_id_list[2])
print(services_id_list[3])