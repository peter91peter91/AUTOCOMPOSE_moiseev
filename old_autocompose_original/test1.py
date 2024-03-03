import docker
c = docker.from_env()
services_id_list = c.services.list()  # список всех айди сервисов

# удаляем в списке весь мусор кроме айдишников <Service: 0lt5gop7c9x9>
services_id_list2 = list(range(len(services_id_list)))
services_id_list2[1] = "<Service: 0lt5gop7c9x9>"


result1 = str(services_id_list2[1])[10:22]   # берем айди (с 10 по 22 символ элемента списка)
print(result1)
