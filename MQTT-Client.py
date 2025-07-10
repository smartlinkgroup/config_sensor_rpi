import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, topic):
        self.broker = "192.168.68.10"
        self.port = 1883
        self.topic = "sensores"
        self.client = mqtt.Client()
        self.client.username_pw_set("lift-adm", "lift2025")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado con codigo de resultado " + str(rc))
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")

    def connect(self):
        self.client.connect(self.broker, self.port, 60)

    def publish(self, payload):
        self.client.publish(self.topic, payload)

    def loop_forever(self):
        self.client.loop_forever()
