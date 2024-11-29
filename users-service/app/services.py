from confluent_kafka import Producer, Consumer

# Kafka Producer
producer = Producer({'bootstrap.servers': 'kafka:9093'})

# Отправка сообщения в Kafka
producer.produce('my_topic', key='key', value='value')
producer.flush()

# Kafka Consumer
consumer = Consumer({
    'bootstrap.servers': 'kafka:9093',
    'group.id': 'my_consumer_group',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe(['my_topic'])
msg = consumer.poll(1.0)
if msg is not None:
    print(msg.value().decode('utf-8'))
