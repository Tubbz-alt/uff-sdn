# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import inet
from ryu.ofproto import ether
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import tcp
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.controller import dpset
from ryu.topology import event
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib import mac


class enlace:
    def __init__(self, dpid_src, src_port, dpid_dst, dst_port):
        self.dpid_src = dpid_src
        self.src_port = src_port
        self.dpid_dst = dpid_dst
        self.dst_port = dst_port

    def __str__(self):
        return '{}:{} -> {}:{}'.format(str(self.dpid_src), str(self.src_port), str(self.dpid_dst), str(self.dst_port))


class topologia:
    def __init__(self):
        self.sws = []
        # self.dp_to_mac = {}
        # self.dp_to_mac.setdefault(0, {})
        self.enlaces = []

    def __str__(self):
        asd = ''
        for enlace in self.enlaces:
            asd += '- {}\n'.format(str(enlace))
        msg = 'Switches: {} \nEnlaces:\n{}'.format(str(self.sws), asd)
        return msg


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet, 'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.switch_to_port = {
            # dpid: {mac: port, ip: port}
        }
        self.dpset = kwargs.get('dpset', None)
        self.stplib = kwargs.get('stplib', None)
    	self.topo = topologia()
        self.first_time = True

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    # PORTA
    @set_ev_cls(event.EventPortDelete)
    def deleta_porta(self, port):
        print('Porta deletada switch {}, porta {}' .format(
            port.port.dpid, port.port.port_no))

    @set_ev_cls(event.EventPortAdd)
    def adiciona_porta(self, port):
        print('Porta adicionada switch {}, porta {}' .format(
            port.port.dpid, port.port.port_no))

    @set_ev_cls(event.EventPortModify)
    def modifica_porta(self, port):
        print('Porta modificada switch {}, porta {}, mac {}' .format(
            port.port.dpid, port.port.port_no, port.port.hw_addr))

    # SWITCH

    @set_ev_cls(event.EventSwitchEnter, MAIN_DISPATCHER)
    def entrou_switch(self, ev):
        # list: ev.switch.ports
        # {'hw_addr': '1a:a5:c5:a3:c5:16', '_config': 0, 'name': 's1-eth1', '_state': 4, 'dpid': 1, 'port_no': 1}
        print ("Switch ID: {} entrou na topologia!".format(ev.switch.dp.id))
        for asd in ev.switch.ports:
            print '>>>>>>>', asd.__dict__
        print '\n'
        self.topo.sws.append(ev.switch.dp.id)
        # self.topo.dp_to_mac[ev.switch.dp.id] = ev.switch.ports.hw_addr

    @set_ev_cls(event.EventSwitchLeave, MAIN_DISPATCHER)
    def saiu_switch(self, ev):
        print "Switch ID: {} saiu da topologia!".format(ev.switch.dp.id)
        del self.topo.sws[self.topo.sws.index(ev.switch.dp.id)]

    # LINK
    @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER)
    def entrou_link(self, ev):
        print "ENTROU um link!"  # {} <> {}".format(ev.link.src.__dict__, ev.link.dst.__dict__)
        self.topo.enlaces.append(enlace(
            ev.link.src.dpid, ev.link.src.port_no, ev.link.dst.dpid, ev.link.dst.port_no))

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def saiu_link(self, ev):
        print "SAIU um link!"
        # del self.topo.elnaces[self.topo.enlaces.index(ev.switch.dp.id)]

    # -------------------------------------------------------------------------------

    # MAIN
    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # print self.dpset.get_all()
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        #print self.topo
        #if self.first_time:
        dpid_paths = self.dijkstra(self.topo,dpid)
        get_out_port(dpid, )
        #print "\n"
        #    self.first_time = False

        out_port = ofproto.OFPP_FLOOD
        actions_add = [parser.OFPActionDecNwTtl(), parser.OFPActionOutput(out_port)]
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch()
            match.set_dl_type(ether.ETH_TYPE_IP)
            match.set_ip_proto(inet.IPPROTO_ICMP)
            match.set_in_port(in_port)
            # print self.topo.dp_to_mac
            match.set_dl_src(mac.haddr_to_bin(src))
            match.set_dl_dst(mac.haddr_to_bin(dst))
            # print(dst, src)

            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 10, match, actions_add, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 10, match, actions_add)
                pass
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @classmethod
    def choose_min_cost_node(cls, cost, visited):
        minimum = float('inf')
        chosen_node = None
        for switch, value in cost.items():
            if visited[switch] == False and value < minimum:
                minimum = value
                chosen_node = switch
        return chosen_node

    @classmethod
    def get_neighbors(cls, parent, actual, enlaces):
        neighbors = {}
        for enlace in enlaces:
            if enlace.dpid_src == actual and enlace.dpid_dst != parent:
                neighbors[enlace.dpid_dst] = enlace.dst_port
        return neighbors

    @classmethod
    def all_visited(cls, visited):
        for value in visited.values():
            if value is False:
                return False
        return True

    def dijkstra(self, topo, initial):
        previous = {}
        cost = {}
        visited = {}

        for sw in topo.sws:
            cost[sw] = float('inf')
            visited[sw] = False
        cost[initial] = 0

        parent = None

        while self.all_visited(visited) is False:
            actual = self.choose_min_cost_node(cost, visited)
            neighbors = self.get_neighbors(parent, actual, topo.enlaces)
            for neighbor in neighbors:
                if actual == initial:
                    cost[neighbor] = 1
                    previous[neighbor] = initial
                else:
                    soma = cost[actual] + 1 # Se fosse com pesos diferentes, teria que somar com o peso do link de actual para neighbor
                    if soma < cost[neighbor]:
                        cost[neighbor] = soma
                        previous[neighbor] = actual
            visited[actual] = True

        return self.getPaths(initial, topo.sws, previous)

    @classmethod
    def getPaths(cls, initial, switches, previous):
        paths = []
        #print "\nInitial {}".format(initial)
        for dpid in switches:
            #print "Last {}".format(dpid)
            path = []
            if dpid != initial:
                hop = previous[dpid]
                while hop != initial:
                    #print ">>HOP",hop
                    path.insert(0, hop)
                    hop = previous[hop]
                path.insert(0, initial)
                path.append(dpid)
                #print path
                paths.append(path)
        return paths

    @classmethod
    def get_out_port(cls, src, dst, paths, enlaces):
        next_hop = None
        for path in paths:
            if path[0] == src:
                if path[-1] == dst: #get last
                    next_hop = path[1]
        for enlace in enlaces:
            if enlace.src == src and enlace.dst != next_hop:
               return enlace.src_port
