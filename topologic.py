from flask import Flask

from ncclient import manager
import xmltodict
import json
from ncclient.xml_ import new_ele
import networkx as nx
import matplotlib.pyplot as plt


def obtener_lldp_json(host, user, password):
    with manager.connect(
        host=host,
        port=830,
        username=user,
        password=password,
        hostkey_verify=False,
        device_params={"name": "junos"},
        allow_agent=False,
        look_for_keys=False
    ) as m:

        rpc = new_ele("get-lldp-neighbors-information")
        response = m.dispatch(rpc)

        # 💡 Esto extrae el XML como string
        raw_xml = str(response)

        # Parseo a diccionario
        data = xmltodict.parse(raw_xml)

        neighbors = data['rpc-reply']['lldp-neighbors-information'].get('lldp-neighbor-information', [])

        if isinstance(neighbors, dict):
            neighbors = [neighbors]

        

        json_list = []
        for neighbor in neighbors:
            json_list.append({
                "local_interface": neighbor.get("lldp-local-port-id"),
                "remote_chassis_id": neighbor.get("lldp-remote-chassis-id"),
                "remote_port_id": neighbor.get("lldp-remote-port-id"),
                "remote_port_description": neighbor.get("lldp-remote-port-description"),
                "remote_system_name": neighbor.get("lldp-remote-system-name"),
                "remote_system_description": neighbor.get("lldp-remote-system-description"),
                "remote_system_capabilities": neighbor.get("lldp-remote-system-capabilities"),
                "remote_enabled_capabilities": neighbor.get("lldp-remote-enabled-capabilities"),
                "ttl": neighbor.get("lldp-remote-ttl")
            })


        return json_list


def graph_to_topology_json(G):
    nodes = []
    links = []

    # Mapear nodo a índice para referencia en enlaces
    node_indices = {}
    for i, node in enumerate(G.nodes()):
        node_indices[node] = i
        nodes.append({"id": i, "label": node})

    for src, dst in G.edges():
        links.append({
            "source": node_indices[src],
            "target": node_indices[dst]
        })

    return {"nodes": nodes, "links": links}



# === Uso ===
def topo():
    hosts = ["172.20.115.32","172.20.115.40","172.20.115.41"]
    user = "germanm"
    password = "juniper1"

    lldp_data = []
    for host in hosts:
        lldp_data += obtener_lldp_json(host, user, password)

    # Imprimir bonito
    print(json.dumps(lldp_data, indent=2))

    local_system_name = "RouterLocal"

    # === Crear grafo dirigido ===
    G = nx.DiGraph()

    for entry in lldp_data:
        local_port = f"{local_system_name}:{entry['local_interface']}"
        remote_name = entry.get("remote_system_name", "Unknown")
        remote_port = entry.get("remote_port_description", "Unknown")
        remote_node = f"{remote_name}:{remote_port}"

        # Añadir nodos y conexión
        G.add_edge(local_port, remote_node)

   
    # === Dibujar el grafo ===
    #plt.figure(figsize=(10, 6))
    #pos = nx.spring_layout(G, seed=42)
    #nx.draw(G, pos, with_labels=True, node_size=2000, node_color='lightblue', font_size=9, arrows=True)
    #plt.title("Topología LLDP")
    #plt.tight_layout()
    #plt.show()

    # === Exportar a JSON ===
    topology_json = graph_to_topology_json(G)

    # Guardar a archivo si lo deseas
    #with open("lldp_topology.json", "w") as f:
    #    json.dump(topology_json, f, indent=2)

    # También puedes imprimirlo
    print(json.dumps(topology_json, indent=2))
    return json.dumps(topology_json,indent=2)


app = Flask(__name__)
PREFIX = "/api"





@app.route(PREFIX+"/topology",methods=["GET"])
def members():
    print("Received request for topology")
    topology = topo()
    print("Topology generated successfully")
    print("Returning topology data")
    print(topology)
    # Aquí puedes devolver la topología como JSON
    # return jsonify(topology)
    # O simplemente devolver el string JSON
    # return topology   
    return topology

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")    
