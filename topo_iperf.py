from mininet.log import setLogLevel
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.net import Mininet

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1', mac='00:00:00:00:00:01' )
        h2 = self.addHost( 'h2', mac='00:00:00:00:00:02' )
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )
        s4 = self.addSwitch( 's4' )
        s5 = self.addSwitch( 's5' )
        s6 = self.addSwitch( 's6' )

        # Add links
        self.addLink( h1, s1 )
        self.addLink( h2, s4 )

        self.addLink( s1, s2 )
        self.addLink( s3, s2 )
        self.addLink( s4, s3 )
        self.addLink( s4, s6 )
        self.addLink( s5, s6 )
        self.addLink( s5, s1 )


topos = { 'ciclo': (lambda: MyTopo())}

def main():
    topo = MyTopo()
    mn = Mininet(topo=topo, controller=RemoteController)
    mn.start()
    h2 = mn.get('h2')
    h2.cmdPrint('iperf -s -u -i 1 -p 11111 > logs/iperf1.log 2>&1 &')
    h2.cmdPrint('iperf -s -u -i 1 -p 22222 > logs/iperf2.log 2>&1 &')
    CLI(mn)
    mn.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()
