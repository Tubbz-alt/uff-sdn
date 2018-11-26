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
    def __init__(self, src, sport, dst, dport):
        self.src = src
        self.src_port = sport
        self.dst = dst
        self.dst_port = dport


class topologia:
    def __init__(self):
        self.sws = []
        self.dp_to_mac = {}
        self.dp_to_mac.setdefault(0, {})
        self.enlaces = []


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
        self.switch_to_port.setdefault(dpid, {})

        tcp_packet = pkt.get_protocol(tcp.tcp)
        ip_packet = pkt.get_protocol(ipv4.ipv4)
        arp_packet = pkt.get_protocol(arp.arp)
        new_msg = '>>> {} {}'.format(src, dst)
        if ip_packet:
            new_msg += ' | {} {}'.format(ip_packet.src, ip_packet.dst)
        if tcp_packet:
            new_msg += ' | {} {}'.format(tcp_packet.src_port,
                                         tcp_packet.dst_port)

        # print '{} | s{}'.format(new_msg, dpid)

        self.switch_to_port[dpid][src] = in_port
        if arp_packet:
            self.switch_to_port[dpid][arp_packet.src_ip] = in_port
        elif ip_packet:
            self.switch_to_port[dpid][ip_packet.src] = in_port

        if dst in self.switch_to_port[dpid]:
            out_port = self.switch_to_port[dpid][dst]
        elif ip_packet and ip_packet.dst in self.switch_to_port[dpid]:
            out_port = self.switch_to_port[dpid][ip_packet.dst]
        elif arp_packet and arp_packet.dst_ip in self.switch_to_port[dpid]:
            out_port = self.switch_to_port[dpid][arp_packet.dst_ip]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions_add = [parser.OFPActionDecNwTtl(), parser.OFPActionOutput(out_port)]
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch()
            match.set_dl_type(ether.ETH_TYPE_IP)
            match.set_ip_proto(inet.IPPROTO_ICMP)
            match.set_in_port(in_port)
            print self.topo.dp_to_mac
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
        for switch, value in cost:
            if visited[switch] == False and value < minimum:
                minimum = value
                chosen_node = switch
        return chosen_node

    @classmethod
    def get_neighbors(cls, parent, actual, enlaces):
        neighbors = []
        for enlace in enlaces:
            if enlace.src == actual and enlace.dst != parent:
                neighbors.append((enlace.dst,enlace.dst_port))
        return neighbors

    @classmethod
    def all_visited(cls, visited):
        for v in visited:
            if v is False:
                return False
        return True

    def dijkstra(self, topo, initial):
        previous=[]
        cost=[]
        visited=[]

        for sw in topo.sws:
            cost.append((sw, float('inf')))
            visited.append((sw, False))
        cost[initial] = 0

        parent = None
        actual = initial

        while self.all_visited(visited) is False:
            actual = self.choose_min_cost_node(cost, visited)
            neighbors = self.get_neighbors(parent, actual, self.topo.enlaces)
            for neighbor in neighbors:
                if actual == initial:
                    cost[neighbor] = 1
                    previous[neighbor] = initial
                else:
                    sum = cost[actual] + 1 # Se fosse com pesos diferentes, teria que somar com o peso do link de actual para neighbor
                    if sum < cost[neighbor]:
                        cost[neighbor] = sum
                        previous[neighbor] = actual
            visited[actual] = True

        return self.getPaths(initial, self.topo.sws, previous)

    @classmethod
    def getPaths(cls, initial, switches, previous):
        paths = []
        path = []
        for switch in switches:
            if switch != initial:
                path.append(initial)
                hop = previous[switch]
                while hop != initial:
                    paths.append(hop)
                    hop = previous[hop]
                path.append(switch)
                paths.append(path)

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
