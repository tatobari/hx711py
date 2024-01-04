from confluent_kafka import Producer
import datetime

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
        key = f"{self.device_name}_{current_time.strftime('%Y-%m-%d_%H:%M:%S')}"
        self.producer.produce(topic, key=key, value=message, callback=self.delivery_report)
        self.producer.flush()

# Usage
# broker = 'your.kafka.broker.address:9092'  # Replace with your Kafka broker address
# device_name = "Device1"
# topic = 'test-topic'

# producer = KafkaProducer(broker, device_name)
# producer.produce_message(topic, 'Hello, Kafka!')
