#! /usr/bin/env python3
import argparse
import datetime
import re
import sys

from collections import OrderedDict

import docker
import pyaml

IGNORE_VALUES = [None, "", [], "null", {}, "default", 0, ",", "no"]

#В ЭТОМ СКРИПТЕ container ЗАМЕНЁН НА service
#ЧТОБЫ ВЫВОДИТЬ ИНФУ ПО СЕРВИСАМ А НЕ ПО КОНТЕЙНЕРАМ
def list_service_names():
    c = docker.from_env()
    return [service.name for service in c.services.list(all=True)]


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
        description="Generate docker-compose yaml definition from running service.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Include all active services",
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
        help="The name of the service to process.",
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
        help="Filter services by regex",
    )
    args = parser.parse_args()

    service_names = args.cnames

    if args.all:
        service_names.extend(list_service_names())

    if args.filter:
        cfilter = re.compile(args.filter)
        service_names = [c for c in service_names if cfilter.search(c)]

    struct = {}
    networks = {}
    volumes = {}
    services = {}

    for cname in service_names:
        print("cname")
        print(cname)
        cfile, c_networks, c_volumes = generate(cname, createvolumes=args.createvolumes)

        struct.update(cfile)

        if not c_networks == None:
            networks.update(c_networks)
        if not c_volumes == None:
            volumes.update(c_volumes)

    # moving the networks = None statements outside of the for loop. Otherwise any service could reset it.
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


def generate(cname, createvolumes=False):
    c = docker.from_env()

    try:
       cid = [x.short_id for x in c.services.list() if cname == x.name or x.short_id in cname][0]
    except IndexError:
        print("That service is not available.", file=sys.stderr)
        print(cname)
        sys.exit(1)

    sattrs = c.services.get(cid).attrs

#----------------------------------------------------------------------------------------
    print("------------------------------")
    print("вывод  c.services")
    print( c.services)
    print("------------------------------")
    print("------------------------------")
    print("вывод sattrs")                     #!!! moiseev
    print(sattrs)

    print("------------------------------")
    print("вывод services")                  #!!! moiseev
    print(c.services.list())
    print("------------------------------")
    print("вывод services get(cid)")         #!!! moiseev
    print(c.services.get(cid))
    print("------------------------------")
    print("вывод cname")                     #!!! moiseev
    print(cname)
    print("------------------------------")
    print("вывод c.services.get(cid).name")   #!!! moiseev
    print(c.services.get(cid).name)
    print("------------------------------")
    #добавляем считку  поля placement constraints - node.role == manager
    print("------------------------------")
    print("вывод placement-constraints  spec и остальное в кавычках    sattrs.get(Spec, {}).get(TaskTemplate, {}).get(Placement, {}).get(Constraints, {})")                     #!!! moiseev
    print(sattrs.get("Spec", {}).get("TaskTemplate", {}).get("Placement", {}).get("Constraints", {}))
    print("------------------------------")
#----------------------------------------------------------------------------------------
#пытаемся вывести список сервисов. Парами Имя сервиса - его айди
    print("------------------------------")
    print("------------------------------")


    # Build yaml dict structure

    cfile = {}
    #cfile[sattrs.get("Name")[1:]] = {}      # БЫЛО ТАК!!!! моисеев
    #ct = cfile[sattrs.get("Name")[1:]]

    cfile[c.services.get(cid).name] = {}
    ct = cfile[c.services.get(cid).name]

    default_networks = ["bridge", "host", "none"]

    values = {
        "cap_drop": sattrs.get("HostConfig", {}).get("CapDrop", None),
        "cgroup_parent": sattrs.get("HostConfig", {}).get("CgroupParent", None),
        "service_name": c.services.get(cid).name,
        "devices": [],
        "dns": sattrs.get("HostConfig", {}).get("Dns", None),
        "dns_search": sattrs.get("HostConfig", {}).get("DnsSearch", None),
        "environment": sattrs.get("Config", {}).get("Env", None),
        "extra_hosts": sattrs.get("HostConfig", {}).get("ExtraHosts", None),
        "image": sattrs.get("Config", {}).get("Image", None),
        "labels": sattrs.get("Config", {}).get("Labels", {}),
        "links": sattrs.get("HostConfig", {}).get("Links"),
        #'log_driver': sattrs.get('HostConfig']['LogConfig']['Type'],
        #'log_opt': sattrs.get('HostConfig']['LogConfig']['Config'],
        "logging": {
            "driver": sattrs.get("HostConfig", {}).get("LogConfig", {}).get("Type", None),
            "options": sattrs.get("HostConfig", {}).get("LogConfig", {}).get("Config", None),
        },
        "networks": {
            x for x in sattrs.get("NetworkSettings", {}).get("Networks", {}).keys() if x not in default_networks
        },
        "security_opt": sattrs.get("HostConfig", {}).get("SecurityOpt"),
        "ulimits": sattrs.get("HostConfig", {}).get("Ulimits"),
        # the line below would not handle type bind
        #        'volumes': [f'{m["Name"]}:{m["Destination"]}' for m in sattrs.get('Mounts'] if m['Type'] == 'volume'],
        "mounts": sattrs.get("Mounts"),  # this could be moved outside of the dict. will only use it for generate
        "volume_driver": sattrs.get("HostConfig", {}).get("VolumeDriver", None),
        "volumes_from": sattrs.get("HostConfig", {}).get("VolumesFrom", None),
        "entrypoint": sattrs.get("Config", {}).get("Entrypoint", None),
        "user": sattrs.get("Config", {}).get("User", None),
        "working_dir": sattrs.get("Config", {}).get("WorkingDir", None),
        "domainname": sattrs.get("Config", {}).get("Domainname", None),
        "hostname": sattrs.get("Config", {}).get("Hostname", None),
        "ipc": sattrs.get("HostConfig", {}).get("IpcMode", None),
        "mac_address": sattrs.get("NetworkSettings", {}).get("MacAddress", None),
        "privileged": sattrs.get("HostConfig", {}).get("Privileged", None),
        "restart": sattrs.get("HostConfig", {}).get("RestartPolicy", {}).get("Name", None),
        "read_only": sattrs.get("HostConfig", {}).get("ReadonlyRootfs", None),
        "stdin_open": sattrs.get("Config", {}).get("OpenStdin", None),
        "tty": sattrs.get("Config", {}).get("Tty", None),
    }

    # Populate devices key if device values are present
    if sattrs.get("HostConfig", {}).get("Devices"):
        values["devices"] = [
            x["PathOnHost"] + ":" + x["PathInService"] for x in sattrs.get("HostConfig", {}).get("Devices")
        ]

    networks = {}
    if values["networks"] == set():
        del values["networks"]

        if len(sattrs.get("NetworkSettings", {}).get("Networks", {}).keys()) > 0:
            assumed_default_network = list(sattrs.get("NetworkSettings", {}).get("Networks", {}).keys())[0]
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
    if sattrs.get("Config", {}).get("Cmd") is not None:
        values["command"] = sattrs.get("Config", {}).get("Cmd")

    # Check for exposed/bound ports and add them if needed.
    try:
        expose_value = list(sattrs.get("Config", {}).get("ExposedPorts", {}).keys())
        ports_value = [
            sattrs.get("HostConfig", {}).get("PortBindings", {})[key][0]["HostIp"]
            + ":"
            + sattrs.get("HostConfig", {}).get("PortBindings", {})[key][0]["HostPort"]
            + ":"
            + key
            for key in sattrs.get("HostConfig", {}).get("PortBindings")
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