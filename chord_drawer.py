#! /usr/bin/python3
import threading
from turtle import *
import json
import socket, select
import sys
import math
if __name__ == "__main__":
    from ezpylog.Logger import Logger, LogLevel
else:
    from .ezpylog.Logger import Logger, LogLevel



NCLE = 64
PORT_DRAWER = 9000
IP_DRAWER = '192.168.1.35' #mettre 'localhost' sur un système en local'
MSGS_TO_TRACK = ["join", "get", "res", "update", "ok", "updateAck", "quit", "nok"]
MSGS = ["join", "get", "res", "update", "ok", "new", "holder_req", "holder_res", "updateAck", "quit", "nok"]
compt = dict.fromkeys(MSGS,0)
#["join", "get", "res", "update", "ok", "new", "holder_req", "holder_res", "updateAck", "quit", "nok"]
LOGLVL = LogLevel.INFO

#IP_DRAWER est valable pour le notifieur uniquement, le drawer est toujours en localhost evidemment
#
#Dans votre noeud chord vous devez ajouter :
#               notifier.configure_node([votre_ip],[port_du_noeud])
#
#Le noeud qui va creer le réseau (le premier appelé) devra aussi s'enregistrer auprès du drawer :
#               notifier.notify_first_node([votre_ip],[port_du_noeud],[cle_du_noeud])
#
#N'oubliez pas de faire un import des modules nécessaire dans chord_tools.py
#(en admetant que ce fichier se trouve dans le dossier ChordDrawer)
#               from ChordDrawer.chord_drawer import *
#
#Il faut aussi décorer la fonction json_send(ip, port, data) dans le fichier chord_tools.py 
#avec @draw_activity pour que le notifieur puisse capter l'activité du noeud
#               @draw_activity
#               def json_send(ip, port, data):
#                   ...


def draw_activity(func):
    global notifier
    def wrapper(ip,port,data):
        if(notifier.is_active() and data["type"] in MSGS_TO_TRACK):
            notifier.send(ip,port,data)
        return func(ip,port,data)
    return wrapper


def draw_arrow(tt,taille): #affiche le bout de la fleche
    pos = tt.pos()
    tt.setheading(tt.heading()+35+180)
    tt.pendown()
    tt.forward(taille)
    tt.goto(pos)
    tt.setheading(tt.heading()-70)
    tt.forward(taille)
    tt.penup()

def angle_from_coords(coords): #retourne l'angle en degrés d'un point
    if(coords[0] == 0):
        if(coords[1] > 0):
            return 90
        else:
            return 270
    if(coords[0] < 0):
        return (math.degrees(math.atan(coords[1]/coords[0]))+180)%360
    if(coords[1] < 0):
        return (math.degrees(math.atan(coords[1]/coords[0]))+360)%360
    return math.degrees(math.atan(coords[1]/coords[0]))


def draw_text(tt, coords, text, taille):
    tt.goto(coords)
    tt.setheading(0)
    tt.pendown()
    tt.write(text, False, align="center", font=("Arial", int(taille/20)))
    tt.penup()


def draw_line_to(tt, end, text, taille): #affiche une ligne de la position actuelle à la position end
    start = tt.pos()
    finish = (end[0]-start[0],end[1]-start[1])
    dist = math.sqrt(finish[0]**2 + finish[1]**2)
    angle = angle_from_coords(finish)
    center = (start[0]+finish[0]/2, start[1]+finish[1]/2)
    tt.pendown()
    tt.setheading(angle)
    tt.forward(dist)
    tt.penup()
    draw_arrow(tt, taille/10)
    draw_text(tt, center, text, taille)
    

def draw_semi_circle(tt,sender_pos, recep_pos, text, taille):
    tt.goto(sender_pos)
    angle_1 = angle_from_coords(recep_pos) - angle_from_coords(sender_pos)
    center  = ((sender_pos[0] + recep_pos[0])/2, (sender_pos[1] + recep_pos[1])/2)
    if(angle_1%360 < 180):
        center = (-center[0], -center[1])
    dist = math.sqrt(center[0]**2 + center[1]**2)
    ndist = max(dist, taille/3)/dist
    center = (center[0]*ndist, center[1]*ndist)

    a_sen = angle_from_coords(((sender_pos[0] - center[0]) , (sender_pos[1] - center[1])))
    a_rec = angle_from_coords(((recep_pos[0] - center[0]) , (recep_pos[1] - center[1])))
    if(angle_1 < 0 and sender_pos[1] * recep_pos[1] < 0): #ca marche mais je sais pas pourquoi
        angle_2 = a_sen-90
        angle_3 = a_rec-a_sen
    else:
        angle_2 = a_sen+270 #wtf
        angle_3 = -1*(360-(a_rec-a_sen)) #??
    radius = math.sqrt((sender_pos[0]-center[0])**2 + (sender_pos[1]-center[1])**2)
    dist = math.sqrt(center[0]**2 + center[1]**2)
    pos_text = (center[0]*(dist+radius)/dist, center[1]*(dist+radius)/dist)
    
    tt.setheading(180+angle_2)
    tt.pendown()
    tt.circle(radius, angle_3)
    tt.setheading(180+tt.heading())
    tt.penup()
    draw_arrow(tt, taille/10)
    draw_text(tt, pos_text, text, taille)

def create_trle():
    trle = Turtle()
    trle.hideturtle()
    trle.speed(0)
    trle.penup()
    return trle

class NotifierClass(object):
    def __init__(self):
        self.drawer_ip = None
        self.drawer_port = None
        self.active = False
        self.configured = False
        self.logger = Logger(LOGLVL,"Notifier")
        self.adrs = {}
    def is_active(self):
        return self.active and self.configured
    def disable(self):
        self.active = False
    def init(self,ip,port):
        self.drawer_ip = ip
        self.drawer_port = port
        self.active = True
        self.logger.log("Notifier initialisé", LogLevel.DEBUG)
    def configure_node(self,ip,port):
        if not self.active:
            self.logger.log("Notifier incatif", LogLevel.CRITICAL)
            self.logger.log("Configurez l'adresse du drawer : notifier.init(IP_DRAWER,PORT_DRAWER)", LogLevel.CRITICAL)
            exit(1)
        self.adrs = {'draw_ips' : ip, 'draw_ports':port}
        self.configured = True
        self.logger.log("Notifier configuré ("+str(ip)+":"+str(port)+")", LogLevel.DEBUG)
    def send(self,ip,port,data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.drawer_ip, self.drawer_port))
                recp = {'draw_ipr' : ip, 'draw_portr' : port}
                dts = {'type' : data['type']}
                if 'id' in data:
                    dts['id'] = data['id']
                if 'ip' in data:
                    dts['ip'] = data['ip']
                if 'port' in data:
                    dts['port'] = data['port']
                s.send(json.dumps({**self.adrs, **recp, **dts}).encode())
        except:
            self.logger.log("Echec de l'envoi d'un message au Drawer", LogLevel.WARNING)
            #self.disable()
    def notify_first_node(self,ip,port,key):
        if(self.is_active()):
            self.send(ip,port,{'type' : "init", 'id' : key})
        else:
            self.logger.log("Le notifier n'est pas configuré ", LogLevel.CRITICAL)
            self.logger.log("Vous devez d'abord notifier.configure_node(IP,PORT)", LogLevel.CRITICAL)
            exit(1)


class GraphicNode(object):
    def __init__(self, size, ip, port, associated_key, key=None, in_network=False):
        global NCLE
        self.nbcles = NCLE
        self.logger = Logger(LOGLVL,"GraphicNode")
        self.size = size
        self.ip = ip
        self.port = port
        self.key = key
        self.innetwork = in_network
        self.associated_key = int(associated_key)
        self.ttrl = create_trle()
        self.ttrl_comm = create_trle()
        self.setpos()
    def in_network(self):
        return self.innetwork
    def join_network(self):
        if(self.key == None):
            self.logger.log("Un noeud doit rejoindre le réseau mais sa clé n'a pas pu être déterminée", LogLevel.WARNING)
            self.logger.log("C'est probablement du à un problème à l'initialisation du notifieur", LogLevel.WARNING)
            self.logger.log("Ca arrive aussi si plusieurs noeuds se lancent en même temps", LogLevel.WARNING)
            self.associated_key = 0
        else:
            self.associated_key = int(self.key)
            self.logger.log("Le noeud "+str(self.ip )+":"+str(self.port)+" ("+str(self.associated_key)+") a été ajouté au réseau", LogLevel.INFO)
        self.innetwork = True
        self.setpos()
    def get_pos(self):
        return self.pos
    def setpos(self):
        angle = (self.associated_key*360)/self.nbcles
        dist = self.size if self.innetwork else self.size*2
        self.pos = (dist*math.sin(math.radians(angle)), dist*math.cos(math.radians(angle)))
        self.draw()
    def is_asking(self):
        return self.key is not None
    def get_key(self):
        return self.associated_key
    def has_key_set(self):
        return self.key is not None
    def set_key(self, key):
        self.key = int(key)
        if self.innetwork:
            self.associated_key = int(key)
            self.setpos()
    def addr_matches(self, addr):
        my_ips = ['','0.0.0.0','127.0.0.1',"localhost",'192.168.1.35']
        if addr[0] != self.ip:
            return (addr[1] == self.port) and (addr[0] in my_ips) and (self.ip in my_ips)
        return (addr[1] == self.port)
    def draw(self):
        self.ttrl.clear()
        self.ttrl.pencolor("blue" if self.innetwork else "green")
        self.ttrl.goto(self.pos)
        self.ttrl.pendown()
        self.ttrl.dot(self.size/10)
        self.ttrl.penup()
        self.ttrl.goto(self.pos[0]*1.15,self.pos[1]*1.15-self.size/10)
        self.ttrl.pendown()
        self.ttrl.write(str(self.key) if(self.innetwork) else "E."+str(self.associated_key),align="center",font=("Arial",int(self.size/10),"bold"))
        self.ttrl.penup()
    def draw_to_node(self, node, color, text = ""):
        self.ttrl_comm.pencolor(color)
        self.ttrl_comm.goto(self.pos)
        if(not self.innetwork or not node.in_network()):
            draw_line_to(self.ttrl_comm,node.get_pos(),text,self.size)
        else:
            draw_semi_circle(self.ttrl_comm, self.pos, node.get_pos(), text, self.size)
        ontimer(lambda : self.ttrl_comm.clear(), 800)
    
class Drawer(object):
    def __init__(self):
        global NCLE
        self.logger = Logger(LOGLVL)
        self.nbcles = NCLE
        self.size = 150
        self.init_t = create_trle()
        self.init_t.color('black', 'red')
        self.init_t.goto(0,self.size)
        self.init_t.setheading(180)
        self.init_t.pendown()
        self.init_t.circle(self.size)
        self.init_t.penup()
        self.nodes = []
        self.colors = {"join": "green", "get": "red", "res": "blue", "update": "orange", "ok": "orange", "new": "black", "holder_req": "purple", "holder_res": "green", "updateAck": "brown", "quit": "brown", "nok": "grey"}

    def find_two_nodes(self, addr1, addr2):
        node1 = self.find_node(addr1)
        node2 = self.find_node(addr2)
        if(node1 is None):
            if (node2 is None):
                return None, None
            node1 = GraphicNode(self.size, addr1[0], int(addr1[1]), node2.get_key())
            self.nodes.append(node1)
            self.logger.log("Nouveau client "+str(addr1[0])+":"+str(addr1[1])+" communiquant avec le noeud ("+str(node2.get_key())+")", LogLevel.INFO)
        if(node2 is None):
            node2 = GraphicNode(self.size, addr2[0], int(addr2[1]), node1.get_key())
            self.logger.log("Nouveau client "+str(addr2[0])+":"+str(addr2[1])+" communiquant avec le noeud ("+str(node1.get_key())+")", LogLevel.INFO)
            self.nodes.append(node2)
        return node1, node2
    
    
    def find_node(self, addr):
        for node in self.nodes:
            if node.addr_matches(addr):
                return node
        return None

    def execute(self, json_data):
        ipr = json_data['draw_ipr']
        portr = json_data['draw_portr']
        ip_src = json_data['draw_ips']
        port_src = json_data['draw_ports']
        if json_data['type'] in MSGS:
            compt[json_data['type']] += 1
        if(json_data['type'] == "init"):
            self.nodes.append(GraphicNode(self.size, ip_src, port_src, int(json_data['id']), int(json_data['id']), True))
            return
        sender, receiver = self.find_two_nodes((ip_src, port_src), (ipr, portr))
        if sender is None and receiver is None:
            self.logger.log("Communication entre deux noeuds inconnus", LogLevel.ERROR)
            return
        if(json_data['type'] == "join"):
            self.logger.log("Un noeud demande a joindre le réseau", LogLevel.DEBUG)
            node = self.find_node((json_data['ip'], int(json_data['port'])))
            if(node == None):
                self.logger.log("Le noeud demandant a rejoindre le réseau est inconnu", LogLevel.WARNING)
                self.logger.log("Le message initial de join n'a pas été intercepté", LogLevel.WARNING)
                node = GraphicNode(self.size, json_data['ip'], int(json_data['port']), int(json_data['id']))
                self.nodes.append(node)
            else:
                node.set_key(json_data['id'])
        if(json_data['type'] in self.colors.keys() and json_data['type'] in MSGS_TO_TRACK):
            sender.draw_to_node(receiver, self.colors[json_data['type']], json_data['type'])
        else:
            self.logger.log("Message non pris en compte : "+json_data['type'], LogLevel.INFO)
        if(json_data['type'] == "ok"):
            receiver.join_network()
        if(json_data['type'] == "holder_res"):
            if not sender.has_key_set():
                sender.set_key(json_data['id'])
                self.logger.log("La clé du noeud a pu être déterminée", LogLevel.INFO)
                



def sockets_client(d,stop_fun):
    port_listener = PORT_DRAWER
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        serversocket.bind(('', port_listener))
        serversocket.listen(5)
        serversocket.settimeout(0.2)
        while not stop_fun():
            try:
                conn, addr = serversocket.accept()
                with conn:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        d.execute(json.loads(data))
            except socket.timeout:
                pass
            except Exception as e:
                print(e)
                break



def main():
    d = Drawer()
    stop_threads = False
    drawer_thread = threading.Thread(target=sockets_client, args=(d,lambda : stop_threads))
    drawer_thread.start()
    try:
        mainloop()
    except Exception as e:
        print(e)
        stop_threads = True
        drawer_thread.join()
        sys.exit(1)
    stop_threads = True
    print(compt)
    exit(0)

if __name__ == "__main__":
    main()
    
notifier = NotifierClass()
notifier.init(IP_DRAWER, PORT_DRAWER)