# Redes Definidas por Software

Informações sobre a disciplina de **Redes Definidas por Software** ministrada em 2018.2 na *Universidade Federal Fluminense*.

Apresentação sobre [Controladores SDN](https://arthurazs.github.io/uff-sdn/controladores).

## Calendário

### Aulas

> **[Arthur]** Controladores SDN **[28/08/2018]**
>
> **[Wilson]** OpenStack **[06/09/2018]**

### Artigos

> **[Arthur]** *Jain, R., & Paul, S. (2013). Network Virtualization and Software Defined Networking for Cloud Computing : A Survey. IEEE Communications Magazine, 51(11), 24–31.* **[??/??/2018]**
>
> **[Juan]** *B. A. A. Nunes, M. Mendonca, X. Nguyen, K. Obraczka and T. Turletti, "A Survey of Software-Defined Networking: Past, Present, and Future of Programmable Networks," in IEEE Communications Surveys & Tutorials, vol. 16, no. 3, pp. 1617-1634, Third Quarter 2014.* **[??/??/2018]**
>
> **[Lucas]** *Jon Matias, Jokin Garay, Nere Toledo, Juanjo Unzilla and Eduardo Jacob. "Toward an SDN-Enabled NFV Architecture" IEEE Communications Magazine, April 2015* **[??/??/2018]**
>
> **[Wilson]** *D. Kreutz, F. M. V. Ramos, P. E. Veríssimo, C. E. Rothenberg, S. Azodolmolky and S. Uhlig, "Software-Defined Networking: A Comprehensive Survey," in Proceedings of the IEEE, vol. 103, no. 1, pp. 14-76, Jan. 2015* **[??/??/2018]**
>
> **[Pedro]** *Traffic Engineering in Software Defined Networks Sugam Agarwal,Murali Kodialam,T. V. Lakshman* **[??/??/2018]**
>
> **[Camila]** *Cassongo, A.B.: The comparison of network simulators for SDN. Modern information system and technologies 5 (2016)* **[??/??/2018]**

## Intro

Rever lista do Slide:

    - Diferença entre Switch e Roteador?
    - MPSI? (ping)
    - Data Center
    - MPLS
    - Outros?

Sistemas - Vertical x Horizontal:

- Mainframe x PC
- Rack x Hardware de Comutação

Assim como Ubuntu é um sistema operacional de computadores, **SDN** é uma espécie de Sistema Operacional de **rede**.

- **Plano de Dados** encaminha os pacotes
  - Controle de Acesso
  - QoS
- **Plano de Controle** organiza a tabela de encaminhamento

Camada 2 x Camada 3:

- **Switch** Hardware -> MAC x Porta
- **Roteador** Rede -> IP

## Aula 21/08/2018

- Substrato de Rede/Hardware?
- **Data path** é o Hardware de Encaminhamento
- **Fluxo** é um conjunto de pacotes
- Tabela de Fluxos TCAM?
- Como funciona comunicação SSL?

1. Rodar `netstat -l` para descobrir a porta do switch
2. Descobrir como rodar wireshark sem interface gráfica

## TODO

- Montar aula (ver [A Comparison between Several Software Defined Networking Controllers](https://ieeexplore.ieee.org/document/7357774/))
- Ler sobre OpenFlow

## Passo a Passo

### Instalar o mininet

```bash
sudo apt install virtualbox
```

1. Baixe e descompacte o [Mininet 2.2.2 on Ubuntu 14.04 LTS - 64 bit](https://github.com/mininet/mininet/wiki/Mininet-VM-Images).
2. Abrir o arquivo com extensão ".ovf".
3. Logar na máquina virtual com usuário/senha: `mininet/mininet`

### Instalar ryu no mininet

```bash
sudo apt update
sudo apt install python-pip python-dev -y
pip install ryu --user --upgrade
echo "export PATH=~/.local/bin:$PATH" >> ~/.bashrc
source ~/.bashrc
ryu --version
```

### Instalar a interface gráfica

```bash
sudo apt update
sudo apt install xubuntu-desktop -y
startxfce4
```

Para aumentar a resolução da tela, primeiro execute o comando `sudo apt install virtualbox-guest-additions-iso -y`. Em seguida, aumente a RAM da VM para 1GB e a RAM da placa gráfica para 64MB.

## Executando exercicio5

1. Executar o ryu: `ryu-manager simple_switch.py`
2. Executar o mininet: `sudo mn --controller remote`
3. Abrir o xterm do s1 no mininet: `xterm s1`
4. Executar o exercicio5: `python exercicio5.py`
5. Executar o comando pingall no mininet: `pingall`


## Aula Wilson (Datacenter / Openstack)

- O que e como o Neutron faz?
- Zero Touch (google)
