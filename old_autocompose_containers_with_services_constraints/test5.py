#сделать postgres-smev

container_name = "rpn-backend-develop_rpn-backend-develop_postgres-smev.1.urxti7x7icib3bhtvsfbj56jm"


resized_container_name = container_name.partition('.')[0] # отрезаем имя после точки и точку
index = resized_container_name.rfind("_") #Найти индекс последнего вхождения символа "_" в строку
short_container_name = resized_container_name[index+1:]    #взять символы после того индекса и до конца

print(container_name)
print(short_container_name)

