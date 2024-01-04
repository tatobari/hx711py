import logging
from confluent_kafka import Producer
import datetime

class KafkaLoggingHandler(logging.Handler):
    def __init__(self, broker_address, topic, device_name):
        super().__init__()
        self.producer = Producer({'bootstrap.servers': broker_address})
        self.topic = topic
        self.device_name = device_name

    def emit(self, record):
        try:
            # Create a message key and value
            current_time = datetime.datetime.now()
            key = f"{self.device_name}_{current_time.strftime('%Y-%m-%d_%H:%M:%S')}"
            message = self.format(record)

            # Produce the message
            self.producer.produce(self.topic, key=key, value=message)
            self.producer.flush()
        except Exception:
            self.handleError(record)

        def get_kafka_logger(broker_address, topic, device_name):
            logger = logging.getLogger('KafkaLogger')
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                kafka_handler = KafkaLoggingHandler(broker_address, topic, device_name)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                kafka_handler.setFormatter(formatter)
                logger.addHandler(kafka_handler)
        return logger

# # Kafka configuration
# broker = '192.168.1.88:9092:9092'  # Replace with your Kafka broker address
# device_name = "chair-sensor-1"
# topic = 'log-topic'

# Set up logging to use the KafkaLoggingHandler
# logger = logging.getLogger('KafkaLogger')
# logger.setLevel(logging.INFO)
# kafka_handler = KafkaLoggingHandler(broker, topic, device_name)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# kafka_handler.setFormatter(formatter)
# logger.addHandler(kafka_handler)

# Log some messages
# logger.info("This is an info log message")
# logger.error("This is an error log message")
