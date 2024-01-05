import datetime
import os
from dotenv import load_dotenv
from confluent_kafka import Producer

load_dotenv()  # This loads the environment variables from .env


class KafkaProducer:
    def __init__(self, broker_address, device_name):
        self.producer = Producer({'bootstrap.servers': broker_address})
        self.device_name = device_name

    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def produce_message(self, topic, message):
        current_time = datetime.datetime.now()
        key = f"{self.device_name}"
        self.producer.produce(topic, key=key, value=message, callback=self.delivery_report)
        self.producer.flush()

# Usage
broker = os.getenv('BROKER')
device_name = "Macbook-Pro"
topic = 'test-topic'

producer = KafkaProducer(broker, device_name)
producer.produce_message(topic, 'Nice, environment variable worked :)')
