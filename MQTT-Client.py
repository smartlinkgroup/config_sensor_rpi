import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, topic, username=None, password=None):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        if username and password:
            self.client.username_pw_set(username, password)
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
