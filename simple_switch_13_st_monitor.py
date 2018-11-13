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

SLEEP_TIME = 10.0

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
        self.monitor_thread = hub.spawn(self.flow_request)
        self.iperf = Iperf()
        # self.monitor_thread2 = hub.spawn(self.port_request)

    def flow_request(self):
        while True:
            for dp in self.dpset.dps.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                req = parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)
            hub.sleep(SLEEP_TIME)
            print('\n')

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

            dpid = ev.msg.datapath.id
            priority = stats.priority
            byte = stats.byte_count

            value = self.iperf.get(dpid, match)
            if value is not None:
                bandwidth = (((byte - value) / SLEEP_TIME) * 8) / (10.0 ** 9)
                self.iperf.update(dpid, match, byte)
            else:
                bandwidth = ((byte / SLEEP_TIME) * 8) / (10.0 ** 9)
                self.iperf.add(dpid, match, byte)
            if bandwidth >= .1:
                print(bandwidth, byte, value)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
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
            print "\n>> DPID=", ev.msg.datapath.id, s


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
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
