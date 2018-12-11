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
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import stplib
from ryu.lib import hub
from ryu.controller import dpset
from ryu.topology import event

SLEEP_TIME = .5
GIGABYTE = 10.0 ** 9
MEGABYTE = 10.0 ** 6


class enlace:
    def __init__(self, src, sport, dst, dport):
        self.src = src
        self.src_port = sport
        self.dst = dst
        self.dst_port = dport


class topologia:
    def __init__(self):
        self.sws = []
        self.enlaces = []


class Iperf():
    def __init__(self):
        self._iperf = {}

    def update(self, dpid, match, byte):
        dpid = str(dpid)
        match = str(match)
        switch = self._iperf[dpid]
        switch[match] = byte

    def add(self, dpid, match, byte):
        dpid = str(dpid)
        match = str(match)
        # {s1: {udp: 10}}
        switch = self._iperf.get(dpid, None)
        if switch is None:
            self._iperf[dpid] = {match: byte}
        else:
            switch[match] = byte

    def get(self, dpid, match):
        dpid = str(dpid)
        match = str(match)
        switch = self._iperf.get(dpid, None)
        # print '>>>', dpid, match, switch, self._iperf
        if switch:
            return switch.get(match, None)
        return None


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp, 'dpset': dpset.DPSet}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.stplib = kwargs.get('stplib', None)
        self.dpset = kwargs.get('dpset', None)
        # self.monitor_thread = hub.spawn(self.flow_request)
        self.monitor_thread2 = hub.spawn(self.port_request)
        self.iperf = Iperf()
        self._first_time = True
        self.topo = topologia()




    # -------------------------------------------------------------------------------

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
        # for qwe in ev.switch.ports:
        #     print '>>>>>>>', qwe.__dict__
        # print '\n'
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

    def flow_request(self):
        while True:
            for dp in self.dpset.dps.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                req = parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)
            hub.sleep(SLEEP_TIME)

    def port_request(self):
        while True:
            for dp in self.dpset.dps.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                req = parser.OFPPortStatsRequest(dp, 0, ofproto.OFPP_ANY)
                dp.send_msg(req)
            hub.sleep(SLEEP_TIME)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _stats_reply_handler(self, ev):
        if len(ev.msg.body) == 0:
            print "Nao existem fluxos"
        for stats in ev.msg.body:
            try:
                actions = stats.instructions[0].actions[0].port
            except IndexError:
                actions = stats.instructions
            match = stats.match
            dic = {'dpid': ev.msg.datapath.id,
                   'priority': stats.priority,
                   'cookie': stats.cookie,
                   'idle_timeout': stats.idle_timeout,
                   'hard_timeout': stats.hard_timeout,
                   'actions': actions,
                   'match': match,
                   'byte_count': stats.byte_count,
                   'duration_sec': stats.duration_sec,
                   'duration_nsec': stats.duration_nsec,
                   'packet_count': stats.packet_count,
                   'table_id': stats.table_id}


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        dpid = ev.msg.datapath.id
        if dpid == 1:
            if len(ev.msg.body) == 0:
                print "Resposta nula"
            for stats in ev.msg.body:
                s = {'port_no': stats.port_no,
                    'rx_packets': stats.rx_packets,
                    'tx_packets': stats.tx_packets,
                    'rx_bytes': stats.rx_bytes,
                    'tx_bytes': stats.tx_bytes,
                    'rx_dropped': stats.rx_dropped,
                    'tx_dropped': stats.tx_dropped,
                    'rx_errors': stats.rx_errors,
                    'tx_errors': stats.tx_errors,
                    'rx_frame_err': stats.rx_frame_err,
                    'rx_over_err': stats.rx_over_err,
                    'rx_crc_err': stats.rx_crc_err,
                    'collisions': stats.collisions}
                # print "\n>> DPID=", ev.msg.datapath.id, s
                # priority = stats.priority
                byte = stats.tx_bytes
                port = stats.port_no

                value = self.iperf.get(dpid, port)
                if value is not None:
                    bandwidth = (((byte - value) / SLEEP_TIME) * 8) / GIGABYTE
                    self.iperf.update(dpid, port, byte)
                else:
                    bandwidth = ((byte / SLEEP_TIME) * 8) / GIGABYTE
                    self.iperf.add(dpid, port, byte)
                if bandwidth >= 0.1:
                    print dpid, port, bandwidth, self._first_time
                # return
                # if banda > 500 and (host in switch) and (mac_src != mac_host)
                if dpid == 1 and bandwidth >= .75 and self._first_time:
                    print(dpid, port, bandwidth, byte, value)
                    self._first_time = False
                    parser = [None,]
                    datapath = [None, ]
                    for dp in self.dpset.dps.values():
                        datapath.append(dp)
                        parser.append(dp.ofproto_parser)
                    if port == 2:
                        self.add_flow(datapath[1], 10, parser[1].OFPMatch(udp_dst=11111), [parser[1].OFPActionOutput(3)])
                        self.add_flow(datapath[5], 10, parser[5].OFPMatch(udp_dst=11111), [parser[5].OFPActionOutput(1)])
                        self.add_flow(datapath[6], 10, parser[6].OFPMatch(udp_dst=11111), [parser[6].OFPActionOutput(1)])
                        print 'success 2'
                    elif port == 3:
                        self.add_flow(datapath[1], 10, parser[1].OFPMatch(udp_dst=11111), [parser[1].OFPActionOutput(2)])
                        self.add_flow(datapath[2], 10, parser[2].OFPMatch(udp_dst=11111), [parser[2].OFPActionOutput(2)])
                        self.add_flow(datapath[3], 10, parser[3].OFPMatch(udp_dst=11111), [parser[3].OFPActionOutput(2)])
                        print 'success 3'


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
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

    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
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
        self.mac_to_port.setdefault(dpid, {})

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 2, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 2, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
