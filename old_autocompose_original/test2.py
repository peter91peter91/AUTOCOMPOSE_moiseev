
import docker

c = docker.from_env()
cattrs = c.services.get("chd7uh460n0t").attrs

print("------------------------------")
print("вывод placement-constraints  spec и остальное в кавычках    cattrs.get(Spec, {}).get(TaskTemplate, {}).get(Placement, {}).get(Constraints, {})")  # !!! moiseev
print(cattrs.get("Spec", {}).get("TaskTemplate", {}).get("Placement", {}).get("Constraints", {}))
print("------------------------------")

