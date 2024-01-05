
import datetime
import os
from dotenv import load_dotenv
from kafka import KafkaProducer
import json

load_dotenv()

class KafkaProducerWrapper:
    def __init__(self, broker_address, device_name):
        self.producer = KafkaProducer(
            bootstrap_servers=[broker_address],
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        self.device_name = device_name

    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic, msg.partition))

    def produce_message(self, topic, message):
        current_time = datetime.datetime.now()
        key = f"{self.device_name}".encode('utf-8')
        future = self.producer.send(topic, key=key, value=message)
        # Block for 'synchronous' sends
        try:
            record_metadata = future.get(timeout=10)
            self.delivery_report(None, record_metadata)
        except Exception as e:
            self.delivery_report(e, None)
        finally:
            self.producer.flush()

# Usage
broker = os.getenv('BROKER')
device_name = "Macbook-Pro"
topic = 'test-topic'

producer = KafkaProducerWrapper(broker, device_name)
producer.produce_message(topic, 'Nice, environment variable worked :)')


