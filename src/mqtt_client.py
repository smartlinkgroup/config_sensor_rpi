import paho.mqtt.client as mqtt
import json
from src.L298N_MOTOR_SIMPLE import Motor  # Add this import if 'motor' is a module in your project

# Configuración MQTT
BROKER = "192.168.68.10"
PORT = 1883
TOPIC_PUB = "sensores"
TOPIC_SUB = "PLC_RS"
USERNAME = "lift-adm"
PASSWORD = "lift2025"

class MQTTClient:
    def __init__(self, broker=BROKER, port=PORT, topic_pub=TOPIC_PUB, topic_sub=TOPIC_SUB, username=USERNAME, password=PASSWORD):
        self.broker = broker
        self.port = port
        self.topic_pub = topic_pub
        self.topic_sub = topic_sub
        self.username = username
        self.password = password
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.message_handler = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Conectado al broker MQTT.")
            self.client.subscribe(self.topic_sub)
        else:
            print(f"Fallo al conectar, código de error: {rc}")

    def on_publish(self, client, userdata, mid):
        pass

    def on_message(self, client, userdata, msg):
        print(f"Mensaje recibido en el topic {msg.topic}: {str(msg.payload.decode())}")
        if self.message_handler:
            self.message_handler(msg.topic, msg.payload)


    def on_subscribe(self, client, userdata, mid, granted_qos):
        print(f"Suscrito a {self.topic_sub} con QoS: {granted_qos[0]}")

    def connect(self):
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        try:
            self.client.connect(self.broker, self.port, 60)
        except Exception as e:
            print(f"Error al conectar con el broker: {e}")

    def publish(self, payload):
        self.client.publish(self.topic_pub, json.dumps(payload))

    def start(self):
        self.connect()
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("Desconectado del broker MQTT.")

    def set_message_handler(self, handler):
        self.message_handler = handler
