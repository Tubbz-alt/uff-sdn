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
        h3 = self.addHost( 'h3', mac='00:00:00:00:00:03' )
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )

        # Add links
        self.addLink( h1, s1 )
        self.addLink( h2, s2 )
        self.addLink( h3, s3 )

        self.addLink( s1, s2 )
        self.addLink( s1, s3 )
        self.addLink( s2, s3 )


topos = { 'ciclo': (lambda: MyTopo())}

# def main():
#     topo = MyTopo()
#     mn = Mininet(topo=topo, controller=RemoteController)
#     mn.start()
#     CLI(mn)
#     mn.stop()


# if __name__ == '__main__':
#     main()
