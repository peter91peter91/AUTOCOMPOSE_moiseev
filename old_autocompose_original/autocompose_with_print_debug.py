#! /usr/bin/env python3
import argparse
import datetime
import re
import sys

from collections import OrderedDict

import docker
import pyaml

IGNORE_VALUES = [None, "", [], "null", {}, "default", 0, ",", "no"]


def list_container_names():
    c = docker.from_env()  #
    return [container.name for container in c.containers.list(all=True)]


def list_network_names():
    c = docker.from_env()
    return [network.name for network in c.networks.list()]


def generate_network_info():
    networks = {}

    for network_name in list_network_names():
        connection = docker.from_env()
        network_attributes = connection.networks.get(network_name).attrs

        values = {
            "name": network_attributes.get("Name"),
            "scope": network_attributes.get("Scope", "local"),
            "driver": network_attributes.get("Driver", None),
            "enable_ipv6": network_attributes.get("EnableIPv6", False),
            "internal": network_attributes.get("Internal", False),
            "ipam": {
                "driver": network_attributes.get("IPAM", {}).get("Driver", "default"),
                "config": [
                    {key.lower(): value for key, value in config.items()}
                    for config in network_attributes.get("IPAM", {}).get("Config", [])
                ],
            },
        }

        networks[network_name] = {key: value for key, value in values.items()}

    return networks


def main():
    parser = argparse.ArgumentParser(
        description="Generate docker-compose yaml definition from running container.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Include all active containers",
    )
    parser.add_argument(
        "-v",
        "--version",
        type=int,
        default=3,
        help="Compose file version (1 or 3)",
    )
    parser.add_argument(
        "cnames",
        nargs="*",
        type=str,
        help="The name of the container to process.",
    )
    parser.add_argument(
        "-c",
        "--createvolumes",
        action="store_true",
        help="Create new volumes instead of reusing existing ones",
    )
    parser.add_argument(
        "-f",
        "--filter",
        type=str,
        help="Filter containers by regex",
    )
    args = parser.parse_args()

    container_names = args.cnames

    if args.all:
        container_names.extend(list_container_names())

    if args.filter:
        cfilter = re.compile(args.filter)
        container_names = [c for c in container_names if cfilter.search(c)]

    struct = {}
    networks = {}
    volumes = {}
    containers = {}

    for cname in container_names:  # здесь цикл заполнения yml-файла
        cfile, c_networks, c_volumes = generate(cname, createvolumes=args.createvolumes)

        struct.update(cfile)

        if not c_networks == None:
            networks.update(c_networks)
        if not c_volumes == None:
            volumes.update(c_volumes)

    # moving the networks = None statements outside of the for loop. Otherwise any container could reset it.
    if len(networks) == 0:
        networks = None
    if len(volumes) == 0:
        volumes = None

    if args.all:
        host_networks = generate_network_info()
        networks = host_networks

    render(struct, args, networks, volumes)


def render(struct, args, networks, volumes):
    # Render yaml file
    if args.version == 1:
        pyaml.p(OrderedDict(struct))
    else:
        ans = {"version": '3.6', "services": struct}

        if networks is not None:
            ans["networks"] = networks

        if volumes is not None:
            ans["volumes"] = volumes

        pyaml.p(OrderedDict(ans), string_val_style='"')


##################################################################
def placement_constraints_moiseev(container_name):  # лучше в будущем вызывать единожды
    print("---------- передали в мою функцию container_name")
    print(container_name)
    # (container_name здесь это c.containers.get(cid).name)
    # Взяли короткое имя. Ищем его далее в массиве docker service ls (c.services.list())
    short_container_name = container_name.partition('.')[0]  # отрезаем имя после точки и точку

    c = docker.from_env()
    services_id_list = c.services.list()  # список всех айди сервисов
    print("---------- выводим services_id_list")
    print(services_id_list)
    # удаляем в списке весь мусор кроме айдишников <Service: 0lt5gop7c9x9>

    i = 0
    list_range = range(len(services_id_list))
    services_name_list = list(list_range)
    services_id_list_filtered = list(list_range)
    for i in list_range:
        service_id = str(services_id_list[i])[10:22]  # берем айди (с 10 по 22 символ элемента списка)
        services_id_list_filtered[i] = service_id
        services_name_list[i] = c.services.get(service_id).name  # список всех имен этих сервисов
        i = i + 1
        services_id_and_name_list = [[services_id_list_filtered], [services_name_list]]
    ###выбираем айди, соответствующий нужному имени сервиса
    ###пока что метод в таком неоптимизированном виде для удобства отладки!!!
    # short_container_name = "rpn-backend-develop_cron"
    target_service_id = ""
    i = 0

    print("1)перед циклом")
    for i in list_range:
        print("2)вошли в цикл")
        print("3)short_container_name   " + short_container_name)
        print("services_name_list[i]   " + services_name_list[i])
        if short_container_name == services_name_list[i]:
            target_service_id = services_id_list_filtered[i]
            print("---------- выводим в теле цикла target_service_id")
            print(target_service_id)
            break
        i = i + 1
    print("---------- выводим вне цикла target_service_id")
    print(target_service_id)
    ########################################################################
    print(
        "---------- выводим двумерный список     services_id_and_name_list = [[services_id_list], [services_name_list]]---------- ")
    for i in range(len(services_id_and_name_list)):
        for j in range(len(services_id_and_name_list[i])):
            print(services_id_and_name_list[i][j], end=' ')
        print()
    ########################################################################
    cattrs = c.services.get(target_service_id).attrs
    placement_constraints = cattrs.get("Spec", {}).get("TaskTemplate", {}).get("Placement", {}).get("Constraints", {})
    print("------------------------------")
    print(
        "вывод placement-constraints  spec и остальное в кавычках    cattrs.get(Spec, {}).get(TaskTemplate, {}).get(Placement, {}).get(Constraints, {})")  # !!! moiseev
    print(placement_constraints)
    print("------------------------------")

    return placement_constraints


##################################################################


def generate(cname, createvolumes=False):
    c = docker.from_env()

    try:
        cid = [x.short_id for x in c.containers.list(all=True) if cname == x.name or x.short_id in cname][0]
    except IndexError:
        print("That container is not available.", file=sys.stderr)
        sys.exit(1)

    cattrs = c.containers.get(cid).attrs

    # ----------------------------------------------------------------------------------------
    #    print("------------------------------")
    #    print("------------------------------")
    #    print("вывод cattrs")  # !!! moiseev
    #    print(cattrs)
    #    print("------------------------------")
    #    print("вывод services")  # !!! moiseev
    #    print(c.containers.list())
    #    print("------------------------------")
    #    print("вывод services get(cid)")  # !!! moiseev
    #    print(c.containers.get(cid))
    #    print("------------------------------")
    #    print("вывод cname")  # !!! moiseev
    #    print(cname)
    #    print("------------------------------")
    #    print("вывод c.services.get(cid).name")  # !!! moiseev
    #    print(c.containers.get(cid).name)
    #    print("------------------------------")
    #    print("------------------------------")
    # ----------------------------------------------------------------------------------------
    # добавляем считку  поля placement constraints - node.role == manager
    print("------------------------------")
    print(
        "вывод placement-constraints  spec и остальное в кавычках    cattrs.get(Spec, {}).get(TaskTemplate, {}).get(Placement, {}).get(Constraints, {})")  # !!! moiseev
    print(cattrs.get("Spec", {}).get("TaskTemplate", {}).get("Placement", {}).get("Constraints", {}))
    print("------------------------------")
    ##################################################################
    ##################################################################
    ##################################################################

    # Build yaml dict structure

    cfile = {}
    cfile[cattrs.get("Name")[1:]] = {}
    ct = cfile[cattrs.get("Name")[1:]]

    default_networks = ["bridge", "host", "none"]

    ###moiseev
    container_name = c.containers.get(cid).name  ###moiseev
    ###moiseev

    values = {
        "cap_drop": cattrs.get("HostConfig", {}).get("CapDrop", None),
        "cgroup_parent": cattrs.get("HostConfig", {}).get("CgroupParent", None),
        "container_name": cattrs.get("Name")[1:],
        "devices": [],
        "dns": cattrs.get("HostConfig", {}).get("Dns", None),
        "dns_search": cattrs.get("HostConfig", {}).get("DnsSearch", None),
        "environment": cattrs.get("Config", {}).get("Env", None),
        "extra_hosts": cattrs.get("HostConfig", {}).get("ExtraHosts", None),
        "image": cattrs.get("Config", {}).get("Image", None),
        "labels": cattrs.get("Config", {}).get("Labels", {}),
        "links": cattrs.get("HostConfig", {}).get("Links"),
        # 'log_driver': cattrs.get('HostConfig']['LogConfig']['Type'],
        # 'log_opt': cattrs.get('HostConfig']['LogConfig']['Config'],
        "logging": {
            "driver": cattrs.get("HostConfig", {}).get("LogConfig", {}).get("Type", None),
            "options": cattrs.get("HostConfig", {}).get("LogConfig", {}).get("Config", None),
        },
        "networks": {
            x for x in cattrs.get("NetworkSettings", {}).get("Networks", {}).keys() if x not in default_networks
        },

        ###moiseev
        "deploy": {
            "placement": {
                "constraints": placement_constraints_moiseev(container_name)
            }
        },
        ###moiseev

        "security_opt": cattrs.get("HostConfig", {}).get("SecurityOpt"),
        "ulimits": cattrs.get("HostConfig", {}).get("Ulimits"),
        # the line below would not handle type bind
        #        'volumes': [f'{m["Name"]}:{m["Destination"]}' for m in cattrs.get('Mounts'] if m['Type'] == 'volume'],
        "mounts": cattrs.get("Mounts"),  # this could be moved outside of the dict. will only use it for generate
        "volume_driver": cattrs.get("HostConfig", {}).get("VolumeDriver", None),
        "volumes_from": cattrs.get("HostConfig", {}).get("VolumesFrom", None),
        "entrypoint": cattrs.get("Config", {}).get("Entrypoint", None),
        "user": cattrs.get("Config", {}).get("User", None),
        "working_dir": cattrs.get("Config", {}).get("WorkingDir", None),
        "domainname": cattrs.get("Config", {}).get("Domainname", None),
        "hostname": cattrs.get("Config", {}).get("Hostname", None),
        "ipc": cattrs.get("HostConfig", {}).get("IpcMode", None),
        "mac_address": cattrs.get("NetworkSettings", {}).get("MacAddress", None),
        "privileged": cattrs.get("HostConfig", {}).get("Privileged", None),
        "restart": cattrs.get("HostConfig", {}).get("RestartPolicy", {}).get("Name", None),
        "read_only": cattrs.get("HostConfig", {}).get("ReadonlyRootfs", None),
        "stdin_open": cattrs.get("Config", {}).get("OpenStdin", None),
        "tty": cattrs.get("Config", {}).get("Tty", None),
    }

    # Populate devices key if device values are present
    if cattrs.get("HostConfig", {}).get("Devices"):
        values["devices"] = [
            x["PathOnHost"] + ":" + x["PathInContainer"] for x in cattrs.get("HostConfig", {}).get("Devices")
        ]

    networks = {}
    if values["networks"] == set():
        del values["networks"]

        if len(cattrs.get("NetworkSettings", {}).get("Networks", {}).keys()) > 0:
            assumed_default_network = list(cattrs.get("NetworkSettings", {}).get("Networks", {}).keys())[0]
            values["network_mode"] = assumed_default_network
            networks = None
    else:
        networklist = c.networks.list()
        for network in networklist:
            if network.attrs["Name"] in values["networks"]:
                networks[network.attrs["Name"]] = {
                    "external": (not network.attrs["Internal"]),
                    "name": network.attrs["Name"],
                }
    #     volumes = {}
    #     if values['volumes'] is not None:
    #         for volume in values['volumes']:
    #             volume_name = volume.split(':')[0]
    #             volumes[volume_name] = {'external': True}
    #     else:
    #         volumes = None

    # handles both the returned values['volumes'] (in c_file) and volumes for both, the bind and volume types
    # also includes the read only option
    volumes = {}
    mountpoints = []
    if values["mounts"] is not None:
        for mount in values["mounts"]:
            destination = mount["Destination"]
            if not mount["RW"]:
                destination = destination + ":ro"
            if mount["Type"] == "volume":
                mountpoints.append(mount["Name"] + ":" + destination)
                if not createvolumes:
                    volumes[mount["Name"]] = {
                        "external": True
                    }  # to reuse an existing volume ... better to make that a choice? (cli argument)
            elif mount["Type"] == "bind":
                mountpoints.append(mount["Source"] + ":" + destination)
        values["volumes"] = mountpoints
    if len(volumes) == 0:
        volumes = None
    values["mounts"] = None  # remove this temporary data from the returned data

    # Check for command and add it if present.
    if cattrs.get("Config", {}).get("Cmd") is not None:
        values["command"] = cattrs.get("Config", {}).get("Cmd")

    # Check for exposed/bound ports and add them if needed.
    try:
        expose_value = list(cattrs.get("Config", {}).get("ExposedPorts", {}).keys())
        ports_value = [
            cattrs.get("HostConfig", {}).get("PortBindings", {})[key][0]["HostIp"]
            + ":"
            + cattrs.get("HostConfig", {}).get("PortBindings", {})[key][0]["HostPort"]
            + ":"
            + key
            for key in cattrs.get("HostConfig", {}).get("PortBindings")
        ]

        # If bound ports found, don't use the 'expose' value.
        if ports_value not in IGNORE_VALUES:
            for index, port in enumerate(ports_value):
                if port[0] == ":":
                    ports_value[index] = port[1:]

            values["ports"] = ports_value
        else:
            values["expose"] = expose_value

    except (KeyError, TypeError):
        # No ports exposed/bound. Continue without them.
        ports = None

    # Iterate through values to finish building yaml dict.
    for key in values:
        value = values[key]
        if value not in IGNORE_VALUES:
            ct[key] = value

    return cfile, networks, volumes


if __name__ == "__main__":
    main()

    ###################################################
# "constraints": {
#     cattrs.get("Spec", {}).get("TaskTemplate", {}).get("Placement", {}).get("Constraints", {})
# },
###################################################
