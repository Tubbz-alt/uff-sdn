# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
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

from operator import attrgetter

from ryu.app import simple_switch_stp_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub


SLEEP_TIME = .5
MEGABYTE = 10.0 ** 6


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
        if switch:
            return switch.get(match, None)
        return None


class SimpleMonitor13(simple_switch_stp_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.iperf = Iperf()
        self._first_time = True

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(SLEEP_TIME)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        if dpid == 1:
            for stat in sorted(body, key=attrgetter('port_no')):
                byte = stat.tx_bytes
                port = stat.port_no

                value = self.iperf.get(dpid, port)
                if value is not None:
                    bandwidth = (((byte - value) / SLEEP_TIME) * 8) / MEGABYTE
                    self.iperf.update(dpid, port, byte)
                else:
                    bandwidth = ((byte / SLEEP_TIME) * 8) / MEGABYTE
                    self.iperf.add(dpid, port, byte)

                if dpid == 1 and bandwidth >= 9:
                    print(dpid, port, bandwidth, self._first_time)

                if dpid == 1 and bandwidth >= 15 and self._first_time:
                    print("New flow for port {}".format(port))
                    self._first_time = False
                    if port == 2:
                        self.new_udp_flow(dpid=1, port_out_to=3, port_out_from=1)
                        self.new_udp_flow(dpid=5, port_out_to=1, port_out_from=2)
                        self.new_udp_flow(dpid=6, port_out_to=1, port_out_from=2)
                        self.new_udp_flow(dpid=4, port_out_to=1, port_out_from=3)
                    elif port == 3:
                        self.new_udp_flow(dpid=1, port_out_to=2, port_out_from=1)
                        self.new_udp_flow(dpid=2, port_out_to=2, port_out_from=1)
                        self.new_udp_flow(dpid=3, port_out_to=2, port_out_from=1)
                        self.new_udp_flow(dpid=4, port_out_to=1, port_out_from=2)

    def new_udp_flow(self, dpid, port_out_to, port_out_from):
        datapath = self.datapaths[dpid]

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match_to = parser.OFPMatch(eth_type=2048, ip_proto=17, udp_dst=11111)
        match_from = parser.OFPMatch(eth_type=2048, ip_proto=17, udp_src=11111)
        inst_to = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            [parser.OFPActionOutput(port_out_to)])]
        inst_from = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            [parser.OFPActionOutput(port_out_from)])]
        mod_to = parser.OFPFlowMod(
            datapath=datapath, priority=65535,
            match=match_to, instructions=inst_to)
        mod_from = parser.OFPFlowMod(
            datapath=datapath, priority=65535,
            match=match_from, instructions=inst_from)
        datapath.send_msg(mod_to)
        datapath.send_msg(mod_from)
