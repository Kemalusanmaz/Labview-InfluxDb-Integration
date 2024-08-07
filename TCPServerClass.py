import socket
import json
import pymongo
import threading
from influxdb_client import InfluxDBClient, Point, WritePrecision
import os

from databaseClass import dBClient
from influxDbClass import influxDbClass
from conf import Configuration as conf

#Server Class to communicate between Gateway and UGKB 
class gatewayServer: # This is a server which manages TCP/IP Server side.
    #These variables is called with gatewayServer.variable
    data_dict ={}
    data_lock = threading.Lock() 

    #Function of Class's Initialize
    def __init__(self,server_ip_address,server_port): # parameters which taking by outside 
        self.server_ip_address = server_ip_address #definition of server ip address which keeps in self.server_ip_address variable
        self.server_port = server_port #definition of server port which keeps in self.port variable
        self.socket = None #self.socket variable's value describes initially empty.
        hostname = socket.gethostname()
        # Host adını IP adresine çevir
        self.server_ip = socket.gethostbyname(hostname)
        print(self.server_ip,hostname)

    #Function of Creating Server Socket is using to create a Listener port to communicate with TC part of UGKB software.
    def createServerSocket(self): #There is no parameter which is taking by outside 
        try:
            #create socket with AF_INET which means IPv4 root and SOCK_STREAM which means TCP/IP informations which keep by self.socket variable.
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
            #socket which was creating, binds with server ip address and server port. Server connection point is creating.
            self.socket.bind((self.server_ip_address,self.server_port)) 
            print(f"Server {self.server_ip_address}:{self.server_port} için soket bağlantı noktası oluşturuldu.")
            return self.socket
        except Exception as ex:
            print(f"Server {self.server_ip_address}:{self.server_port} için soket bağlantı noktası oluşturulurken hata oluştu.\nHata {ex}")
    
    #Function of Listen the Server Socket 
    def listenSocket(self):
        try:
            self.socket.listen() #Socket which created connection point, is started to be listened
            print(f"Sunucu {self.server_ip_address}:{self.server_port} adresini dinliyor...")     
        except Exception as ex:
            print(f"Sunucu {self.server_ip_address}:{self.server_port} adresini dinleyemiyor!!!\nHata {ex}")

    #Function of Accept to connection with Server Socket
    def acceptConnection(self):
            try:
                #If there is claim to connect with Server Socket, this connection will accept by using accept method
                self.conn,self.addr = self.socket.accept() #conn => keeps server ip and port informations. addr => keeps client ip and port informations that connect with server 
                print(f'Bir kullanıcı bağlandı: {self.addr}')
                return self.conn,self.addr   
            except Exception as ex:
                print(f"Bir kullanıcı bağlanamadı!!! Hata {ex}")

    #Function of receiving data from Labview Client to Python Server
    def receiveData(self):
        try:
            with self.data_lock: #threading.lock is usinf to sync treats
                # time.sleep(0,1)
                self.rcvData = self.conn.recv(1024).decode("utf-8") #keeps receiving data in self.rcvData. #keeps converted to format of utf-8s data info. 
                self.data_dict[self.addr] = self.rcvData #received data keeps with dict format to demonstrate wiht relative address. If connection is multiple, this part may be use.
        except Exception as ex:
            print(ex)

    #Function of sending data from Server. This is not use currently.
    def sendData(self,command):  # command parameter which taking by outside 
        try:
            sndData = self.socket.send(command.encode("utf-8")) #keeps sending data
            return sndData
        except Exception as ex:
            print(ex)

    #Function of closing the Server socket
    def closeSocket(self):
        try:
            self.socket.close() #Relative method close the sockets 
            print(f"Sunucu {self.server_ip_address}:{self.server_port} soketi kapatılmıştır.")
        except Exception as ex:
            print(f"Sunucu {self.server_ip_address}:{self.server_port} soketi kapatılamamıştır.\n{ex}")

     #Function of spliting data from Labview Client to sending database
    def splitDataToMongoDb_1(self,interface,dbname,collectionName,seperator):
        try:
            if self.dataSplit.startswith(interface): # if received data starts with interface argument
                dataSplit = self.dataSplit.split(seperator) #split the data as regard seperator

                result = { #the data is converted json format
                    interface:{
                    "Date":dataSplit[1], #second and third parts of data returns date and time stirng 
                    "Time":dataSplit[2],
                    }}
                
                #channel number is different as regars interface for ex, there are three ch for torque tc but siz channel for asm
                for i in range(3, len(dataSplit)): #datasplit is a format of the list so  the loop loops from 3 to number of data  in the variable
                    key = f"CH {i-3}" # keep ch number in the key variable
                    result[interface][key] = dataSplit[i] #add datasplit list in the result variable as regard interface
                # print(result)


                resultToJSON = json.dumps(result,indent= 4, sort_keys=False) #convert dictionary data to JSON
                # print(resultToJSON)
                JSONtoString = json.loads(resultToJSON) #convert json format to JSON string to insert data to the database
                # print(JSONtoString)
                mongoDb = dBClient(dbname,collectionName) #define database client as db
                
                return mongoDb.insertRecord(JSONtoString) #insert data to the database
        except Exception as ex:
            # print("Gelen data tip 1 mongodb için ayrıştırılırken hata oluştu."+ ex)
            print(ex)
        
    def splitDataToMongoDb_2(self,interface,dbname,collectionName,keyname,dataIndex,seperator):
        try:
            if self.dataSplit.startswith(interface): # if received data starts with interface argument
                dataSplit = self.dataSplit.split(";") #split the data as regard seperator
                result = { #the data is converted json format
                    interface:{
                    "Date":dataSplit[1], #second and third parts of data returns date and time stirng 
                    "Time":dataSplit[2]
                    
                        }}
                
                for i in range(3, len(dataSplit)): #datasplit is a format of the list so  the loop loops from 3 to number of data  in the variable
                    dataSplit2 = dataSplit[i].split(seperator)
                    key = f"{keyname}{i-3}"
                    result[interface][key] = dataSplit2[dataIndex] 
                # print(result)
                resultToJSON = json.dumps(result,indent= 4, sort_keys=False) #convert dictionary data to JSON
                JSONtoString = json.loads(resultToJSON) #convert json format to JSON string to insert data to the database
                
                mongoDb = dBClient(dbname,collectionName) #define database client as db
                            
                return mongoDb.insertRecord(JSONtoString) #insert data to the database
        except Exception as ex:
            # print("Gelen data tip 2 mongodb için ayrıştırılırken hata oluştu."+ ex)
            print(ex)

    def sendDataToInfluxDb(self,interface):
        # token = os.environ.get("INFLUXDB_TOKEN") #token bilgisi environment variable'e kaydedilmişti. os paketinden çekilir.
        token = conf.token
        org = conf.org
        url = conf.url
        bucket = conf.bucket

        try:
            # influxDbClass sınıfının örneğini oluştur
            self.influxdatabase= influxDbClass(token, org, url, bucket)
            self.influxdatabase.connectDb()
        except Exception as ex:
            # print("Influxdb'ye bağlanırken hata oluştur" + ex)
            print(ex)
        
        try:
            if self.dataSplit.startswith(interface):
                # print("Doğru")
                dataSplit = self.dataSplit.split(",")
                # print(dataSplit)
                
                self.influxdatabase.writeData(dataSplit[0],"CH0","CH1","CH2",dataSplit[3],dataSplit[4],dataSplit[5])
        except Exception as ex:
            # print("Gelen data influxdb için ayrıştırılırken hata oluştu."+ ex)
            print(ex)

        


    #Function is used for threading.
    def handle_client(self,conn,addr):
        try:
            connected = True #this variable provides bool for infinite loop 
            
            while connected:

                self.receiveData() #receiving data from labview client 

                for self.dataSplit in self.rcvData.split("\n"): #the data from labview is splitted according to seperator string whic is end pf line in this case
                    # print(self.dataSplit)
                    if self.dataSplit == "exit": #If the splitted data is exit, break the loop, close the Server socket via closeSocket method in the Server class 
                        connected = False
                        # self.closeSocket()
                        self.influxdatabase.disconnectDb()
                        
                        break

                    else: #otherwise
                        # self.dataSplit = str(dataSplit) #datasplit variable is converted self to using other methods in the class

                        if self.dataSplit != None: #if the datasplit variable is not null, call the splitDatatoDB method to sending data to defined collection in the database 
                            
                            self.process_data()                       
                    
        except Exception as ex:
            # print("Threat fonksiyonunda bir hata oluştu." + ex)  
            print(ex) 

    def process_data(self):
        with self.data_lock:
            self.mongoDbData()
            self.influxDbData()
            
            
            pass      


    def mongoDbData(self):
        self.splitDataToMongoDb_1("Torque","ReactionWheelDB","Torque TC",",") 
        self.splitDataToMongoDb_1("Tacho","ReactionWheelDB","Tachometer TM",",")
        self.splitDataToMongoDb_1("Dir","ReactionWheelDB","Direction of Rotation TM",",")
        self.splitDataToMongoDb_1("Asm","AnalogSensorDB","Analog Sensor Monitor TM",",")
        self.splitDataToMongoDb_1("Pt","AnalogSensorDB","Pressure Transducer TM",",")
        self.splitDataToMongoDb_1("Anv","AnalogSensorDB","ANV TM",",") #The Method takes some arguments 1-> Interface Name 2-> Database Name from MongoDB 3-> Collection Name from MongoDB
        self.splitDataToMongoDb_2("Hpc","DigitalInterfacesDB","HPC","HPC",4,",") #The Method takes some arguments 1-> Interface Name 2-> Database Name from MongoDB 3-> Collection Name from MongoDB
                                                                            # 4-> key name for results 5-> seperator index 6-> seperator string
        self.splitDataToMongoDb_2("Bsm","DigitalInterfacesDB","BSM","BSM",1,":")
        self.splitDataToMongoDb_2("Bdm","DigitalInterfacesDB","BDM","BDM",1,"/")

    def influxDbData(self):
        self.sendDataToInfluxDb("Torque")
        self.sendDataToInfluxDb("Tacho")
        self.sendDataToInfluxDb("Dir")
        self.sendDataToInfluxDb("Asm")
        self.sendDataToInfluxDb("Anv")
        self.sendDataToInfluxDb("Pt")
        



        